package com.sipc.monitoringsystem.model.dto.res.Weather;

import com.huaweicloud.sdk.thirdparty.com.fasterxml.jackson.annotation.JsonFormat;
import com.sipc.monitoringsystem.model.po.Weather.Weather;
import lombok.Data;

import java.sql.Timestamp;

/**
 * @author alaner28
 * &#064;data 2026/2/5 1:35
 */
@Data
public class GetWeatherRes {
    public GetWeatherRes(Weather weather) {
        this.id = weather.getId();
        this.monitorId = weather.getMonitorId();
        this.temperature = weather.getTemperature();
        this.humidity = weather.getHumidity();
        this.weather = weather.getWeather();
        this.createTime = weather.getCreateTime();
    }

    private Integer id;
    private Integer monitorId;
    private float temperature;
    private float humidity;
    private String weather;
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "GMT+8")
    private Timestamp createTime;
}
