package com.sipc.monitoringsystem.model.dto.param.iot;

import lombok.Data;

@Data
public class ReportParkingTrafficFlowParam {
    private Integer monitorId;
    private String deviceCode;
    private String batchNo;
    private Integer inCount;
    private Integer outCount;
}
