package com.sipc.monitoringsystem.dao;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.sipc.monitoringsystem.model.po.Alarm.AlarmPushRecord;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface AlarmPushRecordDao extends BaseMapper<AlarmPushRecord> {
}
