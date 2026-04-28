package com.sipc.monitoringsystem.dao;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.sipc.monitoringsystem.model.po.Environment.EnvironmentRecord;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface EnvironmentRecordDao extends BaseMapper<EnvironmentRecord> {
}
