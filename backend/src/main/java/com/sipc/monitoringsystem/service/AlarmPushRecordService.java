package com.sipc.monitoringsystem.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.sipc.monitoringsystem.model.po.Alarm.AlarmPushRecord;

public interface AlarmPushRecordService extends IService<AlarmPushRecord> {
    boolean saveRecord(Integer alarmId, Integer userId, String pushType, String pushStatus, String pushDetail);
}
