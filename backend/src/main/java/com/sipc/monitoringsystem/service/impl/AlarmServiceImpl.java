package com.sipc.monitoringsystem.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.sipc.monitoringsystem.dao.AlarmDao;
import com.sipc.monitoringsystem.model.dto.CommonResult;
import com.sipc.monitoringsystem.model.dto.res.Alarm.GetHistoryCntRes;
import com.sipc.monitoringsystem.model.dto.res.Alarm.RealTimeAlarmRes;
import com.sipc.monitoringsystem.model.po.Alarm.SqlGetAlarm;
import com.sipc.monitoringsystem.model.po.Alarm.Alarm;
import com.sipc.monitoringsystem.model.po.Alarm.TimePeriod;
import com.sipc.monitoringsystem.model.po.Monitor.Monitor;
import com.sipc.monitoringsystem.model.po.User.User;
import com.sipc.monitoringsystem.service.AlarmService;
import com.sipc.monitoringsystem.service.MonitorService;
import com.sipc.monitoringsystem.util.OssUtil;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;

@Service
@Slf4j
public class AlarmServiceImpl extends ServiceImpl<AlarmDao, Alarm> implements AlarmService {

    @Autowired
    MonitorServiceImpl monitorServiceImpl;

    @Autowired
    OssUtil ossUtil;

    @Override
    public SqlGetAlarm receiveAlarm(Integer cameraId, Integer caseType, String clipLink) {
        log.info("receive alarm from camera: " + cameraId + " caseType: " + caseType);
        monitorServiceImpl.getBaseMapper().MonitorAlarmCntPlusOne(cameraId);
        Alarm alarm = new Alarm();
        alarm.setClipLink(clipLink);
        alarm.setCaseType(caseType);
        alarm.setMonitorId(cameraId);
        alarm.setWarningLevel(1);
        alarm.setStatus(false);
        this.save(alarm);
        // 获取数据库中的sqlalarm,找id最大且监控id对的上的
        Alarm latestAlarm = this.baseMapper.selectOne(
                new QueryWrapper<Alarm>()
                        .eq("monitor_id", cameraId)
                        .orderByDesc("id")
                        .last("LIMIT 1"));
        if (latestAlarm == null) {
            throw new RuntimeException("Failed to retrieve the saved alarm record");
        }
        SqlGetAlarm sqlAlarm = this.baseMapper.SqlGetAlarm(latestAlarm.getId());
        return sqlAlarm;
    }

    @Override
    public SqlGetAlarm getAlarm(Integer alarmId) {
        SqlGetAlarm sqlGetAlarm = this.baseMapper.SqlGetAlarm(alarmId);
        sqlGetAlarm.setClipLink(ossUtil.getClipLinkByUuid(sqlGetAlarm.getClipLink()));
        return sqlGetAlarm;
    }

    @Override
    public List<SqlGetAlarm> queryAlarmList(Integer pageNum, Integer pageSize, Integer caseType, Integer status,
            Integer warningLevel, String time1, String time2) {
        List<SqlGetAlarm> alarms = this.baseMapper.selectAllTest();
        log.info("alarms size: " + alarms.size());
        for (SqlGetAlarm alarm : alarms) {
            alarm.setClipLink(ossUtil.getClipLinkByUuid(alarm.getClipLink()));
        }
        if (alarms.isEmpty())
            return alarms;

        return alarms;
    }

    /**
     * 新增：根据用户权限获取报警列表
     * role = 0 (管理员): 返回所有报警
     * role = 1 (普通用户): 只返回自己负责的监控产生的报警
     */
    @Override
    public List<SqlGetAlarm> queryAlarmList(Integer pageNum, Integer pageSize, Integer caseType, Integer status,
            Integer warningLevel, String time1, String time2, User user) {
        List<SqlGetAlarm> alarms = this.baseMapper.selectAllTest();
        log.info("alarms size before filter: " + alarms.size());

        // 如果是普通用户，过滤只显示自己负责的监控的报警
        if (user.getRole() != 0) {
            // 获取用户负责的监控ID列表
            List<Monitor> userMonitors = monitorServiceImpl.getMonitorList(user);
            Set<Integer> userMonitorIds = userMonitors.stream()
                    .map(Monitor::getId)
                    .collect(Collectors.toSet());

            // 过滤报警：只保留属于用户负责的监控的报警（根据监控ID匹配）
            alarms = alarms.stream()
                    .filter(alarm -> userMonitorIds.contains(alarm.getMonitorId()))
                    .collect(Collectors.toList());
            log.info("alarms size after filter for user " + user.getUserName() + ": " + alarms.size());
        }

        for (SqlGetAlarm alarm : alarms) {
            alarm.setClipLink(ossUtil.getClipLinkByUuid(alarm.getClipLink()));
        }
        if (alarms.isEmpty())
            return alarms;

        return alarms;
    }

