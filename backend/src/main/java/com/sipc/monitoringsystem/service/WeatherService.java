package com.sipc.monitoringsystem.service;

import com.sipc.monitoringsystem.model.dto.param.weather.CreateWeatherParam;
import com.sipc.monitoringsystem.model.po.Weather.Weather;

import java.util.List;

/**
 * @author alaner28
 * @date 2026-02-05 1:25
 */
public interface WeatherService {
        //获取最新天气信息
        Weather getNewestWeatherByMonitorId(Integer monitorId);
        List<Weather> getWeatherListByMonitorId(Integer monitorId);
        Integer addWeather(CreateWeatherParam param);

}
