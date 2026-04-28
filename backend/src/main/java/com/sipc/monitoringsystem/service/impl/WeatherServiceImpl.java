package com.sipc.monitoringsystem.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.sipc.monitoringsystem.dao.WeatherDao;
import com.sipc.monitoringsystem.model.dto.param.weather.CreateWeatherParam;
import com.sipc.monitoringsystem.model.po.Weather.Weather;
import com.sipc.monitoringsystem.service.WeatherService;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

import java.util.List;

import lombok.extern.slf4j.Slf4j;

/**
 * @author alaner28
 * @date 2026-02-05 1:25
 */
@Slf4j
@Service
public class WeatherServiceImpl extends ServiceImpl<WeatherDao, Weather> implements WeatherService {

        @Override
        @Cacheable(value = "cache", key = "'getNewestWeatherByMonitorId_'+#monitorId", unless = "#result==null")
        public Weather getNewestWeatherByMonitorId(Integer monitorId) {
                QueryWrapper<Weather> queryWrapper = new QueryWrapper<>();
                queryWrapper.eq("monitor_id", monitorId);
                queryWrapper.orderByDesc("create_time");
                List<Weather> weatherList = this.list(queryWrapper);
                return weatherList.isEmpty() ? null : weatherList.get(0);
        }

        @Override
        @Cacheable(value = "cache", key = "'getWeatherListByMonitorId_'+#monitorId", unless = "#result==null")
        public List<Weather> getWeatherListByMonitorId(Integer monitorId) {
                QueryWrapper<Weather> queryWrapper = new QueryWrapper<>();
                queryWrapper.eq("monitor_id", monitorId);
                queryWrapper.orderByDesc("create_time");
                return this.list(queryWrapper);
        }

        @Override
        @CacheEvict(value = "cache", allEntries = true)
        public Integer addWeather(CreateWeatherParam param) {
                Weather weather = new Weather();
                weather.setMonitorId(param.getMonitorId());
                weather.setWeather(param.getWeather());
                weather.setTemperature(param.getTemperature());
                weather.setHumidity(param.getHumidity());
                try {
                        save(weather);
                        return weather.getId();
                } catch (Exception e) {
                        log.error("添加天气失败");
                        return -1;
                }
        }
}
