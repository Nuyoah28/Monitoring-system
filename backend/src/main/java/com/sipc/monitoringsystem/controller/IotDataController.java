package com.sipc.monitoringsystem.controller;

import com.sipc.monitoringsystem.aop.Pass;
import com.sipc.monitoringsystem.model.dto.CommonResult;
import com.sipc.monitoringsystem.model.dto.param.iot.ReportEnvironmentParam;
import com.sipc.monitoringsystem.model.dto.param.iot.ReportParkingParam;
import com.sipc.monitoringsystem.model.dto.param.iot.ReportParkingTrafficFlowParam;
import com.sipc.monitoringsystem.service.EnvironmentDataService;
import com.sipc.monitoringsystem.service.ParkingDataService;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/iot")
public class IotDataController {

    private final EnvironmentDataService environmentDataService;
    private final ParkingDataService parkingDataService;

    public IotDataController(EnvironmentDataService environmentDataService, ParkingDataService parkingDataService) {
        this.environmentDataService = environmentDataService;
        this.parkingDataService = parkingDataService;
    }

    @PostMapping("/environment/report")
    @Pass
    public CommonResult<Integer> reportEnvironment(@RequestBody ReportEnvironmentParam param) {
        if (param == null || param.getMonitorId() == null) {
            return CommonResult.fail("monitorId不能为空");
        }
        return CommonResult.success(environmentDataService.report(param));
    }

    @PostMapping("/parking/report")
    @Pass
    public CommonResult<Integer> reportParking(@RequestBody ReportParkingParam param) {
        if (param == null || param.getMonitorId() == null) {
            return CommonResult.fail("monitorId不能为空");
        }
        return CommonResult.success(parkingDataService.report(param));
    }

    @PostMapping("/parking/traffic/report")
    @Pass
    public CommonResult<Integer> reportParkingTrafficFlow(@RequestBody ReportParkingTrafficFlowParam param) {
        if (param == null || param.getMonitorId() == null) {
            return CommonResult.fail("monitorId不能为空");
        }
        return CommonResult.success(parkingDataService.reportTrafficFlow(param));
    }
}
