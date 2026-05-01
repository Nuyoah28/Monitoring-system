package com.sipc.monitoringsystem.controller;

import com.alibaba.excel.EasyExcel;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.sipc.monitoringsystem.aop.ClearRedis;
import com.sipc.monitoringsystem.aop.Pass;
import com.sipc.monitoringsystem.model.dto.CommonResult;
import com.sipc.monitoringsystem.model.dto.param.alarm.UpdateAlarmParam;
import com.sipc.monitoringsystem.model.dto.res.Alarm.*;
import com.sipc.monitoringsystem.model.dto.res.BlankRes;
import com.sipc.monitoringsystem.model.po.Alarm.Alarm;
import com.sipc.monitoringsystem.model.po.Message.SystemMessage;
import com.sipc.monitoringsystem.model.po.Alarm.SqlGetAlarm;
import com.sipc.monitoringsystem.model.po.User.User;
import com.sipc.monitoringsystem.service.AlarmPushRecordService;
import com.sipc.monitoringsystem.service.AlarmService;
import com.sipc.monitoringsystem.service.SystemMessageService;
import com.sipc.monitoringsystem.util.HttpUtils;
import com.sipc.monitoringsystem.util.JwtUtils;
import com.sipc.monitoringsystem.util.TokenThreadLocalUtil;
import com.sipc.monitoringsystem.websocket.AlarmWebSocketServer;
import com.sipc.monitoringsystem.service.UserService;
import com.sipc.monitoringsystem.service.MonitorService;
import com.sipc.monitoringsystem.model.po.Monitor.Monitor;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotNull;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.io.File;
import java.nio.file.Files;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;

@Validated
@Slf4j
@RestController
@CrossOrigin
@RequestMapping("/api/v1/alarm")

/*
 * TODO
 * 报警记录假设有10000条才占4MB，不至于使用数据库分页查询
 * 而且实时性不高，这个报警推送采用的应该是前端轮询的方式，
 * 应该使用websocket的publish/subscribe模式
 * 这里除了receive之外全改
 */
public class AlarmController {

    @Autowired
    AlarmService alarmService;

    @Autowired
    UserService userService;

    @Autowired
    MonitorService monitorService;

    @Autowired
    SystemMessageService systemMessageService;

    @Autowired
    AlarmPushRecordService alarmPushRecordService;

    @PostMapping("/receive")
    @ClearRedis
    @Pass
    public CommonResult<BlankRes> receiveAlarm(@RequestParam(value = "cameraId", required = true) Integer cameraId,
            @RequestParam(value = "caseType", required = true) Integer caseType,
            @RequestParam(value = "clipId", required = true) String clipId,
            @RequestParam(value = "occurredAt", required = false) String occurredAt) {

        boolean duplicateAlarm = alarmService.getOne(new QueryWrapper<Alarm>()
                .eq("monitor_id", cameraId)
                .eq("case_type", caseType)
                .eq("clip_link", clipId)
                .last("LIMIT 1")) != null;

        // 1. 保存报警到数据库
        SqlGetAlarm alarm = alarmService.receiveAlarm(cameraId, caseType, clipId, occurredAt);

        if (alarm == null) {
            return CommonResult.fail("接收失败");
        }
        if (duplicateAlarm) {
            log.info("重复报警补传已忽略推送: cameraId={}, caseType={}, clipId={}", cameraId, caseType, clipId);
            return CommonResult.success("重复报警已确认");
        }

        GetAlarmRes alarmRes = new GetAlarmRes(alarm);
        Monitor monitor = monitorService.getMonitorById(cameraId);

        // 2. 定向推送给负责人和管理员（现有流程）
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

        // 3. 同区域居民推送（新增）
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

        log.info("报警推送完成: cameraId={}, caseType={}, managerTargets={}, residentTargets={}",
                cameraId, caseType, managerIds.size(), residentIds.size());

        // 4. 同时发送 UniPush 手机推送通知（按需启用）
        // sendUniPushNotification();

        return CommonResult.success("接收成功");
    }

