package com.sipc.monitoringsystem.controller;

import com.sipc.monitoringsystem.model.dto.CommonResult;
import com.sipc.monitoringsystem.model.dto.res.BlankRes;
import com.sipc.monitoringsystem.model.po.Visitor.VisitorInfo;
import com.sipc.monitoringsystem.service.VisitorService;
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

    @GetMapping("/list")
    public CommonResult<List<VisitorInfo>> list() {
        return CommonResult.success(visitorService.listAll());
    }

    @GetMapping("/{id}")
    public CommonResult<VisitorInfo> getById(@PathVariable @NotNull Integer id) {
        VisitorInfo info = visitorService.getById(id);
        if (info == null) {
            return CommonResult.fail("访客记录不存在");
        }
        return CommonResult.success(info);
    }

    @PostMapping("/create")
    public CommonResult<Integer> create(@RequestBody VisitorInfo info) {
        Integer id = visitorService.create(info);
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
        if (!visitorService.update(info)) {
            return CommonResult.fail("更新访客记录失败");
        }
        return CommonResult.success("更新访客记录成功");
    }

    @DeleteMapping("/{id}")
    public CommonResult<BlankRes> delete(@PathVariable @NotNull Integer id) {
        if (!visitorService.delete(id)) {
            return CommonResult.fail("删除访客记录失败");
        }
        return CommonResult.success("删除访客记录成功");
    }
}
