package com.sipc.monitoringsystem.model.dto.res.Alarm;

import com.sipc.monitoringsystem.model.po.Alarm.AlarmCaseTypeTotal;
import com.sipc.monitoringsystem.model.po.Alarm.AlarmTotal;
import lombok.Data;

import java.util.List;

@Data
public class RealTimeAlarmRes
{
    private AlarmTotal alarmTotal;

    private List<AlarmCaseTypeTotal> alarmCaseTypeTotalList;
}
