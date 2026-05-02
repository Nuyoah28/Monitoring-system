package com.sipc.monitoringsystem.config;


import com.qcloud.cos.COSClient;
import com.qcloud.cos.ClientConfig;
import com.qcloud.cos.auth.BasicCOSCredentials;
import com.qcloud.cos.auth.COSCredentials;
import com.qcloud.cos.http.HttpProtocol;
import com.qcloud.cos.region.Region;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class OssConfig {
    @Value("${oss.id:}")
    private String secretId;

    @Value("${oss.pass:}")
    private String secretKey;

    @Value("${oss.region:ap-beijing}")
    private String region;

    @Value("${oss.bucket:my-server-1397492316}")
    private String bucketName;

    @Value("${oss.base-url:}")
    private String baseUrl;

    public COSClient cosClient() {
        COSCredentials cred = new BasicCOSCredentials(
                requireText(secretId, "oss.id"),
                requireText(secretKey, "oss.pass"));
        // ClientConfig 中包含了后续请求 COS 的客户端设置：
        ClientConfig clientConfig = new ClientConfig();
        clientConfig.setRegion(new Region(getRegion()));
        clientConfig.setHttpProtocol(HttpProtocol.https);
        clientConfig.setSocketTimeout(30 * 1000);
        clientConfig.setConnectionTimeout(30 * 1000);
        return new COSClient(cred, clientConfig);
    }

    public String getRegion() {
        return hasText(region) ? region.trim() : "ap-beijing";
    }

    public String getBucketName() {
        return requireText(bucketName, "oss.bucket");
    }

    public String buildObjectUrl(String objectKey) {
        String key = trimLeadingSlash(requireText(objectKey, "objectKey"));
        return getPublicBaseUrl() + "/" + key;
    }

    public String normalizeObjectKey(String clipIdOrKey, String defaultSuffix) {
        String objectKey = requireText(clipIdOrKey, "objectKey").trim();
        if (objectKey.startsWith("http://") || objectKey.startsWith("https://")) {
            return objectKey;
        }
        objectKey = trimLeadingSlash(objectKey);
        if (hasText(defaultSuffix) && !objectKey.contains(".") && !objectKey.endsWith(defaultSuffix)) {
            objectKey += defaultSuffix;
        }
        return objectKey;
    }

    private String getPublicBaseUrl() {
        if (hasText(baseUrl)) {
            return trimTrailingSlash(baseUrl.trim());
        }
        return "https://" + getBucketName() + ".cos." + getRegion() + ".myqcloud.com";
    }

    private String requireText(String value, String name) {
        if (!hasText(value)) {
            throw new IllegalStateException("COS配置缺失: " + name);
        }
        return value.trim();
    }

    private boolean hasText(String value) {
        return value != null && !value.trim().isEmpty();
    }

    private String trimLeadingSlash(String value) {
        String result = value;
        while (result.startsWith("/")) {
            result = result.substring(1);
        }
        return result;
    }

    private String trimTrailingSlash(String value) {
        String result = value;
        while (result.endsWith("/")) {
            result = result.substring(0, result.length() - 1);
        }
        return result;
    }
}
