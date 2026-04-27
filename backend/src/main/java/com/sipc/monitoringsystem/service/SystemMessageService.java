package com.sipc.monitoringsystem.service;

import java.util.List;

import com.sipc.monitoringsystem.model.po.Message.SystemMessage;

public interface SystemMessageService {
    boolean addMessage(SystemMessage message);
    List<SystemMessage> getMessage(Integer receiverUserId);
}
