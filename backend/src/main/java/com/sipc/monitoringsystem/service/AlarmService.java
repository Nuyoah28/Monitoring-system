package com.sipc.monitoringsystem.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.sipc.monitoringsystem.model.dto.res.Alarm.GetHistoryCntRes;
import com.sipc.monitoringsystem.model.dto.res.Alarm.RealTimeAlarmRes;
import com.sipc.monitoringsystem.model.po.Alarm.Alarm;
import com.sipc.monitoringsystem.model.po.Alarm.SqlGetAlarm;
import com.sipc.monitoringsystem.model.po.Alarm.TimePeriod;
import com.sipc.monitoringsystem.model.po.User.User;

import java.util.List;

public interface AlarmService extends IService<Alarm> {
        SqlGetAlarm receiveAlarm(Integer cameraId, Integer caseType, String clipLink);

        List<SqlGetAlarm> queryAlarmList(Integer pageNum, Integer pageSize, Integer caseType, Integer status,
                        Integer warningLevel, String time1, String time2);

        // 新增：根据用户权限获取报警列表
        List<SqlGetAlarm> queryAlarmList(Integer pageNum, Integer pageSize, Integer caseType, Integer status,
                        Integer warningLevel, String time1, String time2, User user);

        SqlGetAlarm getAlarm(Integer alarmId);

        Long getAlarmCnt(Integer caseType, String time1, String time2);

        Boolean updateAlarm(Integer alarmId, Boolean status, String processingContent);

        Boolean deleteAlarm(Integer alarmId);

        List<TimePeriod> getDayHistoryCnt(String date);

        List<TimePeriod> getThreeDaysHistoryCnt(String date);

        List<TimePeriod> getWeekHistoryCnt(String date);

        List<TimePeriod> getDayAreasHistoryCnt(String date);

        List<TimePeriod> getThreeDaysAreasHistoryCnt(String date);

        List<TimePeriod> getWeekAreasHistoryCnt(String date);

        List<TimePeriod> SqlGetCaseTypesDayHistoryCnt(String date);

        List<TimePeriod> SqlGetCaseTypesThreeDaysHistoryCnt(String date);

        List<TimePeriod> SqlGetCaseTypesWeekHistoryCnt(String date);

        // 近一个月 (30天)
        List<TimePeriod> getMonthHistoryCnt(String date);

        List<TimePeriod> getMonthAreasHistoryCnt(String date);

        List<TimePeriod> SqlGetCaseTypesMonthHistoryCnt(String date);

        RealTimeAlarmRes getRealTimeAlarmRes();

        GetHistoryCntRes ServiceGetHistoryCntRes(Integer defer);
}
