package com.sipc.monitoringsystem.controller;

import com.sipc.monitoringsystem.model.dto.CommonResult;
import com.sipc.monitoringsystem.service.AgentService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@Validated
@RestController
@CrossOrigin
@RequestMapping("/api/v1/agent")
public class AgentController {

    @Autowired
    private AgentService agentService;

    @PostMapping("/chat")
    public CommonResult<String> chat(@RequestBody Map<String, String> request) {
        String question = request.get("question");
        return agentService.chat(question);
    }

    @GetMapping("/health")
    public CommonResult<Map<String, Object>> health() {
        boolean available = agentService.isAvailable();
        Map<String, Object> status = Map.of(
                "available", available,
                "message", available ? "Agent服务正常" : "Agent服务不可用");
        return CommonResult.success(status);
    }
}
