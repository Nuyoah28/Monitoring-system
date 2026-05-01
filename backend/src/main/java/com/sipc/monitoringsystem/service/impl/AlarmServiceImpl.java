package com.sipc.monitoringsystem.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.sipc.monitoringsystem.dao.AlarmDao;
import com.sipc.monitoringsystem.model.dto.CommonResult;
import com.sipc.monitoringsystem.model.dto.res.Alarm.GetHistoryCntRes;
import com.sipc.monitoringsystem.model.dto.res.Alarm.GetTypeAreaHeatRes;
import com.sipc.monitoringsystem.model.dto.res.Alarm.RealTimeAlarmRes;
import com.sipc.monitoringsystem.model.po.Alarm.AlarmTypeAreaCount;
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
import java.sql.Timestamp;
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
    public SqlGetAlarm receiveAlarm(Integer cameraID, Integer caseType, String clipLink) {
        return receiveAlarm(cameraID, caseType, clipLink, null);
    }

    @Override
    public SqlGetAlarm receiveAlarm(Integer cameraID, Integer caseType, String clipLink, String occurredAt) {
        log.info("receive alarm from camera: " + cameraID + " caseType: " + caseType);
        Alarm existedAlarm = this.baseMapper.selectOne(
                new QueryWrapper<Alarm>()
                        .eq("monitor_id", cameraID)
                        .eq("case_type", caseType)
                        .eq("clip_link", clipLink)
                        .last("LIMIT 1"));
        if (existedAlarm != null) {
            return this.baseMapper.SqlGetAlarm(existedAlarm.getId());
        }

        Alarm alarm = new Alarm();
        alarm.setClipLink(clipLink);
        alarm.setCaseType(caseType);
        alarm.setMonitorId(cameraID);
        alarm.setWarningLevel(1);
        alarm.setStatus(false);
        Timestamp occurredTime = parseOccurredAt(occurredAt);
        if (occurredTime != null) {
            alarm.setCreateTime(occurredTime);
        }
        this.save(alarm);
        monitorServiceImpl.getBaseMapper().MonitorAlarmCntPlusOne(cameraID);
        // 获取数据库中的sqlalarm,找id最大且监控id对的上的
        Alarm latestAlarm = this.baseMapper.selectOne(
                new QueryWrapper<Alarm>()
                        .eq("monitor_id", cameraID)
                        .orderByDesc("id")
                        .last("LIMIT 1"));
        if (latestAlarm == null) {
            throw new RuntimeException("Failed to retrieve the saved alarm record");
        }
        return this.baseMapper.SqlGetAlarm(latestAlarm.getId());
    }

    private Timestamp parseOccurredAt(String occurredAt) {
        if (occurredAt == null || occurredAt.isBlank()) {
            return null;
        }
        try {
            return Timestamp.valueOf(occurredAt.trim());
        } catch (IllegalArgumentException e) {
            log.warn("invalid alarm occurredAt: {}", occurredAt);
            return null;
        }
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

        // 获取用户负责的监控ID列表（如果是管理员则为空集或全集，这里我们通过动态判断过滤）
        Set<Integer> userMonitorIds = new HashSet<>();
        if (user.getRole() != 0) {
            List<Monitor> userMonitors = monitorServiceImpl.getMonitorList(user);
            userMonitorIds = userMonitors.stream()
                    .map(Monitor::getId)
                    .collect(Collectors.toSet());
        }

        final Set<Integer> finalMonitorIds = userMonitorIds;

        // 组合过滤所有条件
        alarms = alarms.stream()
                .filter(alarm -> {
                    // 1. 用户权限过滤
                    if (user.getRole() != 0 && !finalMonitorIds.contains(alarm.getMonitorId()))
                        return false;
                    // 2. 状态过滤
                    if (status != null) {
                        boolean alarmStatus = alarm.getStatus() != null && alarm.getStatus();
                        boolean targetStatus = status == 1; // 假设 1=已处理, 0=未处理
                        if (alarmStatus != targetStatus)
                            return false;
                    }
                    // 3. 告警类型过滤
                    if (caseType != null && !caseType.equals(alarm.getCaseType()))
                        return false;
                    // 4. 警报等级过滤
                    if (warningLevel != null && !warningLevel.equals(alarm.getWarningLevel()))
                        return false;

                    return true;
                })
                .collect(Collectors.toList());

        // 执行内存分页
        int total = alarms.size();
        int fromIndex = (pageNum - 1) * pageSize;
        if (fromIndex >= total || fromIndex < 0) {
            alarms = new ArrayList<>();
        } else {
            int toIndex = Math.min(fromIndex + pageSize, total);
            alarms = alarms.subList(fromIndex, toIndex);
        }

        for (SqlGetAlarm alarm : alarms) {
            alarm.setClipLink(ossUtil.getClipLinkByUuid(alarm.getClipLink()));
        }

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

    // ========== 近一个月 (30天) ==========

    @Override
    public List<TimePeriod> getMonthHistoryCnt(String date) {
        List<String> allPeriods = new ArrayList<>();
        Calendar calendar = Calendar.getInstance();
        calendar.setTime(new Date());
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");
        for (int i = 0; i < 30; i++) {
            allPeriods.add(sdf.format(calendar.getTime()));
            calendar.add(Calendar.DAY_OF_YEAR, -1);
        }
        List<TimePeriod> timePeriods = this.baseMapper.SqlGetMonthHistoryCnt(date);
        Alignment(allPeriods, timePeriods);
        // 只保留月份和日期
        for (TimePeriod tp : timePeriods) {
            tp.setPeriod(tp.getPeriod().substring(5));
        }
        return timePeriods;
    }

    @Override
    public List<TimePeriod> getMonthAreasHistoryCnt(String date) {
        return this.baseMapper.SqlGetAreasMonthHistoryCnt(date);
    }

    @Override
    public List<TimePeriod> SqlGetCaseTypesMonthHistoryCnt(String date) {
        return this.baseMapper.SqlGetCaseTypesMonthHistoryCnt(date);
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
        } else if (defer == 30) {
            g1 = this.getMonthHistoryCnt(time);
            getHistoryCntRes.setGraph1(g1);
            g2 = this.getMonthAreasHistoryCnt(time);
            getHistoryCntRes.setGraph2(g2);
            g3 = this.SqlGetCaseTypesMonthHistoryCnt(time);
            getHistoryCntRes.setGraph3(g3);
            return getHistoryCntRes;
        } else {
            return null;
        }
    }

    @Override
    public GetTypeAreaHeatRes getTypeAreaHeat(Integer defer) {
        if (defer == null || !(defer == 1 || defer == 3 || defer == 7 || defer == 30)) {
            return null;
        }

        LocalDateTime endDateTime = LocalDateTime.now().withHour(0).withMinute(0).withSecond(0).withNano(0).plusDays(1);
        LocalDateTime startDateTime = defer == 1
                ? endDateTime.minusDays(1)
                : endDateTime.minusDays(defer);
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
        List<AlarmTypeAreaCount> source = this.baseMapper.SqlGetTypeAreaHeat(
                startDateTime.format(formatter),
                endDateTime.format(formatter));

        Map<String, Long> typeTotals = new HashMap<>();
        Map<String, Long> areaTotals = new HashMap<>();
        Map<String, Map<String, Long>> matrix = new HashMap<>();
        Long total = 0L;
        Long maxCount = 0L;

        for (AlarmTypeAreaCount item : source) {
            String area = normalizeHeatName(item.getArea(), "未标注区域");
            String type = normalizeHeatName(item.getCaseTypeName(), "未知事件");
            Long count = item.getCnt() == null ? 0L : item.getCnt();
            total += count;
            maxCount = Math.max(maxCount, count);
            typeTotals.put(type, typeTotals.getOrDefault(type, 0L) + count);
            areaTotals.put(area, areaTotals.getOrDefault(area, 0L) + count);
            matrix.computeIfAbsent(area, key -> new HashMap<>()).put(type, count);
        }

        List<GetTypeAreaHeatRes.RankItem> byType = buildRankItems(typeTotals, 8);
        List<GetTypeAreaHeatRes.RankItem> byArea = buildRankItems(areaTotals, 8);
        List<String> topTypes = byType.stream().limit(4).map(GetTypeAreaHeatRes.RankItem::getName)
                .collect(Collectors.toList());
        List<String> topAreas = byArea.stream().limit(4).map(GetTypeAreaHeatRes.RankItem::getName)
                .collect(Collectors.toList());

        List<GetTypeAreaHeatRes.HeatRow> rows = new ArrayList<>();
        for (String area : topAreas) {
            Map<String, Long> values = new LinkedHashMap<>();
            for (String type : topTypes) {
                values.put(type, matrix.getOrDefault(area, Collections.emptyMap()).getOrDefault(type, 0L));
            }
            rows.add(new GetTypeAreaHeatRes.HeatRow(area, values));
        }

        GetTypeAreaHeatRes res = new GetTypeAreaHeatRes();
        res.setDefer(defer);
        res.setRangeLabel(buildHeatRangeLabel(defer));
        res.setTotal(total);
        res.setByType(byType);
        res.setByArea(byArea);
        res.setTypes(topTypes);
        res.setRows(rows);
        res.setMaxCount(maxCount);
        return res;
    }

    private List<GetTypeAreaHeatRes.RankItem> buildRankItems(Map<String, Long> source, Integer limit) {
        return source.entrySet().stream()
                .sorted((a, b) -> {
                    int countCompare = Long.compare(b.getValue(), a.getValue());
                    if (countCompare != 0) {
                        return countCompare;
                    }
                    return a.getKey().compareTo(b.getKey());
                })
                .limit(limit)
                .map(entry -> new GetTypeAreaHeatRes.RankItem(entry.getKey(), entry.getValue()))
                .collect(Collectors.toList());
    }

    private String normalizeHeatName(String value, String fallback) {
        if (value == null || value.trim().isEmpty()) {
            return fallback;
        }
        return value.trim();
    }

    private String buildHeatRangeLabel(Integer defer) {
        if (defer == 1) {
            return "今日";
        }
        if (defer == 3) {
            return "近3天";
        }
        if (defer == 7) {
            return "近7天";
        }
        if (defer == 30) {
            return "近30天";
        }
        return "统计周期";
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
