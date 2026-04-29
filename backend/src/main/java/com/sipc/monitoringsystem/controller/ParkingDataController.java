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

import java.sql.Timestamp;
import java.util.ArrayList;
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
    public CommonResult<ParkingRealtimeRes> getRealtime(@RequestParam Integer monitorId,
                                                        @RequestParam(defaultValue = "real") String source) {
        if ("mock".equalsIgnoreCase(source)) {
            return CommonResult.success(buildMockRealtime(monitorId));
        }

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

    private ParkingRealtimeRes buildMockRealtime(Integer monitorId) {
        long tick = System.currentTimeMillis() / 8000L;
        ParkingRealtimeRes res = new ParkingRealtimeRes();
        res.setMonitorId(monitorId);
        res.setSource("mock");
        res.setUpdateTime(new Timestamp(System.currentTimeMillis()));
        res.setZones(new ArrayList<>());

        addMockZone(res, "A", "地库A区", 56, 32, tick, 9);
        addMockZone(res, "B", "地库B区", 48, 24, tick, 11);
        addMockZone(res, "EAST", "地面东侧", 32, 16, tick, 7);
        addMockZone(res, "WEST", "地面西侧", 28, 20, tick, 6);

        int total = res.getZones().stream()
                .map(ParkingRealtimeRes.ZoneItem::getTotalSpaces)
                .filter(item -> item != null)
                .mapToInt(Integer::intValue)
                .sum();
        int occupied = res.getZones().stream()
                .map(ParkingRealtimeRes.ZoneItem::getOccupiedSpaces)
                .filter(item -> item != null)
                .mapToInt(Integer::intValue)
                .sum();

        res.setTotalSpaces(total);
        res.setOccupiedSpaces(occupied);
        res.setFreeSpaces(Math.max(total - occupied, 0));
        res.setOccupancyRate(total == 0 ? 0 : Math.round(occupied * 100F / total));
        return res;
    }

    private void addMockZone(ParkingRealtimeRes res, String areaCode, String areaName,
                             int totalSpaces, int baseOccupied, long tick, int swing) {
        int offset = (int) Math.round(Math.sin((tick + areaCode.hashCode()) * 0.75D) * swing);
        int occupied = Math.max(0, Math.min(totalSpaces, baseOccupied + offset));

        ParkingRealtimeRes.ZoneItem item = new ParkingRealtimeRes.ZoneItem();
        item.setAreaCode(areaCode);
        item.setAreaName(areaName);
        item.setTotalSpaces(totalSpaces);
        item.setOccupiedSpaces(occupied);
        res.getZones().add(item);
    }
}
