package com.sipc.monitoringsystem.service.impl;

import com.sipc.monitoringsystem.model.po.Monitor.Monitor;
import com.sipc.monitoringsystem.service.MonitorService;
import com.sipc.monitoringsystem.service.WeatherService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.util.List;

@Slf4j
@Component
public class WeatherSyncScheduler {

    private final MonitorService monitorService;
    private final WeatherService weatherService;

    public WeatherSyncScheduler(MonitorService monitorService, WeatherService weatherService) {
        this.monitorService = monitorService;
        this.weatherService = weatherService;
    }

    @Scheduled(initialDelay = 15000, fixedDelayString = "${weather.sync.interval-ms:1800000}")
    public void syncAllWeather() {
        try {
            List<Monitor> monitors = monitorService.getMonitorList();
            for (Monitor monitor : monitors) {
                if (monitor.getId() != null) {
                    weatherService.syncWeatherByMonitorId(monitor.getId());
                }
            }
        } catch (Exception e) {
            log.error("syncAllWeather failed", e);
        }
    }
}
