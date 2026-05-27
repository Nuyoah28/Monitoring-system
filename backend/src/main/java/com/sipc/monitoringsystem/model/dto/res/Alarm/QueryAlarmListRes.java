package com.sipc.monitoringsystem.model.dto.res.Alarm;

import lombok.Data;

import java.util.List;


@Data
public class QueryAlarmListRes {
    private Integer count;

    private List<GetAlarmRes> alarmList;
}
