package com.sipc.monitoringsystem.service.impl;


import com.plexpt.chatgpt.entity.chat.Message;
import com.sipc.monitoringsystem.model.dto.param.gpt.ChatParam;
import com.sipc.monitoringsystem.service.CbsService;

import com.sipc.monitoringsystem.util.CbsUtil;
import com.sipc.monitoringsystem.util.KeyUtils.KeyManager;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;


@Slf4j
@RequiredArgsConstructor
@Service
public class CbsServiceImpl implements CbsService {

    final KeyManager keyManager;
    //   哈希表   id和对话一一对应
    private static Map<String, List<Message>> context = new HashMap<>();

    public List<Message> get(String id) {
        List<Message> messages = context.get(id);
        if (messages == null) {
            messages = new ArrayList<>();
            context.put(id, messages);
        }
        return messages;
    }

    public void add(String id, Message message) {
        List<Message> messages = context.get(id);
        if (messages == null) {
            messages = new ArrayList<>();
            context.put(id, messages);
        }
        messages.add(message);
    }



    @Override
    public Message getText(ChatParam param) {

        String prompt = param.buildPrompt();

        try {
            Message message = Message.of(prompt);
            List<Message> messages = get(param.getId());
            messages.add(message);
//
//            ChatCompletionResponse completion = chatGPT.chatCompletion(messages);
//            Message message1 = completion.getChoices().get(0).getMessage();

            //返回的为字符串
            CbsUtil cbsUtil = new CbsUtil();
            Message message1 = Message.of(cbsUtil.cbs(param.getMessage()));
            add(param.getId(), message);
            add(param.getId(), message1);
            return message1;

        } catch (Exception e) {
            log.error("API调用出错：{}", e);
            throw new RuntimeException("服务器挤爆了，请检查KEY， 网络。请输入你的APIKEY后试用: " + e.getMessage());
        }
    }


}
