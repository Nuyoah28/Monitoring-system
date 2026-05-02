package com.sipc.monitoringsystem.controller;

import com.sipc.monitoringsystem.model.dto.CommonResult;
import com.sipc.monitoringsystem.model.dto.res.BlankRes;
import com.sipc.monitoringsystem.model.po.DeviceRepair.DeviceRepairInfo;
import com.sipc.monitoringsystem.model.po.User.User;
import com.sipc.monitoringsystem.service.DeviceRepairService;
import com.sipc.monitoringsystem.service.UserService;
import com.sipc.monitoringsystem.util.JwtUtils;
import com.sipc.monitoringsystem.util.TokenThreadLocalUtil;
import jakarta.validation.constraints.NotNull;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@CrossOrigin
@RequestMapping("/api/v1/device-repair")
public class DeviceRepairController {

    @Autowired
    private DeviceRepairService deviceRepairService;

    @Autowired
    private UserService userService;

    @GetMapping("/list")
    public CommonResult<List<DeviceRepairInfo>> list() {
        User currentUser = getCurrentUser();
        if (currentUser == null) {
            return CommonResult.fail("token错误");
        }
        return CommonResult.success(deviceRepairService.listAll(currentUser));
    }

    @GetMapping("/{id}")
    public CommonResult<DeviceRepairInfo> getById(@PathVariable @NotNull Integer id) {
        User currentUser = getCurrentUser();
        if (currentUser == null) {
            return CommonResult.fail("token错误");
        }
        DeviceRepairInfo info = deviceRepairService.getById(id, currentUser);
        if (info == null) {
            return CommonResult.fail("设备报修记录不存在");
        }
        return CommonResult.success(info);
    }

    @PostMapping("/create")
    public CommonResult<Integer> create(@RequestBody DeviceRepairInfo info) {
        User currentUser = getCurrentUser();
        if (currentUser == null) {
            return CommonResult.fail("token错误");
        }
        Integer id = deviceRepairService.create(info, currentUser);
        if (id == null || id < 0) {
            return CommonResult.fail("创建设备报修失败");
        }
        return CommonResult.success(id);
    }

    @PutMapping("/update")
    public CommonResult<BlankRes> update(@RequestBody DeviceRepairInfo info) {
        if (info == null || info.getId() == null) {
            return CommonResult.fail("id不能为空");
        }
        User currentUser = getCurrentUser();
        if (currentUser == null) {
            return CommonResult.fail("token错误");
        }
        if (!deviceRepairService.update(info, currentUser)) {
            return CommonResult.fail("更新设备报修失败");
        }
        return CommonResult.success("更新设备报修成功");
    }

    @DeleteMapping("/{id}")
    public CommonResult<BlankRes> delete(@PathVariable @NotNull Integer id) {
        User currentUser = getCurrentUser();
        if (currentUser == null) {
            return CommonResult.fail("token错误");
        }
        if (!deviceRepairService.delete(id, currentUser)) {
            return CommonResult.fail("删除设备报修失败");
        }
        return CommonResult.success("删除设备报修成功");
    }

    private User getCurrentUser() {
        User tokenUser = JwtUtils.getUserByToken(TokenThreadLocalUtil.getInstance().getToken());
        return tokenUser == null ? null : userService.getById(tokenUser.getId());
    }
}
