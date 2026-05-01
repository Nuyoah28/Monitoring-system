package com.sipc.monitoringsystem.model.dto.param.iot;

import lombok.Data;

@Data
public class ReportAlarmMqttParam {
    private Integer cameraId;
    private Integer caseType;
    private String clipId;
    private String occurredAt;
}
