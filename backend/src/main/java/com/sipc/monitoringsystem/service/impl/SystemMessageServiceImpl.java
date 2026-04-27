package com.sipc.monitoringsystem.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.sipc.monitoringsystem.dao.SystemMessageDao;
import com.sipc.monitoringsystem.model.po.Message.SystemMessage;
import com.sipc.monitoringsystem.service.SystemMessageService;
import org.springframework.stereotype.Service;

import java.sql.Timestamp;
import java.util.List;

@Service
public class SystemMessageServiceImpl extends ServiceImpl<SystemMessageDao, SystemMessage>
        implements SystemMessageService {

    @Override
    public boolean addMessage(SystemMessage message) {
        if (message == null) {
            return false;
        }
        if (message.getTimestamp() == null) {
            message.setTimestamp(new Timestamp(System.currentTimeMillis()));
        }
        return this.save(message);
    }

    @Override
    public List<SystemMessage> getMessage(Integer receiverUserId) {
        QueryWrapper<SystemMessage> wrapper = new QueryWrapper<>();
        if (receiverUserId != null) {
            wrapper.and(w -> w.isNull("receiver_user_id").or().eq("receiver_user_id", receiverUserId));
        }
        wrapper.orderByDesc("timestamp").orderByDesc("id");
        return this.list(wrapper);
    }
}