    @Override
    public Long getAlarmCnt(Integer caseType, String time1, String time2) {
        QueryWrapper<Alarm> queryWrapper = new QueryWrapper<>();
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");
        if (caseType != null) {
            queryWrapper.eq("case_type", caseType);
        }

        if (time1 != null && time2 != null) {
            try {
                Date date1 = sdf.parse(time1);
                Date date2 = sdf.parse(time2);
                queryWrapper.between("time", date1, date2);
            } catch (ParseException e) {
                log.error(e.getMessage());
                return null;
            }
        }

        if (time1 != null && time2 == null) {
            try {
                Date date1 = sdf.parse(time1);
                queryWrapper.ge("time", date1);
            } catch (ParseException e) {
                log.error(e.getMessage());
                return null;
            }
        }

        if (time1 == null && time2 != null) {
            try {
                Date date2 = sdf.parse(time2);
                queryWrapper.le("time", date2);
            } catch (ParseException e) {
                log.error(e.getMessage());
                return null;
            }
        }

        return this.count(queryWrapper);

    }

    @Override
    public Boolean updateAlarm(Integer alarmId, Boolean status, String processingContent) {
        Alarm alarm = this.getById(alarmId);
        if (alarm == null)
            return false;
        alarm.setStatus(status);
        alarm.setProcessingContent(processingContent);
        return this.updateById(alarm);
    }

    @Override
    public Boolean deleteAlarm(Integer alarmId) {
        return this.removeById(alarmId);
    }

    @Override
    public List<TimePeriod> getDayHistoryCnt(String date) {
        List<TimePeriod> timePeriods = this.baseMapper.SqlGetDayHistoryCnt(date);

        // 生成一个包含所有时间段的完整列表
        List<String> allPeriods = Arrays.asList("03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00", "24:00");

        // 对齐补齐时间
        Alignment(allPeriods, timePeriods);

        return timePeriods;

    }

    @Override
    public List<TimePeriod> getDayAreasHistoryCnt(String date) {
        return this.baseMapper.SqlGetAreasDayHistoryCnt(date);
    }

    @Override
    public List<TimePeriod> getThreeDaysHistoryCnt(String date) {
        List<String> allPeriods = new ArrayList<>();
        Calendar calendar = Calendar.getInstance();
        calendar.setTime(new Date());
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");
        for (int i = 0; i < 3; i++) {
            allPeriods.add(sdf.format(calendar.getTime()));
            calendar.add(Calendar.DAY_OF_YEAR, -1);
        }
        List<TimePeriod> timePeriods = this.baseMapper.SqlGetThreeDaysHistoryCnt(date);
        Alignment(allPeriods, timePeriods);
        // 只保留月份和日期
        for (TimePeriod tp : timePeriods) {
            tp.setPeriod(tp.getPeriod().substring(5));
        }
        return timePeriods;
    }

    @Override
    public List<TimePeriod> getWeekHistoryCnt(String date) {
        List<String> allPeriods = new ArrayList<>();
        Calendar calendar = Calendar.getInstance();
        calendar.setTime(new Date());
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");
        for (int i = 0; i < 7; i++) {
            allPeriods.add(sdf.format(calendar.getTime()));
            calendar.add(Calendar.DAY_OF_YEAR, -1);
        }
        List<TimePeriod> timePeriods = this.baseMapper.SqlGetWeekHistoryCnt(date);
        Alignment(allPeriods, timePeriods);
        // 只保留月份和日期
        for (TimePeriod tp : timePeriods) {
            tp.setPeriod(tp.getPeriod().substring(5));
        }
        return timePeriods;
    }

