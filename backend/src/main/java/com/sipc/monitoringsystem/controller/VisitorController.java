package com.sipc.monitoringsystem.controller;

import com.sipc.monitoringsystem.model.dto.CommonResult;
import com.sipc.monitoringsystem.model.dto.res.BlankRes;
import com.sipc.monitoringsystem.model.po.User.User;
import com.sipc.monitoringsystem.model.po.Visitor.VisitorInfo;
import com.sipc.monitoringsystem.service.VisitorService;
import com.sipc.monitoringsystem.service.UserService;
import com.sipc.monitoringsystem.util.JwtUtils;
import com.sipc.monitoringsystem.util.TokenThreadLocalUtil;
import jakarta.validation.constraints.NotNull;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@CrossOrigin
@RequestMapping("/api/v1/visitor")
public class VisitorController {

    @Autowired
    private VisitorService visitorService;

    @Autowired
    private UserService userService;

    @GetMapping("/list")
    public CommonResult<List<VisitorInfo>> list() {
        User currentUser = getCurrentUser();
        if (currentUser == null) {
            return CommonResult.fail("token错误");
        }
        return CommonResult.success(visitorService.listAll(currentUser));
    }

    @GetMapping("/{id}")
    public CommonResult<VisitorInfo> getById(@PathVariable @NotNull Integer id) {
        User currentUser = getCurrentUser();
        if (currentUser == null) {
            return CommonResult.fail("token错误");
        }
        VisitorInfo info = visitorService.getById(id, currentUser);
        if (info == null) {
            return CommonResult.fail("访客记录不存在");
        }
        return CommonResult.success(info);
    }

    @PostMapping("/create")
    public CommonResult<Integer> create(@RequestBody VisitorInfo info) {
        User currentUser = getCurrentUser();
        if (currentUser == null) {
            return CommonResult.fail("token错误");
        }
        Integer id = visitorService.create(info, currentUser);
        if (id == null || id < 0) {
            return CommonResult.fail("创建访客记录失败");
        }
        return CommonResult.success(id);
    }

    @PutMapping("/update")
    public CommonResult<BlankRes> update(@RequestBody VisitorInfo info) {
        if (info == null || info.getId() == null) {
            return CommonResult.fail("id不能为空");
        }
        User currentUser = getCurrentUser();
        if (currentUser == null) {
            return CommonResult.fail("token错误");
        }
        if (!visitorService.update(info, currentUser)) {
            return CommonResult.fail("更新访客记录失败");
        }
        return CommonResult.success("更新访客记录成功");
    }

    @DeleteMapping("/{id}")
    public CommonResult<BlankRes> delete(@PathVariable @NotNull Integer id) {
        User currentUser = getCurrentUser();
        if (currentUser == null) {
            return CommonResult.fail("token错误");
        }
        if (!visitorService.delete(id, currentUser)) {
            return CommonResult.fail("删除访客记录失败");
        }
        return CommonResult.success("删除访客记录成功");
    }

    private User getCurrentUser() {
        User tokenUser = JwtUtils.getUserByToken(TokenThreadLocalUtil.getInstance().getToken());
        return tokenUser == null ? null : userService.getById(tokenUser.getId());
    }
}
