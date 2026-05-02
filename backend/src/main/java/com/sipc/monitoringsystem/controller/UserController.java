package com.sipc.monitoringsystem.controller;

import com.sipc.monitoringsystem.aop.Pass;
import com.sipc.monitoringsystem.model.dto.CommonResult;
import com.sipc.monitoringsystem.model.dto.param.user.LoginParam;
import com.sipc.monitoringsystem.model.dto.param.user.RegisterParam;
import com.sipc.monitoringsystem.model.dto.param.user.UpdateProfileParam;
import com.sipc.monitoringsystem.model.dto.param.user.UpdatePasswordParam;
import com.sipc.monitoringsystem.model.dto.res.BlankRes;
import com.sipc.monitoringsystem.model.dto.res.User.LoginRes;
import com.sipc.monitoringsystem.model.dto.res.User.ProfileRes;
import com.sipc.monitoringsystem.model.po.User.User;
import com.sipc.monitoringsystem.service.impl.UserServiceImpl;
import com.sipc.monitoringsystem.util.JwtUtils;
import com.sipc.monitoringsystem.util.TokenThreadLocalUtil;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotNull;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

/**
 * @author CZCZCZ
 * &#064;date 2023-09-10 17:26
 */
@Validated
@CrossOrigin
@RestController
@RequestMapping("/api/v1/user")
public class UserController {
    @Autowired
    UserServiceImpl userService;

    @Pass
    @PostMapping("/login")
    public CommonResult<LoginRes> login(@Valid @RequestBody LoginParam loginParam) {
        String token = userService.login(loginParam.getUserName(), loginParam.getPassword());
        if (token == null) {
            return CommonResult.fail("用户名或密码错误");
        }
        User user = JwtUtils.getUserByToken(token);
        user = userService.getById(user.getId());
        if (user == null || !Integer.valueOf(0).equals(user.getRole())) {
            return CommonResult.fail("请使用管理端账号登录");
        }
        return CommonResult.success(buildLoginRes(user, token));
    }

    @PostMapping("/owner/login")
    @Pass
    public CommonResult<LoginRes> ownerLogin(@Valid @RequestBody LoginParam loginParam) {
        String token = userService.login(loginParam.getUserName(), loginParam.getPassword());
        if (token == null) {
            return CommonResult.fail("用户名或密码错误");
        }
        User user = JwtUtils.getUserByToken(token);
        user = userService.getById(user.getId());
        if (user == null || !Integer.valueOf(1).equals(user.getRole())) {
            return CommonResult.fail("请使用业主端账号登录");
        }
        return CommonResult.success(buildLoginRes(user, token));
    }

    @Pass
    @PostMapping("/register")
    public CommonResult<BlankRes> register(@Valid @RequestBody RegisterParam registerParam) {
        if (userService.register(registerParam.getUsername(), registerParam.getPassword(), registerParam.getRole(),
                registerParam.getHomeArea())) {
            return CommonResult.success("注册成功");
        } else {
            return CommonResult.fail("注册失败");
        }
    }

    @PostMapping("/update/password")
    public CommonResult<BlankRes> updatePassword(@Valid @RequestBody UpdatePasswordParam updatePasswordParam) {
        User user = JwtUtils.getUserByToken(TokenThreadLocalUtil.getInstance().getToken());
        if (user == null) {
            return CommonResult.fail("token错误");
        }
        if (userService.updatePassword(user.getId(), updatePasswordParam.getOldPassword(), updatePasswordParam.getNewPassword())) {
            return CommonResult.success("修改成功");
        }

        return CommonResult.fail("密码错误");
    }

    @PostMapping("/update/name/{name}")
    public CommonResult<BlankRes> updateName(@PathVariable @NotNull String name) {
        User user = JwtUtils.getUserByToken(TokenThreadLocalUtil.getInstance().getToken());
        if (userService.updateName(user.getId(), name)) {
            return CommonResult.success("修改成功");
        }

        return CommonResult.fail("修改失败");
    }

    @GetMapping("/profile")
    public CommonResult<ProfileRes> getProfile() {
        User tokenUser = JwtUtils.getUserByToken(TokenThreadLocalUtil.getInstance().getToken());
        User user = userService.getById(tokenUser.getId());
        if (user == null) {
            return CommonResult.fail("用户不存在");
        }
        return CommonResult.success(new ProfileRes(user));
    }

    @PostMapping("/profile")
    public CommonResult<ProfileRes> updateProfile(@RequestBody UpdateProfileParam updateProfileParam) {
        User tokenUser = JwtUtils.getUserByToken(TokenThreadLocalUtil.getInstance().getToken());
        if (!userService.updateProfile(tokenUser.getId(), updateProfileParam)) {
            return CommonResult.fail("修改失败");
        }
        User user = userService.getById(tokenUser.getId());
        if (user == null) {
            return CommonResult.fail("用户不存在");
        }
        return CommonResult.success(new ProfileRes(user));
    }

    /**
     * Token刷新接口
     * 如果token即将过期（剩余时间少于7天），可以调用此接口获取新token
     */
    @Pass
    @PostMapping("/refresh")
    public CommonResult<LoginRes> refreshToken(@RequestHeader(value = "Authorization", required = false) String authHeader) {
        // 兼容 App 端的裸 token 和 Web 端常见的 Bearer token。
        String token = null;
        if (authHeader != null && !authHeader.isBlank()) {
            token = authHeader.startsWith("Bearer ") ? authHeader.substring(7).trim() : authHeader.trim();
        }
        
        if (token == null || token.isEmpty()) {
            return CommonResult.fail("Token不能为空");
        }
        
        // 验证token是否有效（即使快过期也可以刷新）
        if (!JwtUtils.verify(token)) {
            return CommonResult.fail("Token无效或已过期，请重新登录");
        }
        
        try {
            // 从token中获取用户信息
            User user = JwtUtils.getUserByToken(token);
            // 从数据库获取最新用户信息
            user = userService.getById(user.getId());
            if (user == null) {
                return CommonResult.fail("用户不存在");
            }
            
            // 生成新token
            String newToken = JwtUtils.signUser(user);
            
            return CommonResult.success(buildLoginRes(user, newToken));
        } catch (Exception e) {
            return CommonResult.fail("Token刷新失败: " + e.getMessage());
        }
    }

    private LoginRes buildLoginRes(User user, String token) {
        LoginRes loginRes = new LoginRes();
        loginRes.setId(user.getId());
        loginRes.setName(user.getUserName());
        loginRes.setPhone(user.getPhone());
        loginRes.setRole(user.getRole());
        loginRes.setAvatarUrl(user.getAvatarUrl());
        loginRes.setHomeArea(user.getHomeArea());
        loginRes.setNotifyEnabled(user.getNotifyEnabled());
        loginRes.setToken(token);
        return loginRes;
    }

}
