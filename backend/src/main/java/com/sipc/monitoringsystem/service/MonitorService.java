package com.sipc.monitoringsystem.service;

import com.sipc.monitoringsystem.model.dto.param.Monitor.CreateMonitorParam;
import com.sipc.monitoringsystem.model.dto.param.Monitor.UpdateMonitorParam;
import com.sipc.monitoringsystem.model.po.Monitor.Monitor;
import com.sipc.monitoringsystem.model.po.User.User;

import java.util.List;

public interface MonitorService {
    List<Monitor> getMonitorList();

    // 新增：根据用户权限获取监控列表
    List<Monitor> getMonitorList(User user);

    Monitor getMonitorById(Integer id);

    Integer createMonitor(CreateMonitorParam createMonitorParam);

    Boolean updateMonitor(UpdateMonitorParam updateMonitorParam);

    String getMonitorIPById(Integer id);

    String getMonitorImg(Integer id);

    Boolean switchMonitor(Integer id);

    Boolean updateLeaders(String oldName, String newName);

    Boolean deleteMonitor(Integer id);
}
