package com.sipc.monitoringsystem.controller;

import com.qcloud.cos.COSClient;
import com.qcloud.cos.model.COSObject;
import com.qcloud.cos.model.GetObjectRequest;
import com.sipc.monitoringsystem.aop.Pass;
import com.sipc.monitoringsystem.config.OssConfig;
import com.sipc.monitoringsystem.util.OssUtil;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.StreamingResponseBody;

import java.io.InputStream;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Slf4j
@RestController
@CrossOrigin
@RequestMapping("/api/v1/alarm")
public class AlarmClipController {

    private static final Pattern RANGE_PATTERN = Pattern.compile("bytes=(\\d+)-(\\d+)?");

    @Autowired
    private OssConfig ossConfig;

    @Autowired
    private OssUtil ossUtil;

    @Pass
    @GetMapping("/clips/{clipId:.+}")
    public ResponseEntity<StreamingResponseBody> streamAlarmClip(
            @PathVariable String clipId,
            @RequestHeader(value = "Range", required = false) String rangeHeader) {
        String objectKey = ossUtil.normalizeClipObjectKey(clipId);
        if (objectKey == null || objectKey.isBlank()) {
            return ResponseEntity.notFound().build();
        }

        COSClient cosClient = ossConfig.cosClient();
        String bucketName = ossConfig.getBucketName();
        try {
            long fileSize = cosClient.getObjectMetadata(bucketName, objectKey).getContentLength();
            long start = 0L;
            long end = fileSize - 1;
            boolean partial = false;

            GetObjectRequest request = new GetObjectRequest(bucketName, objectKey);
            if (rangeHeader != null && !rangeHeader.isBlank()) {
                Matcher matcher = RANGE_PATTERN.matcher(rangeHeader.trim());
                if (matcher.matches()) {
                    start = Long.parseLong(matcher.group(1));
                    String endStr = matcher.group(2);
                    if (endStr != null) {
                        end = Math.min(Long.parseLong(endStr), fileSize - 1);
                    }
                    if (start < fileSize && start <= end) {
                        request.setRange(start, end);
                        partial = true;
                    }
                }
            }

            COSObject cosObject = cosClient.getObject(request);
            long contentLength = partial ? (end - start + 1) : fileSize;

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.parseMediaType("video/x-flv"));
            headers.set("Accept-Ranges", "bytes");
            headers.setCacheControl("no-store, no-cache, must-revalidate, max-age=0");
            headers.setPragma("no-cache");
            headers.setContentLength(contentLength);
            if (partial) {
                headers.set("Content-Range", "bytes " + start + "-" + end + "/" + fileSize);
            }

            StreamingResponseBody body = outputStream -> {
                try (InputStream inputStream = cosObject.getObjectContent()) {
                    byte[] buffer = new byte[8192];
                    int len;
                    while ((len = inputStream.read(buffer)) != -1) {
                        outputStream.write(buffer, 0, len);
                    }
                    outputStream.flush();
                } finally {
                    cosClient.shutdown();
                }
            };

            return ResponseEntity.status(partial ? HttpStatus.PARTIAL_CONTENT : HttpStatus.OK)
                    .headers(headers)
                    .body(body);
        } catch (Exception e) {
            cosClient.shutdown();
            log.warn("alarm clip stream failed, key={}", objectKey, e);
            return ResponseEntity.notFound().build();
        }
    }
}