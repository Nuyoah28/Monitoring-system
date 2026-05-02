package com.sipc.monitoringsystem.util;

import com.sipc.monitoringsystem.config.OssConfig;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Component;

@Component
public class OssUtil {
    @Autowired
    private OssConfig ossConfig;

    /**
     * 根据告警视频 clipId / 对象 key 获得 COS 访问链接。
     *
     * @param clipIdOrKey 数据库 alarm_info.clip_link 中保存的 clipId 或对象 key
     * @return {@link String}
     */

    @Cacheable(value = "clipLink", key = "#clipIdOrKey")
    public String getClipLinkByUuid(String clipIdOrKey) {
        if (clipIdOrKey == null || clipIdOrKey.trim().isEmpty()) {
            return clipIdOrKey;
        }
        String objectKey = ossConfig.normalizeObjectKey(clipIdOrKey, ".flv");
        if (objectKey.startsWith("http://") || objectKey.startsWith("https://")) {
            return objectKey;
        }
        return ossConfig.buildObjectUrl(objectKey);
    }
}
