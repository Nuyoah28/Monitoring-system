package com.sipc.monitoringsystem.model.po.Alarm;

import lombok.Data;

@Data
public class AlarmTotal {

    private Integer total;

    private Integer todayNew;

    private Integer dayChange;
}
