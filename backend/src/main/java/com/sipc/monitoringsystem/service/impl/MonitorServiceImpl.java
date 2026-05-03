package com.sipc.monitoringsystem.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.sipc.monitoringsystem.dao.MonitorDao;
import com.sipc.monitoringsystem.model.dto.param.Monitor.CreateMonitorParam;
import com.sipc.monitoringsystem.model.dto.param.Monitor.UpdateMonitorParam;
import com.sipc.monitoringsystem.model.po.Monitor.Monitor;
import com.sipc.monitoringsystem.model.po.User.User;
import com.sipc.monitoringsystem.service.MonitorService;
import com.sipc.monitoringsystem.service.RequestFlaskService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

@Slf4j
@Service
public class MonitorServiceImpl extends ServiceImpl<MonitorDao, Monitor> implements MonitorService {

    @Autowired
    public RequestFlaskService requestFlaskService;

    @Override
    @Cacheable(value = "cache", key = "'getMonitorList'", unless = "#result==null")
    public List<Monitor> getMonitorList() {
        return this.list();
    }

    /**
     * 新增：根据用户权限获取监控列表
     * role = 0 (管理员): 返回所有监控
     * role = 1 (普通用户): 只返回 leader = userName 的监控
     * 添加了缓存，key 为 "getMonitorListByUser_" + userName
     */
    @Override
    @Cacheable(value = "cache", key = "'getMonitorListByUser_'+#user.userName", unless = "#result==null")
    public List<Monitor> getMonitorList(User user) {
        if (user.getRole() == 0) {
            // 管理员：返回所有
            return this.list();
        } else {
            // 普通用户：只返回自己负责的
            QueryWrapper<Monitor> queryWrapper = new QueryWrapper<>();
            queryWrapper.eq("leader", user.getUserName());
            return this.list(queryWrapper);
        }
    }

    @Override
    public Monitor getMonitorById(Integer id) {
        return this.getById(id);
    }

    @Override
    public Integer createMonitor(CreateMonitorParam createMonitorParam) {
        // TODO 改字段要改这里
        Monitor monitor = new Monitor();
        monitor.setName(createMonitorParam.getName());
        monitor.setArea(createMonitorParam.getArea());
        monitor.setLeader(createMonitorParam.getLeader());
        monitor.setRunning(true);
        monitor.setAlarmCnt(0);
        monitor.setFall(false);
        monitor.setFlame(false);
        monitor.setSmoke(false);
        monitor.setPunch(false);
        monitor.setRubbish(false);
        monitor.setIce(false);
        monitor.setEbike(false);
        monitor.setVehicle(false);
        monitor.setWave(false);
        monitor.setDangerArea(false);
        monitor.setStreamLink(createMonitorParam.getIp());
        monitor.setLeftX(createMonitorParam.getLeftX());
        monitor.setLeftY(createMonitorParam.getLeftY());
        monitor.setRightX(createMonitorParam.getRightX());
        monitor.setRightY(createMonitorParam.getRightY());
        try {
            save(monitor);
            return monitor.getId();

        } catch (Exception e) {
            log.error("创建监控失败");
            return -1;
        }
    }

    @Override
    public String getMonitorIPById(Integer id) {
        Monitor monitor = this.getById(id);
        return monitor.getStreamLink();
    }

