package com.sipc.monitoringsystem.service;

import com.sipc.monitoringsystem.model.po.DeviceRepair.DeviceRepairInfo;
import com.sipc.monitoringsystem.model.po.User.User;

import java.util.List;

public interface DeviceRepairService {
    List<DeviceRepairInfo> listAll(User currentUser);

    DeviceRepairInfo getById(Integer id, User currentUser);

    Integer create(DeviceRepairInfo info, User currentUser);

    boolean update(DeviceRepairInfo info, User currentUser);

    boolean delete(Integer id, User currentUser);
}
