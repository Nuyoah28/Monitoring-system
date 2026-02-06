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

/**
 * AI Agent 服务
 * 调用Python Agent进行智能问答
 * 
 * @author AI Assistant
 * @date 2024-01-27
 */
@Slf4j
@Service
public class AgentService {
    
    @Value("${agent.api.url:http://localhost:5000}")
    private String agentApiUrl;
    
    private final ObjectMapper objectMapper = new ObjectMapper();
    
    /**
     * 调用Agent进行智能问答
     * 
     * @param question 用户问题
     * @return AI回答
     */
    public CommonResult<String> chat(String question) {
        if (question == null || question.trim().isEmpty()) {
            return CommonResult.fail("问题不能为空");
        }
        
        try {
            // 构建请求体
            Map<String, String> requestBody = new HashMap<>();
            requestBody.put("question", question);
            
            String jsonBody = objectMapper.writeValueAsString(requestBody);
            
            log.info("调用Agent服务，问题: {}", question);
            
            // 调用Python Agent API
            String response = HttpUtils.postJson(agentApiUrl + "/chat", jsonBody);
            
            if (response == null || response.isEmpty()) {
                log.error("Agent服务无响应");
                return CommonResult.fail("Agent服务暂时不可用");
            }
            
            // 解析响应
            JsonNode jsonNode = objectMapper.readTree(response);
            String code = jsonNode.get("code").asText();
            String message = jsonNode.get("message").asText();
            
            if ("00000".equals(code)) {
                String answer = jsonNode.get("data").get("answer").asText();
                log.info("Agent回答成功");
                return CommonResult.success(answer);
            } else {
                log.error("Agent服务返回错误: {}", message);
                return CommonResult.fail(message);
            }
            
        } catch (Exception e) {
            log.error("调用Agent服务失败", e);
            return CommonResult.fail("Agent服务调用失败: " + e.getMessage());
        }
    }
    
    /**
     * 检查Agent服务是否可用
     * 
     * @return 是否可用
     */
    public boolean isAvailable() {
        try {
            String response = HttpUtils.get(agentApiUrl + "/health");
            if (response != null && response.contains("\"status\":\"ok\"")) {
                return true;
            }
        } catch (Exception e) {
            log.warn("Agent服务健康检查失败: {}", e.getMessage());
        }
        return false;
    }
}
