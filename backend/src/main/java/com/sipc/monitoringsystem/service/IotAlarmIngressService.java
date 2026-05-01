package com.sipc.monitoringsystem.service;

import com.sipc.monitoringsystem.model.po.Alarm.SqlGetAlarm;

public interface IotAlarmIngressService {
    SqlGetAlarm receiveAndDispatchAlarm(Integer cameraId, Integer caseType, String clipId, String occurredAt);
}
