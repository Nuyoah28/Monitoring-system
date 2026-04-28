package com.sipc.monitoringsystem.controller;

import com.sipc.monitoringsystem.aop.Pass;
import com.sipc.monitoringsystem.model.dto.CommonResult;
import com.sipc.monitoringsystem.model.dto.res.Weather.GetWeatherRes;
import com.sipc.monitoringsystem.model.dto.res.Weather.WeatherForecastDayRes;
import com.sipc.monitoringsystem.model.po.Weather.Weather;
import com.sipc.monitoringsystem.service.WeatherService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.ArrayList;
import java.util.List;

@RestController
@RequestMapping("/api/v1/weather")
public class WeatherController {

    private final WeatherService weatherService;

    public WeatherController(WeatherService weatherService) {
        this.weatherService = weatherService;
    }

    @GetMapping("/newest/{monitorId}")
    @Pass
    public CommonResult<GetWeatherRes> getWeather(@PathVariable Integer monitorId) {
        Weather weather = weatherService.getNewestWeatherByMonitorId(monitorId);
        if (weather == null) {
            return CommonResult.fail("暂无天气数据");
        }
        return CommonResult.success(new GetWeatherRes(weather));
    }

    @GetMapping("/all/{monitorId}")
    @Pass
    public CommonResult<List<GetWeatherRes>> getWeatherHistory(@PathVariable Integer monitorId) {
        List<Weather> weatherList = weatherService.getWeatherListByMonitorId(monitorId);
        List<GetWeatherRes> result = new ArrayList<>();
        for (Weather weather : weatherList) {
            result.add(new GetWeatherRes(weather));
        }
        return CommonResult.success(result);
    }

    @GetMapping("/forecast/{monitorId}")
    @Pass
    public CommonResult<List<WeatherForecastDayRes>> getForecast(@PathVariable Integer monitorId) {
        return CommonResult.success(weatherService.getForecastByMonitorId(monitorId));
    }

    @PostMapping("/sync/{monitorId}")
    @Pass
    public CommonResult<GetWeatherRes> syncWeather(@PathVariable Integer monitorId) {
        Weather weather = weatherService.syncWeatherByMonitorId(monitorId);
        if (weather == null) {
            return CommonResult.fail("天气同步失败");
        }
        return CommonResult.success(new GetWeatherRes(weather));
    }
}
