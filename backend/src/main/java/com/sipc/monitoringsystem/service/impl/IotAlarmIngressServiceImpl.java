package com.sipc.monitoringsystem.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.sipc.monitoringsystem.aop.ClearRedisImpl;
import com.sipc.monitoringsystem.model.dto.res.Alarm.GetAlarmRes;
import com.sipc.monitoringsystem.model.po.Alarm.Alarm;
import com.sipc.monitoringsystem.model.po.Alarm.SqlGetAlarm;
import com.sipc.monitoringsystem.model.po.Message.SystemMessage;
import com.sipc.monitoringsystem.model.po.Monitor.Monitor;
import com.sipc.monitoringsystem.model.po.User.User;
import com.sipc.monitoringsystem.service.AlarmPushRecordService;
import com.sipc.monitoringsystem.service.AlarmService;
import com.sipc.monitoringsystem.service.IotAlarmIngressService;
import com.sipc.monitoringsystem.service.MonitorService;
import com.sipc.monitoringsystem.service.SystemMessageService;
import com.sipc.monitoringsystem.service.UserService;
import com.sipc.monitoringsystem.websocket.AlarmWebSocketServer;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

@Service
@Slf4j
@RequiredArgsConstructor
public class IotAlarmIngressServiceImpl implements IotAlarmIngressService {

    private final AlarmService alarmService;
    private final UserService userService;
    private final MonitorService monitorService;
    private final SystemMessageService systemMessageService;
    private final AlarmPushRecordService alarmPushRecordService;
    private final ClearRedisImpl clearRedisImpl;

    @Override
    public SqlGetAlarm receiveAndDispatchAlarm(Integer cameraId, Integer caseType, String clipId, String occurredAt) {
        clearRedisImpl.deleteCache();

        boolean duplicateAlarm = alarmService.getOne(new QueryWrapper<Alarm>()
                .eq("monitor_id", cameraId)
                .eq("case_type", caseType)
                .eq("clip_link", clipId)
                .last("LIMIT 1")) != null;

        SqlGetAlarm alarm = alarmService.receiveAlarm(cameraId, caseType, clipId, occurredAt);
        if (alarm == null) {
            return null;
        }
        if (duplicateAlarm) {
            log.info("Duplicate alarm ignored for push: cameraId={}, caseType={}, clipId={}",
                    cameraId, caseType, clipId);
            return alarm;
        }

        GetAlarmRes alarmRes = new GetAlarmRes(alarm);
        Monitor monitor = monitorService.getMonitorById(cameraId);

        Map<String, Object> managerSocketMessage = new HashMap<>();
        managerSocketMessage.put("type", "NEW_ALARM");
        managerSocketMessage.put("message", "您有一条新的报警信息，请及时处理");
        managerSocketMessage.put("data", alarmRes);

        Set<Integer> managerIds = collectManagerTargets(monitor);
        if (!managerIds.isEmpty()) {
            AlarmWebSocketServer.sendToUsers(
                    managerIds.stream().map(String::valueOf).collect(Collectors.toList()),
                    managerSocketMessage);
            for (Integer userId : managerIds) {
                alarmPushRecordService.saveRecord(alarm.getId(), userId, "ws", "success", "manager_or_admin");
            }
        }

        Set<Integer> residentIds = collectResidentTargets(monitor);
        if (!residentIds.isEmpty()) {
            Map<String, Object> residentSocketMessage = new HashMap<>();
            residentSocketMessage.put("type", "NEW_ALARM");
            residentSocketMessage.put("message", buildResidentMessage(alarm, monitor));
            residentSocketMessage.put("data", alarmRes);

            AlarmWebSocketServer.sendToUsers(
                    residentIds.stream().map(String::valueOf).collect(Collectors.toList()),
                    residentSocketMessage);

            for (Integer residentId : residentIds) {
                SystemMessage residentNotice = new SystemMessage();
                residentNotice.setReceiverUserId(residentId);
                residentNotice.setMessage(buildResidentMessage(alarm, monitor));
                systemMessageService.addMessage(residentNotice);
                alarmPushRecordService.saveRecord(alarm.getId(), residentId, "ws", "success", "resident_by_area");
                alarmPushRecordService.saveRecord(alarm.getId(), residentId, "system_message", "success",
                        "resident_by_area");
            }
        }

        log.info("Alarm dispatch completed: cameraId={}, caseType={}, managerTargets={}, residentTargets={}",
                cameraId, caseType, managerIds.size(), residentIds.size());
        return alarm;
    }

    private Set<Integer> collectManagerTargets(Monitor monitor) {
        Set<Integer> targetIds = new LinkedHashSet<>();
        if (monitor != null && monitor.getLeader() != null) {
            User leaderUser = userService.getOne(new QueryWrapper<User>().eq("user_name", monitor.getLeader()));
            if (leaderUser != null) {
                targetIds.add(leaderUser.getId());
            }
        }
        List<User> admins = userService.list(new QueryWrapper<User>().eq("role", 0));
        for (User admin : admins) {
            targetIds.add(admin.getId());
        }
        return targetIds;
    }

    private Set<Integer> collectResidentTargets(Monitor monitor) {
        Set<Integer> targetIds = new LinkedHashSet<>();
        if (monitor == null || monitor.getArea() == null || monitor.getArea().isBlank()) {
            return targetIds;
        }
        List<User> residents = userService.list(new QueryWrapper<User>()
                .eq("is_resident", 1)
                .eq("notify_enabled", 1)
                .eq("home_area", monitor.getArea()));
        for (User resident : residents) {
            targetIds.add(resident.getId());
        }
        return targetIds;
    }

    private String buildResidentMessage(SqlGetAlarm alarm, Monitor monitor) {
        String area = monitor == null || monitor.getArea() == null ? "附近区域" : monitor.getArea();
        String caseName = alarm.getCaseTypeName() == null ? "异常事件" : alarm.getCaseTypeName();
        return "【" + area + "】发生" + caseName + "，请注意安全并留意物业通知。";
    }
}
