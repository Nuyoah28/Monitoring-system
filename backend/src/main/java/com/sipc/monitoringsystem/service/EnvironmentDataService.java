package com.sipc.monitoringsystem.service;

import com.sipc.monitoringsystem.model.dto.param.iot.ReportEnvironmentParam;
import com.sipc.monitoringsystem.model.dto.res.environment.EnvironmentRealtimeRes;
import com.sipc.monitoringsystem.model.dto.res.environment.EnvironmentTrendPointRes;

import java.util.List;

public interface EnvironmentDataService {
    Integer report(ReportEnvironmentParam param);

    EnvironmentRealtimeRes getRealtime(Integer monitorId);

    List<EnvironmentTrendPointRes> getTrend(Integer monitorId, String range);
}