    @Override
    public Boolean updateMonitor(UpdateMonitorParam updateMonitorParam) {
        // TODO 改字段要改这里
        Boolean dangerArea = updateMonitorParam.getLeftX() != null && updateMonitorParam.getLeftY() != null
                && updateMonitorParam.getRightX() != null && updateMonitorParam.getRightY() != null;

        try {
            LambdaUpdateWrapper<Monitor> updateWrapper = new LambdaUpdateWrapper<>();
            updateWrapper
                    .eq(Monitor::getId, updateMonitorParam.getId())
                    .set(Monitor::getName, updateMonitorParam.getName())
                    .set(Monitor::getArea, updateMonitorParam.getArea())
                    .set(Monitor::getLeader, updateMonitorParam.getLeader())
                    .set(Monitor::getFall, updateMonitorParam.getFall())
                    .set(Monitor::getFlame, updateMonitorParam.getFlame())
                    .set(Monitor::getSmoke, updateMonitorParam.getSmoke())
                    .set(Monitor::getPunch, updateMonitorParam.getPunch())
                    .set(Monitor::getRubbish, updateMonitorParam.getRubbish())
                    .set(Monitor::getIce, updateMonitorParam.getIce())
                    .set(Monitor::getEbike, updateMonitorParam.getEbike())
                    .set(Monitor::getVehicle, updateMonitorParam.getVehicle())
                    .set(Monitor::getWave, updateMonitorParam.getWave())
                    .set(Monitor::getDangerArea, dangerArea)
                    .set(Monitor::getLeftX, dangerArea ? updateMonitorParam.getLeftX() : null)
                    .set(Monitor::getLeftY, dangerArea ? updateMonitorParam.getLeftY() : null)
                    .set(Monitor::getRightX, dangerArea ? updateMonitorParam.getRightX() : null)
                    .set(Monitor::getRightY, dangerArea ? updateMonitorParam.getRightY() : null);
            boolean updated = update(updateWrapper);
            if (!updated) {
                return false;
            }
        } catch (Exception e) {
            log.error("更新监控数据库失败", e);
            return false;
        }

        try {
            String IP = getMonitorIPById(updateMonitorParam.getId());
            if (dangerArea) {
                List<Integer> area = new ArrayList<>();
                area.add(updateMonitorParam.getLeftX());
                area.add(updateMonitorParam.getLeftY());
                area.add(updateMonitorParam.getRightX());
                area.add(updateMonitorParam.getRightY());
                if (!requestFlaskService.updateMonitorArea(IP, area)) {
                    log.warn("同步监控区域到算法节点失败 monitorId={}, area={}", updateMonitorParam.getId(), area);
                }
            }
            List<Boolean> ability = new ArrayList<>();
            // 按照casetype表中的顺序添加：1危险区域，2烟雾/吸烟，3区域停留(暂无字段)，4摔倒，5明火，6吸烟(同烟雾)，7打架，8垃圾乱放，9冰面，10电动车进楼，11载具占用车道，12挥手
            // Flask服务已按照SQL表(case_type_info)的顺序修改，需要提供12个布尔值
            // TODO 改字段的时候要改这里
            ability.add(dangerArea); // 0: 危险区域 (caseType=1)
            ability.add(false); // 1: 烟雾 (caseType=2)
            ability.add(dangerArea); // 2: 区域停留 (caseType=3)
            ability.add(updateMonitorParam.getFall()); // 3: 摔倒 (caseType=4)
            ability.add(updateMonitorParam.getFlame()); // 4: 明火 (caseType=5)
            ability.add(updateMonitorParam.getSmoke()); // 5: 吸烟 (caseType=6)
            ability.add(updateMonitorParam.getPunch()); // 6: 打架 (caseType=7)
            ability.add(updateMonitorParam.getRubbish()); // 7: 垃圾乱放 (caseType=8)
            ability.add(updateMonitorParam.getIce()); // 8: 冰面 (caseType=9)
            ability.add(updateMonitorParam.getEbike()); // 9: 电动车进楼 (caseType=10)
            ability.add(updateMonitorParam.getVehicle()); // 10: 载具占用车道 (caseType=11)
            ability.add(updateMonitorParam.getWave()); // 11: 挥手 (caseType=12)
            if (!requestFlaskService.updateMonitorAbility(IP, ability)) {
                log.warn("同步监控能力到算法节点失败 monitorId={}, ability={}", updateMonitorParam.getId(), ability);
            }
        } catch (Exception e) {
            log.warn("同步监控配置到算法节点异常 monitorId={}", updateMonitorParam.getId(), e);
        }

        return true;
    }

    @Override
    public Boolean deleteMonitor(Integer id) {
        try {
            removeById(id);
            return true;
        } catch (Exception e) {
            log.error("删除监控失败");
            return false;
        }
    }

    @Override
    public String getMonitorImg(Integer id) {
        String ip = getMonitorIPById(id);
        try {
            return requestFlaskService.getMonitorImg(ip);
        } catch (Exception e) {
            log.error(e.getMessage());
            return null;
        }
    }

    @Override
    public Boolean switchMonitor(Integer id) {
        try {
            this.baseMapper.MonitorRunningSwitch(id);
            return true;
        } catch (Exception e) {
            log.error("切换监控失败");
            return false;
        }
    }

    @Override
    public Boolean updateLeaders(String oldName, String newName) {
        LambdaUpdateWrapper<Monitor> updateWrapper = new LambdaUpdateWrapper<>();
        updateWrapper.eq(Monitor::getLeader, oldName)
                .set(Monitor::getLeader, newName);
        try {
            update(updateWrapper);
            return true;
        } catch (Exception e) {
            log.error("更新监控失败");
            return false;
        }

    }
}
