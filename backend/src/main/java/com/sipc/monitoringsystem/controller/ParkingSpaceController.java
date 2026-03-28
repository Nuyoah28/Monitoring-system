package com.sipc.monitoringsystem.controller;

import com.sipc.monitoringsystem.model.dto.CommonResult;
import com.sipc.monitoringsystem.model.dto.res.BlankRes;
import com.sipc.monitoringsystem.model.po.Parking.ParkingSpaceInfo;
import com.sipc.monitoringsystem.service.ParkingSpaceService;
import jakarta.validation.constraints.NotNull;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@CrossOrigin
@RequestMapping("/api/v1/parking-space")
public class ParkingSpaceController {

    @Autowired
    private ParkingSpaceService parkingSpaceService;

    @GetMapping("/list")
    public CommonResult<List<ParkingSpaceInfo>> list() {
        return CommonResult.success(parkingSpaceService.listAll());
    }

    @GetMapping("/{id}")
    public CommonResult<ParkingSpaceInfo> getById(@PathVariable @NotNull Integer id) {
        ParkingSpaceInfo info = parkingSpaceService.getById(id);
        if (info == null) {
            return CommonResult.fail("车位记录不存在");
        }
        return CommonResult.success(info);
    }

    @PostMapping("/create")
    public CommonResult<Integer> create(@RequestBody ParkingSpaceInfo info) {
        Integer id = parkingSpaceService.create(info);
        if (id == null || id < 0) {
            return CommonResult.fail("创建车位记录失败");
        }
        return CommonResult.success(id);
    }

    @PutMapping("/update")
    public CommonResult<BlankRes> update(@RequestBody ParkingSpaceInfo info) {
        if (info == null || info.getId() == null) {
            return CommonResult.fail("id不能为空");
        }
        if (!parkingSpaceService.update(info)) {
            return CommonResult.fail("更新车位记录失败");
        }
        return CommonResult.success("更新车位记录成功");
    }

    @DeleteMapping("/{id}")
    public CommonResult<BlankRes> delete(@PathVariable @NotNull Integer id) {
        if (!parkingSpaceService.delete(id)) {
            return CommonResult.fail("删除车位记录失败");
        }
        return CommonResult.success("删除车位记录成功");
    }
}
