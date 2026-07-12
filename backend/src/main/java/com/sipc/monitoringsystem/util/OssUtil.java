package com.sipc.monitoringsystem.util;

import com.qcloud.cos.COSClient;
import com.qcloud.cos.model.ObjectMetadata;
import com.sipc.monitoringsystem.config.OssConfig;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.net.URI;
import java.util.UUID;

// AI辅助生成：GLM-5 智谱AI，新增 OssUtil 工具类，提供告警视频链接规范化和前端代理链接生成方法，统一处理 clipId 和对象 key，兼容演示标识 SIM_。
@Component
public class OssUtil {
    private static final String ALARM_CLIP_PREFIX = "/api/v1/alarm/clips/";

    @Autowired
    private OssConfig ossConfig;

    /**
     * 根据告警视频 clipId / 对象 key 获得前端可播放链接。
     * SIM_* 演示标识保持原样，真实报警片段统一走后端代理，避免 COS CORS 和签名过期问题。
     *
     * @param clipIdOrKey 数据库 alarm_info.clip_link 中保存的 clipId 或对象 key
     * @return 前端可使用的视频链接
     */
    @Cacheable(value = "clipLink", key = "#clipIdOrKey", condition = "#clipIdOrKey != null && !#clipIdOrKey.trim().isEmpty() && !#clipIdOrKey.trim().startsWith('SIM_')")
    public String getClipLinkByUuid(String clipIdOrKey) {
        if (clipIdOrKey == null || clipIdOrKey.trim().isEmpty()) {
            return clipIdOrKey;
        }
        if (isDemoClipId(clipIdOrKey)) {
            return clipIdOrKey.trim();
        }
        return ALARM_CLIP_PREFIX + normalizeClipObjectKey(clipIdOrKey);
    }

    public String normalizeClipObjectKey(String clipIdOrKey) {
        if (clipIdOrKey == null || clipIdOrKey.trim().isEmpty()) {
            return clipIdOrKey;
        }
        String objectKey = clipIdOrKey.trim();
        if (objectKey.startsWith(ALARM_CLIP_PREFIX)) {
            objectKey = objectKey.substring(ALARM_CLIP_PREFIX.length());
        }
        if (objectKey.startsWith("http://") || objectKey.startsWith("https://")) {
            try {
                URI uri = URI.create(objectKey);
                String path = uri.getPath();
                if (path != null && !path.isBlank()) {
                    if (path.startsWith(ALARM_CLIP_PREFIX)) {
                        objectKey = path.substring(ALARM_CLIP_PREFIX.length());
                    } else {
                        int slashIndex = path.lastIndexOf('/');
                        objectKey = slashIndex >= 0 ? path.substring(slashIndex + 1) : path;
                    }
                }
            } catch (IllegalArgumentException ignored) {
                // Fall back to the original value if URI parsing fails.
            }
        }
        return ossConfig.normalizeObjectKey(objectKey, ".flv");
    }

    private boolean isDemoClipId(String clipIdOrKey) {
        String value = clipIdOrKey.trim();
        return value.startsWith("SIM_");
    }

    /**
     * 上传一张图片到 COS（社区上报随手拍使用），返回对象 key。
     * 复用 OssConfig 已配置的凭证与 bucket，与告警片段同一套对象存储。
     *
     * @param file 前端上传的图片文件
     * @return COS objectKey，形如 community-report/xxxx.jpg
     */
    public String uploadImage(MultipartFile file) throws IOException {
        if (file == null || file.isEmpty()) {
            throw new IOException("上传文件为空");
        }
        String original = file.getOriginalFilename();
        String ext = "";
        if (original != null && original.contains(".")) {
            ext = original.substring(original.lastIndexOf('.'));
        }
        String objectKey = "community-report/" + UUID.randomUUID().toString().replace("-", "") + ext;
        COSClient cosClient = ossConfig.cosClient();
        try {
            ObjectMetadata metadata = new ObjectMetadata();
            metadata.setContentLength(file.getSize());
            if (file.getContentType() != null) {
                metadata.setContentType(file.getContentType());
            }
            cosClient.putObject(ossConfig.getBucketName(), objectKey, file.getInputStream(), metadata);
        } finally {
            cosClient.shutdown();
        }
        return objectKey;
    }

    /** 由对象 key 生成可公开访问的 COS 图片 URL */
    public String buildImageUrl(String objectKey) {
        return ossConfig.buildObjectUrl(objectKey);
    }
}