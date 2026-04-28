package com.sipc.monitoringsystem.service;

import com.sipc.monitoringsystem.model.dto.param.iot.ReportParkingParam;
import com.sipc.monitoringsystem.model.dto.res.parking.ParkingRealtimeRes;
import com.sipc.monitoringsystem.model.dto.res.parking.ParkingTrendPointRes;

import java.util.List;

public interface ParkingDataService {
    int report(ReportParkingParam param);

    ParkingRealtimeRes getRealtime(Integer monitorId);

    List<ParkingTrendPointRes> getTrend(Integer monitorId, String range);
}