    @Override
    public List<TimePeriod> getThreeDaysAreasHistoryCnt(String date) {
        return this.baseMapper.SqlGetAreasThreeDaysHistoryCnt(date);
    }

    @Override
    public List<TimePeriod> getWeekAreasHistoryCnt(String date) {
        return this.baseMapper.SqlGetAreasWeekHistoryCnt(date);
    }

    @Override
    @Cacheable(value = "cache", key = "'getRealTimeAlarmRes'", unless = "#result==null")
    public RealTimeAlarmRes getRealTimeAlarmRes() {
        RealTimeAlarmRes realTimeAlarmRes = new RealTimeAlarmRes();
        try {
            realTimeAlarmRes.setAlarmTotal(this.baseMapper.SqlGetAlarmTotal());
            realTimeAlarmRes.setAlarmCaseTypeTotalList(this.baseMapper.SqlGetAlarmCaseTypeTotal());

            return realTimeAlarmRes;
        } catch (Exception e) {
            log.error(e.getMessage());
            return null;
        }

    }

    @Override
    public List<TimePeriod> SqlGetCaseTypesDayHistoryCnt(String date) {
        return this.baseMapper.SqlGetCaseTypesDayHistoryCnt(date);
    }

    @Override
    public List<TimePeriod> SqlGetCaseTypesThreeDaysHistoryCnt(String date) {
        return this.baseMapper.SqlGetCaseTypesThreeDaysHistoryCnt(date);
    }

    @Override
    public List<TimePeriod> SqlGetCaseTypesWeekHistoryCnt(String date) {
        return this.baseMapper.SqlGetCaseTypesWeekHistoryCnt(date);
    }

    @Override
    @Cacheable(value = "cache", key = "'ServiceGetHistoryCntRes'+#defer", unless = "#result==null")
    public GetHistoryCntRes ServiceGetHistoryCntRes(Integer defer) {
        GetHistoryCntRes getHistoryCntRes = new GetHistoryCntRes();
        List<TimePeriod> g1;
        List<TimePeriod> g2;
        List<TimePeriod> g3;
        LocalDateTime currentDate = LocalDateTime.now().withHour(0).withMinute(0).withSecond(0).minusDays(0);
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd");
        String time = currentDate.format(formatter);
        if (defer == 1) {
            g1 = this.getDayHistoryCnt(time);
            getHistoryCntRes.setGraph1(g1);
            g2 = this.getDayAreasHistoryCnt(time);
            getHistoryCntRes.setGraph2(g2);
            g3 = this.SqlGetCaseTypesDayHistoryCnt(time);
            getHistoryCntRes.setGraph3(g3);
            return getHistoryCntRes;
        } else if (defer == 3) {
            g1 = this.getThreeDaysHistoryCnt(time);
            getHistoryCntRes.setGraph1(g1);
            g2 = this.getThreeDaysAreasHistoryCnt(time);
            getHistoryCntRes.setGraph2(g2);
            g3 = this.SqlGetCaseTypesThreeDaysHistoryCnt(time);
            getHistoryCntRes.setGraph3(g3);
            return getHistoryCntRes;
        } else if (defer == 7) {
            g1 = this.getWeekHistoryCnt(time);
            getHistoryCntRes.setGraph1(g1);
            g2 = this.getWeekAreasHistoryCnt(time);
            getHistoryCntRes.setGraph2(g2);
            g3 = this.SqlGetCaseTypesWeekHistoryCnt(time);
            getHistoryCntRes.setGraph3(g3);
            return getHistoryCntRes;
        } else {
            return null;
        }
    }

    private List<TimePeriod> Alignment(List<String> allPeriods, List<TimePeriod> timePeriods) {
        for (String period : allPeriods) {
            boolean exists = false;
            for (TimePeriod tp : timePeriods) {
                if (tp.getPeriod().equals(period)) {
                    exists = true;
                    break;
                }
            }
            if (!exists) {
                TimePeriod newTp = new TimePeriod();
                newTp.setPeriod(period);
                newTp.setCnt(0L);
                timePeriods.add(newTp);
            }
        }
        return timePeriods;
    }

}
