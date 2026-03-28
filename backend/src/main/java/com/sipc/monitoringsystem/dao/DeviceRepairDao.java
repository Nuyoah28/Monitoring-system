package com.sipc.monitoringsystem.dao;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.sipc.monitoringsystem.model.po.DeviceRepair.DeviceRepairInfo;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface DeviceRepairDao extends BaseMapper<DeviceRepairInfo> {
}
