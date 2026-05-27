package com.sipc.monitoringsystem.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.sipc.monitoringsystem.model.dto.param.user.UpdateProfileParam;
import com.sipc.monitoringsystem.model.po.User.User;


public interface UserService extends IService<User> {

    String login(String phone, String password);

    Boolean register(String username, String password, Integer role, String homeArea);

    Boolean updatePassword(Integer id, String oldPassword, String newPassword);

    Boolean updateName(Integer id, String name);

    Boolean updateProfile(Integer id, UpdateProfileParam param);

}
