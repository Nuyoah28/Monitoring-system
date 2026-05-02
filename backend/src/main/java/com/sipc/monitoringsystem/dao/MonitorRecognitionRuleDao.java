package com.sipc.monitoringsystem.dao;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.sipc.monitoringsystem.model.po.Monitor.MonitorRecognitionRule;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface MonitorRecognitionRuleDao extends BaseMapper<MonitorRecognitionRule> {
}
