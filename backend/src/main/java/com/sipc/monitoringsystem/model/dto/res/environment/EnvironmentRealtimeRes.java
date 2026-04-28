package com.sipc.monitoringsystem.model.dto.res.environment;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.sipc.monitoringsystem.model.po.Environment.EnvironmentRecord;
import lombok.Data;

import java.sql.Timestamp;

@Data
public class EnvironmentRealtimeRes {
    private Integer monitorId;
    private String deviceCode;
    private String weather;
    private Float temperature;
    private Float humidity;
    private Float pm25;
    private Integer aqi;

    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private Timestamp createTime;

    public EnvironmentRealtimeRes(EnvironmentRecord record) {
        this.monitorId = record.getMonitorId();
        this.deviceCode = record.getDeviceCode();
        this.weather = record.getWeather();
        this.temperature = record.getTemperature();
        this.humidity = record.getHumidity();
        this.pm25 = record.getPm25();
        this.aqi = record.getAqi();
        this.createTime = record.getCreateTime();
    }
}
