package com.sipc.monitoringsystem.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.sipc.monitoringsystem.dao.DeviceRepairDao;
import com.sipc.monitoringsystem.model.po.User.User;
import com.sipc.monitoringsystem.model.po.DeviceRepair.DeviceRepairInfo;
import com.sipc.monitoringsystem.service.DeviceRepairService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;

@Slf4j
@Service
public class DeviceRepairServiceImpl extends ServiceImpl<DeviceRepairDao, DeviceRepairInfo> implements DeviceRepairService {

    @Override
    public List<DeviceRepairInfo> listAll(User currentUser) {
        if (currentUser != null && Integer.valueOf(1).equals(currentUser.getRole())) {
            return this.list(new com.baomidou.mybatisplus.core.conditions.query.QueryWrapper<DeviceRepairInfo>()
                    .eq("owner_user_id", currentUser.getId())
                    .orderByDesc("report_time")
                    .orderByDesc("id"));
        }
        return this.list(new com.baomidou.mybatisplus.core.conditions.query.QueryWrapper<DeviceRepairInfo>()
                .orderByDesc("report_time")
                .orderByDesc("id"));
    }

    @Override
    public DeviceRepairInfo getById(Integer id, User currentUser) {
        DeviceRepairInfo info = this.baseMapper.selectById(id);
        if (info == null) {
            return null;
        }
        if (currentUser != null && Integer.valueOf(1).equals(currentUser.getRole())) {
            return currentUser.getId().equals(info.getOwnerUserId()) ? info : null;
        }
        return info;
    }

    @Override
    public Integer create(DeviceRepairInfo info, User currentUser) {
        try {
            if (info != null && currentUser != null) {
                info.setOwnerUserId(currentUser.getId());
                if (info.getPublisher() == null || info.getPublisher().trim().isEmpty()) {
                    info.setPublisher(currentUser.getUserName());
                }
            }
            this.save(info);
            return info.getId();
        } catch (Exception e) {
            log.error("创建设备报修失败", e);
            return -1;
        }
    }

    @Override
    public boolean update(DeviceRepairInfo info, User currentUser) {
        try {
            if (currentUser != null && Integer.valueOf(1).equals(currentUser.getRole())) {
                DeviceRepairInfo existing = this.baseMapper.selectById(info.getId());
                if (existing == null || !currentUser.getId().equals(existing.getOwnerUserId())) {
                    return false;
                }
                info.setOwnerUserId(existing.getOwnerUserId());
                if (info.getPublisher() == null || info.getPublisher().trim().isEmpty()) {
                    info.setPublisher(existing.getPublisher());
                }
            }
            return this.updateById(info);
        } catch (Exception e) {
            log.error("更新设备报修失败", e);
            return false;
        }
    }

    @Override
    public boolean delete(Integer id, User currentUser) {
        try {
            if (currentUser != null && Integer.valueOf(1).equals(currentUser.getRole())) {
                DeviceRepairInfo existing = this.baseMapper.selectById(id);
                if (existing == null || !currentUser.getId().equals(existing.getOwnerUserId())) {
                    return false;
                }
            }
            return this.removeById(id);
        } catch (Exception e) {
            log.error("删除设备报修失败", e);
            return false;
        }
    }
}
