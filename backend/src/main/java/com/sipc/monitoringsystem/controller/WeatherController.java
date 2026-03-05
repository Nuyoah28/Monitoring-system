package com.sipc.monitoringsystem.controller;

import com.sipc.monitoringsystem.aop.Pass;
import com.sipc.monitoringsystem.model.dto.CommonResult;
import com.sipc.monitoringsystem.model.dto.param.weather.CreateWeatherParam;
import com.sipc.monitoringsystem.model.dto.res.Weather.CreateWeatherRes;
import com.sipc.monitoringsystem.model.dto.res.Weather.GetWeatherRes;
import com.sipc.monitoringsystem.model.po.Weather.Weather;
import com.sipc.monitoringsystem.service.WeatherService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.List;

/**
 * @author alaner28
 * &#064;date  2026-02-05 1:25
 */

@RestController
@RequestMapping("/api/v1/weather")
public class WeatherController {
    @Autowired
    private WeatherService weatherService;

    @GetMapping("/newest/{monitorId}")
    @Pass
    public CommonResult<GetWeatherRes> getWeather(@PathVariable Integer monitorId) {
        Weather weather = weatherService.getNewestWeatherByMonitorId(monitorId);
        if (weather == null) {
            return CommonResult.fail("获取最新天气失败");
        }
        GetWeatherRes getWeatherRes = new GetWeatherRes(weather);
        return CommonResult.success(getWeatherRes);
    }

    @GetMapping("/all/{monitorId}")
    public CommonResult<List<GetWeatherRes>> getWeatherHistory(@PathVariable Integer monitorId) {
        List<Weather> weatherList = weatherService.getWeatherListByMonitorId(monitorId);
        if (weatherList == null) {
            return CommonResult.fail("获取天气列表失败");
        }
        List<GetWeatherRes> getWeatherResList = new ArrayList<>();
        for (Weather weather : weatherList) {
            GetWeatherRes getWeatherRes = new GetWeatherRes(weather);
            getWeatherResList.add(getWeatherRes);
        }
        return CommonResult.success(getWeatherResList);
    }

    @PostMapping("/add")
    @Pass
    public CommonResult<CreateWeatherRes> createWeather(@RequestBody CreateWeatherParam createWeatherParam) {
        Integer id = weatherService.addWeather(createWeatherParam);
        if (id == null) {
            return CommonResult.fail("创建天气失败");
        }
        CreateWeatherRes createWeatherRes = new CreateWeatherRes(id);
        return CommonResult.success(createWeatherRes);
    }
}
