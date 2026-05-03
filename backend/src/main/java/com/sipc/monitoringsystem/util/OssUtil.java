package com.sipc.monitoringsystem.util;

import com.sipc.monitoringsystem.config.OssConfig;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Component;

import java.net.URI;

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
}