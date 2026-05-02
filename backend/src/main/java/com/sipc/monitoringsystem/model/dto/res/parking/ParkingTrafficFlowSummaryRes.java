package com.sipc.monitoringsystem.model.dto.res.parking;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Data;

import java.sql.Timestamp;

@Data
public class ParkingTrafficFlowSummaryRes {
    private Integer monitorId;
    private String source;
    private Integer todayInCount;
    private Integer todayOutCount;
    private Integer todayNetFlow;
    private Integer todayTotalFlow;
    private Integer latestInCount;
    private Integer latestOutCount;
    private Integer latestNetFlow;
    private Integer latestTotalFlow;

    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private Timestamp updateTime;
}