    /**
     * 发送 UniPush 手机推送通知（原有逻辑抽取）
     */
    private void sendUniPushNotification() {
        Map<String, String> paramMap = new HashMap<>();
        paramMap.put("cid", ""); // cid不填默认全发
        paramMap.put("title", "报警通知");
        paramMap.put("content",
                "您有一条新的报警信息，请及时处理" + LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")));
        Map<String, String> optMap = new HashMap<>();
        Map<String, String> catMap = new HashMap<>();
        catMap.put("/message/android/category", "WORK");
        optMap.put("HW", catMap.toString());
        Map<String, Object> dateMap = new HashMap<>();
        dateMap.put("date1", 1);
        dateMap.put("date2", 1);
        paramMap.put("options", optMap.toString());
        paramMap.put("date", dateMap.toString());
        Random random = new Random();
        String randomString = random.ints(10, 0, 10)
                .mapToObj(Integer::toString)
                .collect(Collectors.joining());
        paramMap.put("request_id", randomString);
        try {
            String resJson = HttpUtils.postJson(
                    "https://fc-mp-e0386718-0219-4138-80a9-902540e76f67.next.bspapp.com/notice",
                    new ObjectMapper().writeValueAsString(paramMap));
            if (resJson.contains("success")) {
                log.info("发送 UniPush 报警通知成功");
            } else {
                log.error("发送 UniPush 报警通知失败");
            }
        } catch (JsonProcessingException e) {
            log.error("发送 UniPush 报警通知失败", e);
        }
    }

    @GetMapping("/{alarmId}")
    @Pass
    public CommonResult<GetAlarmRes> getAlarm(@PathVariable @NotNull(message = "alarmId不能为空") Integer alarmId) {
        SqlGetAlarm alarm = alarmService.getAlarm(alarmId);
        if (alarm == null)
            return CommonResult.fail("查询失败");

        return CommonResult.success(new GetAlarmRes(alarm));
    }

    @GetMapping("/query/cnt")
    @Pass
    public CommonResult<BlankRes> getAlarmCnt(@RequestParam(value = "caseType", required = false) Integer caseType,
            @RequestParam(value = "time1", required = false) String time1,
            @RequestParam(value = "time2", required = false) String time2) {
        Long alarmCnt = alarmService.getAlarmCnt(caseType, time1, time2);
        if (alarmCnt == null)
            return CommonResult.fail("查询失败");
        else
            return CommonResult.success(alarmCnt.toString());
    }

    @GetMapping("/query/cnt/history")
    @Pass
    public CommonResult<GetHistoryCntRes> getHistoryCnt(@RequestParam(value = "defer") Integer defer) {
        GetHistoryCntRes getHistoryCntRes = alarmService.ServiceGetHistoryCntRes(defer);
        if (getHistoryCntRes == null)
            return CommonResult.fail("查询失败");
        else
            return CommonResult.success(getHistoryCntRes);
    }

    @GetMapping("/query/cnt/type-area")
    @Pass
    public CommonResult<GetTypeAreaHeatRes> getTypeAreaHeat(@RequestParam(value = "defer") Integer defer) {
        GetTypeAreaHeatRes heatRes = alarmService.getTypeAreaHeat(defer);
        if (heatRes == null)
            return CommonResult.fail("查询失败");
        else
            return CommonResult.success(heatRes);
    }

    @GetMapping("/query")
    public CommonResult<QueryAlarmListRes> queryAlarmList(
            @RequestParam(value = "pageNum", required = true) Integer pageNum,
            @RequestParam(value = "pageSize", required = true) Integer pageSize,
            @RequestParam(value = "caseType", required = false) Integer caseType,
            @RequestParam(value = "status", required = false) Integer status,
            @RequestParam(value = "warningLevel", required = false) Integer warningLevel,
            @RequestParam(value = "time1", required = false) String time1,
            @RequestParam(value = "time2", required = false) String time2) {

        // 从 Token 获取当前用户信息基础信息 (此时只包含id和role)
        User tokenUser = JwtUtils.getUserByToken(TokenThreadLocalUtil.getInstance().getToken());

        // 🚨根据id从数据库获取完整的用户信息，因为token里没有userName，而鉴权过滤强依赖 userName
        User user = userService.getById(tokenUser.getId());
        if (user == null) {
            user = tokenUser; // fallback
        }

        // 根据用户权限获取报警列表
        List<SqlGetAlarm> alarmList = alarmService.queryAlarmList(pageNum, pageSize, caseType, status, warningLevel,
                time1, time2, user);

        if (alarmList == null)
            return CommonResult.fail("查询失败");

        List<GetAlarmRes> res = new ArrayList<>();

        for (SqlGetAlarm alarm : alarmList) {
            res.add(new GetAlarmRes(alarm));
        }
        QueryAlarmListRes queryAlarmListRes = new QueryAlarmListRes();
        queryAlarmListRes.setCount(res.size());
        queryAlarmListRes.setAlarmList(res);
        return CommonResult.success(queryAlarmListRes);
    }

    @PutMapping("/update")
    @ClearRedis
    @Pass
    public CommonResult<BlankRes> updateAlarm(@Valid @RequestBody UpdateAlarmParam updateAlarmParam) {
        if (alarmService.updateAlarm(updateAlarmParam.getId(), updateAlarmParam.getStatus(),
                updateAlarmParam.getProcessingContent()))
            return CommonResult.success("更新成功");
        else
            return CommonResult.fail("更新失败");
    }

    @DeleteMapping("/{alarmId}")
    @ClearRedis
    @Pass
    public CommonResult<BlankRes> deleteAlarm(@PathVariable @NotNull(message = "alarmId不能为空") Integer alarmId) {
        if (alarmService.deleteAlarm(alarmId))
            return CommonResult.success("删除成功");
        else
            return CommonResult.fail("删除失败");
    }

    @GetMapping("/realtime")
    @Pass
    public CommonResult<RealTimeAlarmRes> getRealTimeAlarm() {
        RealTimeAlarmRes realTimeAlarmRes = alarmService.getRealTimeAlarmRes();
        if (realTimeAlarmRes == null)
            return CommonResult.fail("查询失败");
        else
            return CommonResult.success(realTimeAlarmRes);
    }

    @GetMapping("/export")
    @Pass
    public ResponseEntity<byte[]> exportAlarms() {
        String Filename = "temp.xlsx";
        File file = new File(Filename);
        EasyExcel.write(Filename, GetAlarmRes.class)
                .sheet("报警数据")
                .doWrite(() -> {
                    List<SqlGetAlarm> alarmRes = alarmService.queryAlarmList(1, 5000, null, null, null, null, null);
                    List<GetAlarmRes> res = new ArrayList<>();
                    for (SqlGetAlarm alarmRe : alarmRes) {
                        res.add(new GetAlarmRes(alarmRe));
                    }
                    return res;
                });
        byte[] bytes = null;
        try {
            bytes = Files.readAllBytes(file.toPath());
        } catch (Exception e) {
            log.error("文件读取失败");
            return null;
        }
        return ResponseEntity.ok().body(bytes);
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
