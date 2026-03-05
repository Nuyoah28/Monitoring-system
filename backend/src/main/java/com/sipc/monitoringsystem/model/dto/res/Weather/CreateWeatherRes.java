package com.sipc.monitoringsystem.model.dto.res.Weather;

/**
 * @author alaner28
 * &#064;data 2026/2/5 1:34
 */
import lombok.Data;

@Data
public class CreateWeatherRes {
    private Integer id;

    public CreateWeatherRes(Integer id) {
        this.id = id;
    }
}