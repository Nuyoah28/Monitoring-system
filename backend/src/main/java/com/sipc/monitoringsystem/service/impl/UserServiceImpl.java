package com.sipc.monitoringsystem.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.sipc.monitoringsystem.dao.UserDao;
import com.sipc.monitoringsystem.model.dto.param.user.UpdateProfileParam;
import com.sipc.monitoringsystem.model.po.User.User;
import com.sipc.monitoringsystem.service.UserService;
import com.sipc.monitoringsystem.util.JwtUtils;
import com.sipc.monitoringsystem.util.MD5Util;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

/**
 * @author CZCZCZ
 * &#064;date 2023-09-10 17:27
 */

@Slf4j
@Service
public class UserServiceImpl extends ServiceImpl<UserDao, User> implements UserService {

    @Autowired
    MonitorServiceImpl monitorService;

    @Override
    public String login(String userName, String password) {
        userName = normalize(userName);
        if (userName == null) {
            return null;
        }
        password = MD5Util.MD5Encode(password);
        User user = getOne(new QueryWrapper<User>().eq("user_name", userName).eq("password", password), false);
        if (user != null) {
            return JwtUtils.signUser(user);
        }
        return null;
    }

    @Override
    public Boolean register(String username, String password, Integer role, String homeArea) {
        username = normalize(username);
        if (username == null || password == null || role == null) {
            return false;
        }
        User existed = getOne(new QueryWrapper<User>().eq("user_name", username), false);
        if (existed != null) {
            log.warn("注册失败：用户名已存在 {}", username);
            return false;
        }
        User user = new User();
        user.setUserName(username);
        user.setPassword(MD5Util.MD5Encode(password));
        user.setRole(role);
        user.setIsResident(Integer.valueOf(1).equals(role));
        user.setNotifyEnabled(true);
        user.setHomeArea(normalize(homeArea));
        try{
            save(user);
            return true;
        }catch (Exception e){
            log.error("注册失败");
            return false;
        }

    }

    @Override
    public Boolean updatePassword(Integer id, String oldPassword, String newPassword){
        User user = getOne(new QueryWrapper<User>().eq("id", id).eq("password", MD5Util.MD5Encode(oldPassword)));
        if (user == null){
            return false;
        }
        user.setPassword(MD5Util.MD5Encode(newPassword));
        try{
            updateById(user);
            return true;
        }catch (Exception e){
            log.error("修改密码失败");
            return false;
        }
    }

    @Override
    public Boolean updateName(Integer id, String newName){
        User user = getById(id);
        if (user == null){
            return false;
        }
        newName = normalize(newName);
        if (newName == null) {
            return false;
        }
        User existed = getOne(new QueryWrapper<User>().eq("user_name", newName).ne("id", id), false);
        if (existed != null) {
            log.warn("修改用户名失败：用户名已存在 {}", newName);
            return false;
        }
        String oldName = user.getUserName();
        user.setUserName(newName);
        try{
            if (monitorService.updateLeaders(oldName,newName) && updateById(user))
            return true;
        }catch (Exception e){
            log.error("修改用户名失败");
            return false;
        }
        return false;
    }

    @Override
    public Boolean updateProfile(Integer id, UpdateProfileParam param) {
        User user = getById(id);
        if (user == null || param == null) {
            return false;
        }

        String oldName = user.getUserName();
        String newName = normalize(param.getUserName());
        if (newName != null && !newName.equals(oldName)) {
            user.setUserName(newName);
        }
        if (param.getHomeArea() != null) {
            user.setHomeArea(normalize(param.getHomeArea()));
        }
        if (param.getAvatarUrl() != null) {
            user.setAvatarUrl(normalize(param.getAvatarUrl()));
        }
        if (param.getNotifyEnabled() != null) {
            user.setNotifyEnabled(param.getNotifyEnabled());
        }

        try {
            if (newName != null && !newName.equals(oldName) && !monitorService.updateLeaders(oldName, newName)) {
                return false;
            }
            return updateById(user);
        } catch (Exception e) {
            log.error("修改用户资料失败", e);
            return false;
        }
    }

    private String normalize(String value) {
        if (value == null) {
            return null;
        }
        String trimmed = value.trim();
        return trimmed.isEmpty() ? null : trimmed;
    }



}
