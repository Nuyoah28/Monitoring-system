package com.sipc.monitoringsystem.service.impl;

import java.util.List;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.sipc.monitoringsystem.dao.SystemMessageDao;
import com.sipc.monitoringsystem.model.po.Message.SystemMessage;
import com.sipc.monitoringsystem.service.SystemMessageService;
import org.springframework.stereotype.Service;

import java.sql.Timestamp;

@Service
public class SystemMessageServiceImpl extends ServiceImpl<SystemMessageDao, SystemMessage> implements SystemMessageService {
    @Override
    public boolean addMessage(SystemMessage message) {
        if (message == null) {
            return false;
        }
        if (message.getTimestamp() == null) {
            message.setTimestamp(new Timestamp(System.currentTimeMillis()));
        }
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
