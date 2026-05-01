package com.sipc.monitoringsystem.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Data
@Component
@ConfigurationProperties(prefix = "iot.mqtt")
public class IotMqttProperties {
    private boolean enabled = false;
    private String brokerUrl = "tcp://127.0.0.1:1883";
    private String clientId = "monitoring-system-backend";
    private String username;
    private String password;
    private String environmentTopic = "iot/sensor/+/environment";
    private String alarmTopic = "iot/algo/+/alarm";
    private int qos = 1;
}
