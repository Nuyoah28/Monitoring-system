package com.sipc.monitoringsystem.model.dto.param.weather;

import lombok.Data;

@Data
public class CreateWeatherParam {
    private Integer monitorId;
    private String weather;
    private Integer temperature;
    private Integer humidity;
}
