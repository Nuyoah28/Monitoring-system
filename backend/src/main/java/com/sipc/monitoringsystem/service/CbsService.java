package com.sipc.monitoringsystem.service;

import com.plexpt.chatgpt.entity.chat.Message;
import com.sipc.monitoringsystem.model.dto.param.gpt.ChatParam;

public interface CbsService {

    Message getText(ChatParam chatParam);

}
