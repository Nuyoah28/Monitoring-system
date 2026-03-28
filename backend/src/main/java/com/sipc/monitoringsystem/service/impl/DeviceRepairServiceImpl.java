package com.sipc.monitoringsystem.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.sipc.monitoringsystem.dao.DeviceRepairDao;
import com.sipc.monitoringsystem.model.po.DeviceRepair.DeviceRepairInfo;
import com.sipc.monitoringsystem.service.DeviceRepairService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;

@Slf4j
@Service
public class DeviceRepairServiceImpl extends ServiceImpl<DeviceRepairDao, DeviceRepairInfo> implements DeviceRepairService {

    @Override
    public List<DeviceRepairInfo> listAll() {
        return this.list();
    }

    @Override
    public DeviceRepairInfo getById(Integer id) {
        return this.baseMapper.selectById(id);
    }

    @Override
    public Integer create(DeviceRepairInfo info) {
        try {
            this.save(info);
            return info.getId();
        } catch (Exception e) {
            log.error("创建设备报修失败", e);
            return -1;
        }
    }

    @Override
    public boolean update(DeviceRepairInfo info) {
        try {
            return this.updateById(info);
        } catch (Exception e) {
            log.error("更新设备报修失败", e);
            return false;
        }
    }

    @Override
    public boolean delete(Integer id) {
        try {
            return this.removeById(id);
        } catch (Exception e) {
            log.error("删除设备报修失败", e);
            return false;
        }
    }
}
