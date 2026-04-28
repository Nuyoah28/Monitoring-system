package com.sipc.monitoringsystem.dao;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.sipc.monitoringsystem.model.po.Weather.WeatherRegionConfig;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface WeatherRegionConfigDao extends BaseMapper<WeatherRegionConfig> {
}
