package com.sipc.monitoringsystem.controller;

import com.sipc.monitoringsystem.aop.Pass;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.ClassPathResource;
import org.springframework.core.io.Resource;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;

import java.io.IOException;
import java.io.InputStream;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * FLV视频流控制器
 * 用于提供FLV格式视频文件的HTTP访问
 * 
 * @author alaner28
 * @date 2026-01-27
 */
@Slf4j
@RestController
@CrossOrigin
@RequestMapping("/video")
public class FlvController {

    private static final Pattern RANGE_PATTERN = Pattern.compile("bytes=(\\d+)-(\\d+)?");

    /**
     * 获取FLV视频流
     * 
     * @param fileName    视频文件名
     * @param rangeHeader Range请求头
     * @return 包含FLV视频流的响应
     */
    @Pass
    @GetMapping("/{fileName:.+\\.flv}")
    public ResponseEntity<byte[]> getFlvVideo(@PathVariable String fileName,
            @RequestHeader(value = "Range", required = false) String rangeHeader) {
        try {
            // 从资源目录加载FLV文件
            Resource resource = new ClassPathResource("flv/" + fileName);

            if (!resource.exists()) {
                log.warn("Requested FLV file does not exist: {}", fileName);
                return ResponseEntity.notFound().build();
            }

            long fileSize;
            try (InputStream inputStream = resource.getInputStream()) {
                fileSize = inputStream.available();
            }

            if (rangeHeader != null) {
                return handleRangeRequest(resource, rangeHeader, fileSize);
            } else {
                // 全部文件请求
                byte[] videoBytes;
                try (InputStream inputStream = resource.getInputStream()) {
                    videoBytes = inputStream.readAllBytes();
                }

                HttpHeaders headers = new HttpHeaders();
                headers.setContentType(MediaType.parseMediaType("video/x-flv"));
                headers.setContentLength(fileSize);
                headers.set("Accept-Ranges", "bytes");
                headers.setCacheControl("public, max-age=3600");

                log.info("Serving full FLV video: {}, size: {} bytes", fileName, fileSize);
                return ResponseEntity.status(HttpStatus.PARTIAL_CONTENT)
                        .headers(headers)
                        .body(videoBytes);
            }
        } catch (IOException e) {
            log.error("Error serving FLV video: {}", fileName, e);
            return ResponseEntity.internalServerError().build();
        }
    }

    private ResponseEntity<byte[]> handleRangeRequest(Resource resource, String rangeHeader, long fileSize)
            throws IOException {
        Matcher matcher = RANGE_PATTERN.matcher(rangeHeader);
        if (!matcher.matches()) {
            return ResponseEntity.badRequest().build();
        }

        long start = Long.parseLong(matcher.group(1));
        String endStr = matcher.group(2);
        long end = (endStr != null) ? Long.parseLong(endStr) : fileSize - 1;

        // 确保结束位置不超过文件大小
        end = Math.min(end, fileSize - 1);

        if (start >= fileSize) {
            // 请求范围超出文件大小
            HttpHeaders headers = new HttpHeaders();
            headers.set("Content-Range", "bytes */" + fileSize);
            return ResponseEntity.status(HttpStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                    .headers(headers)
                    .build();
        }

        // 计算要读取的字节数
        long length = end - start + 1;
        byte[] buffer = new byte[(int) length];

        try (InputStream inputStream = resource.getInputStream()) {
            // 跳转到指定位置
            long skipped = inputStream.skip(start);
            if (skipped < start) {
                // 如果跳过的字节少于请求的起始位置，说明文件长度不够
                return ResponseEntity.status(HttpStatus.REQUESTED_RANGE_NOT_SATISFIABLE).build();
            }

            // 读取指定范围的数据
            int totalRead = 0;
            while (totalRead < length) {
                int bytesRead = inputStream.read(buffer, totalRead, (int) (length - totalRead));
                if (bytesRead == -1) {
                    break; // 文件结束
                }
                totalRead += bytesRead;
            }
        }

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.parseMediaType("video/x-flv"));
        headers.setContentLength(length);
        headers.set("Accept-Ranges", "bytes");
        headers.set("Content-Range", "bytes " + start + "-" + end + "/" + fileSize);
        headers.setCacheControl("public, max-age=3600");

        log.info("Serving FLV video range: {}-{} of {}, file: {}", start, end, fileSize, resource.getFilename());
        return ResponseEntity.status(HttpStatus.PARTIAL_CONTENT)
                .headers(headers)
                .body(buffer);
    }
}