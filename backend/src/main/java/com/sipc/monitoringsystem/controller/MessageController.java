package com.sipc.monitoringsystem.controller;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.sipc.monitoringsystem.model.dto.CommonResult;
import com.sipc.monitoringsystem.model.dto.res.BlankRes;
import com.sipc.monitoringsystem.model.po.Message.SystemMessage;
import com.sipc.monitoringsystem.model.po.User.User;
import com.sipc.monitoringsystem.service.SystemMessageService;
import com.sipc.monitoringsystem.service.UserService;
import com.sipc.monitoringsystem.util.JwtUtils;
import com.sipc.monitoringsystem.util.TokenThreadLocalUtil;

import lombok.extern.slf4j.Slf4j;

@Slf4j
@RestController
@CrossOrigin
@RequestMapping("/api/v1/system/message")
public class MessageController {
    @Autowired
    SystemMessageService systemMessageService;
    @Autowired
    UserService userService;

    @PostMapping("/addMessage")
    public CommonResult<BlankRes> addMessage(SystemMessage message){
        User tokenUser = JwtUtils.getUserByToken(TokenThreadLocalUtil.getInstance().getToken());
        User user = userService.getById(tokenUser.getId());
        if (user == null) {
            user = tokenUser;
        }
        //TODO: if not manager, return fail
        if(!systemMessageService.addMessage(message)){
            return CommonResult.fail("添加消息失败");
        }
        else{
            return CommonResult.success("添加消息成功");
        }
    }

    @RequestMapping("/getMessage")
    public CommonResult<List<SystemMessage>> getMessage(SystemMessage message){
        return CommonResult.success(systemMessageService.getMessage(message));
    }
}
