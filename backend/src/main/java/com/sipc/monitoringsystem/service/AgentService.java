package com.sipc.monitoringsystem.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.sipc.monitoringsystem.model.dto.CommonResult;
import com.sipc.monitoringsystem.util.HttpUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;

@Slf4j
@Service
public class AgentService {

    private static final String PUBLIC_AGENT_ERROR_MESSAGE = "智能助手暂时不可用，请稍后重试";

    @Value("${agent.api.url:http://localhost:5000}")
    private String agentApiUrl;

    private final ObjectMapper objectMapper = new ObjectMapper();

    public CommonResult<String> chat(String question) {
        if (question == null || question.trim().isEmpty()) {
            return CommonResult.fail("问题不能为空");
        }

        try {
            Map<String, String> requestBody = new HashMap<>();
            requestBody.put("question", question);

            String jsonBody = objectMapper.writeValueAsString(requestBody);

            log.info("调用Agent服务，问题: {}", question);

            String response = HttpUtils.postJson(agentApiUrl + "/chat", jsonBody);

            if (response == null || response.isEmpty()) {
                log.error("Agent服务无响应");
                return CommonResult.fail(PUBLIC_AGENT_ERROR_MESSAGE);
            }

            JsonNode jsonNode = objectMapper.readTree(response);
            String code = jsonNode.path("code").asText();
            String message = jsonNode.path("message").asText();

            if ("00000".equals(code)) {
                String answer = jsonNode.path("data").path("answer").asText();
                log.info("Agent回答成功");
                return CommonResult.success(answer);
            }

            log.error("Agent服务返回错误: {}", message);
            return CommonResult.fail(PUBLIC_AGENT_ERROR_MESSAGE);
        } catch (Exception e) {
            log.error("调用Agent服务失败", e);
            return CommonResult.fail(PUBLIC_AGENT_ERROR_MESSAGE);
        }
    }

    public boolean isAvailable() {
        try {
            String response = HttpUtils.get(agentApiUrl + "/health");
            return response != null && response.contains("\"status\":\"ok\"");
        } catch (Exception e) {
            log.warn("Agent服务健康检查失败: {}", e.getMessage());
            return false;
        }
    }
}
