package com.sipc.monitoringsystem.controller;

import com.sipc.monitoringsystem.aop.Pass;
import com.sipc.monitoringsystem.model.dto.CommonResult;
import com.sipc.monitoringsystem.model.dto.res.environment.EnvironmentRealtimeRes;
import com.sipc.monitoringsystem.model.dto.res.environment.EnvironmentTrendPointRes;
import com.sipc.monitoringsystem.service.EnvironmentDataService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/v1/env")
public class EnvironmentController {

    private final EnvironmentDataService environmentDataService;

    public EnvironmentController(EnvironmentDataService environmentDataService) {
        this.environmentDataService = environmentDataService;
    }

    @GetMapping("/realtime")
    @Pass
    public CommonResult<EnvironmentRealtimeRes> getRealtime(@RequestParam Integer monitorId) {
        EnvironmentRealtimeRes res = environmentDataService.getRealtime(monitorId);
        if (res == null) {
            return CommonResult.fail("暂无环境数据");
        }
        return CommonResult.success(res);
    }

    @GetMapping("/trend")
    @Pass
    public CommonResult<List<EnvironmentTrendPointRes>> getTrend(@RequestParam Integer monitorId,
                                                                 @RequestParam(defaultValue = "day") String range) {
        return CommonResult.success(environmentDataService.getTrend(monitorId, range));
    }
}
