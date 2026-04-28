package com.sipc.monitoringsystem.dao;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.sipc.monitoringsystem.model.po.Parking.ParkingAreaStatus;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface ParkingAreaStatusDao extends BaseMapper<ParkingAreaStatus> {
}
