package com.sipc.monitoringsystem.dao;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.sipc.monitoringsystem.model.po.Weather.Weather;
import org.apache.ibatis.annotations.Mapper;

/**
 * @author alaner28
 * @date 2026-02-05 1:25
 */
@Mapper
public interface WeatherDao extends BaseMapper<Weather> {
}
