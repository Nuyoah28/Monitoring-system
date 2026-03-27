package com.sipc.monitoringsystem.service.impl;

import java.util.List;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.sipc.monitoringsystem.dao.SystemMessageDao;
import com.sipc.monitoringsystem.model.po.Message.SystemMessage;
import com.sipc.monitoringsystem.service.SystemMessageService;

public class SystemMessageServiceImpl extends ServiceImpl<SystemMessageDao, SystemMessage> implements SystemMessageService {
    @Override
    public boolean addMessage(SystemMessage message) {
        if(!this.save(message)){
            return false;
        }
        return true;
    }
    @Override
    public List<SystemMessage> getMessage(SystemMessage message){
        //return all messages
        return this.list();
    }
}
