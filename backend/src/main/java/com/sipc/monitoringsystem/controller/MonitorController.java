package com.sipc.monitoringsystem.controller;

import com.sipc.monitoringsystem.aop.ClearRedis;
import com.sipc.monitoringsystem.aop.Pass;
import com.sipc.monitoringsystem.model.dto.CommonResult;
import com.sipc.monitoringsystem.model.dto.param.Monitor.CreateMonitorParam;
import com.sipc.monitoringsystem.model.dto.param.Monitor.UpdateMonitorParam;
import com.sipc.monitoringsystem.model.dto.res.BlankRes;
import com.sipc.monitoringsystem.model.dto.res.Monitor.CreateMonitorRes;
import com.sipc.monitoringsystem.model.dto.res.Monitor.GetMonitorsPosRes;
import com.sipc.monitoringsystem.model.dto.res.Monitor.GetMonitorListRes;
import com.sipc.monitoringsystem.model.po.Monitor.Monitor;
import com.sipc.monitoringsystem.model.po.User.User;
import com.sipc.monitoringsystem.service.MonitorService;
import com.sipc.monitoringsystem.service.UserService;
import com.sipc.monitoringsystem.util.JwtUtils;
import com.sipc.monitoringsystem.util.TokenThreadLocalUtil;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotNull;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.ResponseEntity;
import org.springframework.beans.factory.annotation.Value;

/**
 * @author CZCZCZ
 *         &#064;date 2023-10-01 20:50
 */

@Slf4j
@RestController
@CrossOrigin
@RequestMapping("/api/v1/monitor")
public class MonitorController {
    @Autowired
    MonitorService monitorService;

    @Autowired
    UserService userService;

    @Value("${agent.api.url:http://localhost:5000}")
    private String agentApiUrl;

    private final RestTemplate restTemplate = new RestTemplate();

    @GetMapping()
    public CommonResult<List<GetMonitorListRes>> getMonitorList() {
        // 从 Token 获取当前用户信息
        User tokenUser = JwtUtils.getUserByToken(TokenThreadLocalUtil.getInstance().getToken());
        User user = userService.getById(tokenUser.getId());
        if (user == null) {
            user = tokenUser;
        }

        // 根据用户权限获取监控列表
        List<Monitor> sqlMonitors = monitorService.getMonitorList(user);
        if (sqlMonitors == null) {
            return CommonResult.fail("获取监控列表失败");
        }
        System.out.println(sqlMonitors);
        List<GetMonitorListRes> getMonitorListResList = new ArrayList<>();
        for (Monitor monitor : sqlMonitors) {
            GetMonitorListRes getMonitorListRes = new GetMonitorListRes(monitor);
            getMonitorListResList.add(getMonitorListRes);
        }

        return CommonResult.success(getMonitorListResList);
    }

    @GetMapping("/map")
    public CommonResult<GetMonitorsPosRes> getMonitorsPos() {
        List<Monitor> sqlMonitors = monitorService.getMonitorList();
        if (sqlMonitors == null) {
            return CommonResult.fail("获取监控列表失败");
        }
        GetMonitorsPosRes getMonitorsPosRes = new GetMonitorsPosRes(sqlMonitors);

        return CommonResult.success(getMonitorsPosRes);
    }

    @GetMapping("/flask/info")
    public CommonResult<Monitor> getMonitor() {
        Monitor monitor = JwtUtils.getMonitorByToken(TokenThreadLocalUtil.getInstance().getToken());
        monitor = monitorService.getMonitorById(monitor.getId());
        if (monitor == null) {
            return CommonResult.fail("token错误");
        }

        return CommonResult.success(monitor);
    }

    @PostMapping("/update")
    @ClearRedis
    public CommonResult<BlankRes> updateMonitor(@Valid @RequestBody UpdateMonitorParam updateMonitorParam) {
        if (!monitorService.updateMonitor(updateMonitorParam)) {
            return CommonResult.fail("更新失败");
        }
        return CommonResult.success("更新成功");
    }

    @PostMapping("/flask/create")
    @Pass
    @ClearRedis
    public CommonResult<CreateMonitorRes> createMonitor(@Valid @RequestBody CreateMonitorParam createMonitorParam) {
        CreateMonitorRes createMonitorRes = new CreateMonitorRes();
        Integer id = monitorService.createMonitor(createMonitorParam);
        if (id == -1) {
            return CommonResult.fail("创建失败");
        }
        createMonitorRes.setId(id);
        createMonitorRes.setToken(JwtUtils.signMonitor(id));

        return CommonResult.success(createMonitorRes);
    }

    @GetMapping("/image/{monitorId}")
    public CommonResult<String> getMonitorImg(@PathVariable @NotNull Integer monitorId) {
        String img = monitorService.getMonitorImg(monitorId);
        if (img == null) {
            return CommonResult.fail("获取图片失败");
        }
        return CommonResult.success(img);
    }

    @PostMapping("/switch/{id}")
    @ClearRedis
    public CommonResult<BlankRes> switchMonitor(@PathVariable @NotNull Integer id) {
        if (!monitorService.switchMonitor(id)) {
            return CommonResult.fail("开启或关闭失败");
        }
        return CommonResult.success("开启或关闭成功");
    }

    @PostMapping("/update_prompt")
    public CommonResult<?> updatePrompt(@RequestBody Map<String, Object> body) {
        try {
            // 将前端发来的包含中文的 prompts 透传给 Python 算法端进行翻译和动态加载
            String targetUrl = agentApiUrl + "/api/v1/monitor-device/update_prompt";
            ResponseEntity<Map> response = restTemplate.postForEntity(targetUrl, body, Map.class);
            Map respBody = response.getBody();
            if (respBody != null && "00000".equals(respBody.get("code"))) {
                return CommonResult.success(respBody.get("translated"));
            } else {
                return CommonResult.fail("Python 端返回更新失败");
            }
        } catch (Exception e) {
            log.error("Failed to proxy update_prompt to python agent", e);
            return CommonResult.fail("转发请求到视觉算力节点失败");
        }
    }
}
