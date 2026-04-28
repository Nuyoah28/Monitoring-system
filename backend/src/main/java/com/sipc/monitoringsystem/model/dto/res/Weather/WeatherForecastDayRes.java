package com.sipc.monitoringsystem.model.dto.res.Weather;

import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class WeatherForecastDayRes {
    private String date;
    private String dayweather;
    private String daytemp;
    private String nighttemp;
}
