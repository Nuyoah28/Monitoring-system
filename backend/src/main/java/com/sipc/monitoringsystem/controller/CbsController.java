package com.sipc.monitoringsystem.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.plexpt.chatgpt.entity.chat.Message;
import com.sipc.monitoringsystem.model.dto.CommonResult;
import com.sipc.monitoringsystem.model.dto.param.gpt.ChatParam;
import com.sipc.monitoringsystem.model.dto.res.BlankRes;
import com.sipc.monitoringsystem.service.CbsService;

import jakarta.validation.Valid;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.IOException;
import java.util.Map;

/**
 * @author wangfeng
 * &#064;date 2023-09-13 20:59
 */

@Validated
@CrossOrigin
@RestController
@Slf4j
@RequestMapping("/api/v1/cbs")

public class CbsController {
    //与gpt共用
    @Autowired
    CbsService cbsService;

    @PostMapping()
    public CommonResult<BlankRes> chat(@Valid  @RequestBody ChatParam param) {


        log.info("正在提问: " + param.getMessage());
        Message message = cbsService.getText(param);
        //text  content为答案
        String text = message.getContent();
        //log.info("答案是"+text);
       //  log.info("问题：" + param.getMessage() + "\n回答：" + text);

        return CommonResult.success(text);
    }

    /**
     * 流式对话接口（SSE - Server-Sent Events）
     * 实时返回AI回答的片段，支持一个字一个字的显示
     */
    @PostMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter chatStream(@Valid @RequestBody ChatParam param) {
        SseEmitter emitter = new SseEmitter(60000L); // 60秒超时
        
        // 异步处理，避免阻塞
        new Thread(() -> {
            try {
                log.info("正在提问（流式）: " + param.getMessage());
                
                // 发送开始信号
                Map<String, String> startData = Map.of(
                    "type", "start",
                    "question", param.getMessage() != null ? param.getMessage() : ""
                );
                ObjectMapper mapper = new ObjectMapper();
                emitter.send(SseEmitter.event()
                    .name("start")
                    .data(mapper.writeValueAsString(startData)));
                
                // 获取AI回答
                Message message = cbsService.getText(param);
                String text = message.getContent();
                
                // 分段发送响应（模拟流式输出）
                // 每次发送1个字符，实现逐字显示
                for (int i = 0; i < text.length(); i++) {
                    String chunk = text.substring(i, i + 1);
                    
                    // 发送数据块
                    Map<String, String> data = Map.of(
                        "type", "chunk",
                        "content", chunk
                    );
                    emitter.send(SseEmitter.event()
                        .name("message")
                        .data(mapper.writeValueAsString(data)));
                    
                    // 小延迟，控制显示速度（20ms = 50字符/秒）
                    Thread.sleep(20);
                }
                
                // 发送完成信号
                Map<String, String> doneData = Map.of("type", "done");
                emitter.send(SseEmitter.event()
                    .name("done")
                    .data(mapper.writeValueAsString(doneData)));
                
                emitter.complete();
                
            } catch (Exception e) {
                log.error("流式处理失败: ", e);
                try {
                    Map<String, String> error = Map.of(
                        "type", "error",
                        "message", e.getMessage() != null ? e.getMessage() : "处理失败"
                    );
                    ObjectMapper mapper = new ObjectMapper();
                    emitter.send(SseEmitter.event()
                        .name("error")
                        .data(mapper.writeValueAsString(error)));
                } catch (IOException ex) {
                    log.error("发送错误信息失败: ", ex);
                }
                emitter.completeWithError(e);
            }
        }).start();
        
        return emitter;
    }

}
