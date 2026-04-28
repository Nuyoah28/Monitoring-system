package com.sipc.monitoringsystem.model.dto.param.iot;

import lombok.Data;

@Data
public class ReportEnvironmentParam {
    private Integer monitorId;
    private String deviceCode;
    private Float temperature;
    private Float humidity;
    private Float pm25;
    private Float combustibleGas;
}
