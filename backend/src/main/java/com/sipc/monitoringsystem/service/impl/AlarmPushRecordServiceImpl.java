package com.sipc.monitoringsystem.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.sipc.monitoringsystem.dao.AlarmPushRecordDao;
import com.sipc.monitoringsystem.model.po.Alarm.AlarmPushRecord;
import com.sipc.monitoringsystem.service.AlarmPushRecordService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Slf4j
@Service
public class AlarmPushRecordServiceImpl extends ServiceImpl<AlarmPushRecordDao, AlarmPushRecord>
        implements AlarmPushRecordService {

    @Override
    public boolean saveRecord(Integer alarmId, Integer userId, String pushType, String pushStatus, String pushDetail) {
        if (alarmId == null || userId == null) {
            return false;
        }
        AlarmPushRecord record = new AlarmPushRecord();
        record.setAlarmId(alarmId);
        record.setUserId(userId);
        record.setPushType(pushType);
        record.setPushStatus(pushStatus);
        record.setPushDetail(pushDetail);
        try {
            return this.save(record);
        } catch (Exception e) {
            log.warn("保存推送记录失败 alarmId={}, userId={}, pushType={}, reason={}",
                    alarmId, userId, pushType, e.getMessage());
            return false;
        }
    }
}
