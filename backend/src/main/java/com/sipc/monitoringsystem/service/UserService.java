package com.sipc.monitoringsystem.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.sipc.monitoringsystem.model.po.User.User;

/**
 * @author CZCZCZ
 *         &#064;date 2023-09-10 17:27
 */
public interface UserService extends IService<User> {

    String login(String phone, String password);

    Boolean register(String username, String password, Integer role);

    Boolean updatePassword(Integer id, String oldPassword, String newPassword);

    Boolean updateName(Integer id, String name);

}
