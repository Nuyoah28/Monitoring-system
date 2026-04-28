package com.sipc.monitoringsystem.controller;

import com.sipc.monitoringsystem.aop.Pass;
import com.sipc.monitoringsystem.model.dto.CommonResult;
import com.sipc.monitoringsystem.model.dto.res.parking.ParkingRealtimeRes;
import com.sipc.monitoringsystem.model.dto.res.parking.ParkingTrendPointRes;
import com.sipc.monitoringsystem.service.ParkingDataService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/v1/parking")
public class ParkingDataController {

    private final ParkingDataService parkingDataService;

    public ParkingDataController(ParkingDataService parkingDataService) {
        this.parkingDataService = parkingDataService;
    }

    @GetMapping("/realtime")
    @Pass
    public CommonResult<ParkingRealtimeRes> getRealtime(@RequestParam Integer monitorId) {
        ParkingRealtimeRes res = parkingDataService.getRealtime(monitorId);
        if (res == null) {
            return CommonResult.fail("暂无车位数据");
        }
        return CommonResult.success(res);
    }

    @GetMapping("/trend")
    @Pass
    public CommonResult<List<ParkingTrendPointRes>> getTrend(@RequestParam Integer monitorId,
                                                             @RequestParam(defaultValue = "day") String range) {
        return CommonResult.success(parkingDataService.getTrend(monitorId, range));
    }
}
