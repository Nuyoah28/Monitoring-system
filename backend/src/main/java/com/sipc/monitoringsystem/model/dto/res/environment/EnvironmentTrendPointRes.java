package com.sipc.monitoringsystem.model.dto.res.environment;

import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class EnvironmentTrendPointRes {
    private String label;
    private Integer aqi;
    private Integer humidity;
    private Integer pm25;
}
