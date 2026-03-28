package com.sipc.monitoringsystem.service;

import com.sipc.monitoringsystem.model.po.DeviceRepair.DeviceRepairInfo;

import java.util.List;

public interface DeviceRepairService {
    List<DeviceRepairInfo> listAll();

    DeviceRepairInfo getById(Integer id);

    Integer create(DeviceRepairInfo info);

    boolean update(DeviceRepairInfo info);

    boolean delete(Integer id);
}
