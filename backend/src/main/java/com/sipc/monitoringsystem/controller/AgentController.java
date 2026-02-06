package com.sipc.monitoringsystem.controller;

import com.sipc.monitoringsystem.model.dto.CommonResult;
import com.sipc.monitoringsystem.service.AgentService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * AI Agent 控制器
 * 提供智能问答接口
 * 
 * @author AI Assistant
 * @date 2024-01-27
 */
@Slf4j
@Validated
@RestController
@CrossOrigin
@RequestMapping("/api/v1/agent")
public class AgentController {
    
    @Autowired
    private AgentService agentService;
    
    /**
     * 智能问答接口
     * 
     * 功能：
     * 1. 回答安全知识问题
     * 2. 查询告警信息并给出建议
     * 3. 查询监控点信息并分析
     * 4. 实时统计数据分析
     * 
     * @param request 请求体，包含question字段
     * @return AI回答
     */
    @PostMapping("/chat")
    public CommonResult<String> chat(@RequestBody Map<String, String> request) {
        String question = request.get("question");
        return agentService.chat(question);
    }
    
    /**
     * 检查Agent服务状态
     * 
     * @return 服务状态
     */
    @GetMapping("/health")
    public CommonResult<Map<String, Object>> health() {
        boolean available = agentService.isAvailable();
        Map<String, Object> status = Map.of(
            "available", available,
            "message", available ? "Agent服务正常" : "Agent服务不可用"
        );
        return CommonResult.success(status);
    }
}
