package com.sipc.monitoringsystem.model.po.Alarm;

import lombok.Data;

/**
 * 报警类型与区域聚合统计投影
 */
@Data
public class AlarmTypeAreaCount {
    private String area;
    private String caseTypeName;
    private Long cnt;
}
