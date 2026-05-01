package com.sipc.monitoringsystem.service.impl;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.sipc.monitoringsystem.config.IotMqttProperties;
import com.sipc.monitoringsystem.model.dto.param.iot.ReportAlarmMqttParam;
import com.sipc.monitoringsystem.model.dto.param.iot.ReportEnvironmentParam;
import com.sipc.monitoringsystem.service.EnvironmentDataService;
import com.sipc.monitoringsystem.service.IotAlarmIngressService;
import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken;
import org.eclipse.paho.client.mqttv3.MqttCallbackExtended;
import org.eclipse.paho.client.mqttv3.MqttClient;
import org.eclipse.paho.client.mqttv3.MqttConnectOptions;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.eclipse.paho.client.mqttv3.MqttMessage;
import org.springframework.stereotype.Component;

@Component
@Slf4j
@RequiredArgsConstructor
public class IotMqttConsumer {

    private final IotMqttProperties properties;
    private final ObjectMapper objectMapper;
    private final EnvironmentDataService environmentDataService;
    private final IotAlarmIngressService iotAlarmIngressService;

    private MqttClient mqttClient;

    @PostConstruct
    public void start() {
        if (!properties.isEnabled()) {
            log.info("IoT MQTT consumer disabled");
            return;
        }

        try {
            mqttClient = new MqttClient(
                    properties.getBrokerUrl(),
                    properties.getClientId() + "-" + MqttClient.generateClientId()
            );
            mqttClient.setCallback(new MqttCallbackExtended() {
                @Override
                public void connectComplete(boolean reconnect, String serverURI) {
                    subscribeTopics();
                    log.info("IoT MQTT connected: reconnect={}, broker={}", reconnect, serverURI);
                }

                @Override
                public void connectionLost(Throwable cause) {
                    log.warn("IoT MQTT connection lost: {}", cause == null ? "unknown" : cause.getMessage());
                }

                @Override
                public void messageArrived(String topic, MqttMessage message) throws Exception {
                    handleMessage(topic, message);
                }

                @Override
                public void deliveryComplete(IMqttDeliveryToken token) {
                }
            });

            MqttConnectOptions options = new MqttConnectOptions();
            options.setAutomaticReconnect(true);
            options.setCleanSession(true);
            if (properties.getUsername() != null && !properties.getUsername().isBlank()) {
                options.setUserName(properties.getUsername());
            }
            if (properties.getPassword() != null && !properties.getPassword().isBlank()) {
                options.setPassword(properties.getPassword().toCharArray());
            }

            mqttClient.connect(options);
            subscribeTopics();
        } catch (MqttException e) {
            log.error("Failed to start IoT MQTT consumer", e);
        }
    }

    @PreDestroy
    public void stop() {
        if (mqttClient != null) {
            try {
                mqttClient.disconnect();
                mqttClient.close();
            } catch (MqttException e) {
                log.warn("Failed to stop IoT MQTT consumer cleanly", e);
            }
        }
    }

    private void subscribeTopics() {
        if (mqttClient == null || !mqttClient.isConnected()) {
            return;
        }

        try {
            mqttClient.subscribe(properties.getEnvironmentTopic(), properties.getQos());
            mqttClient.subscribe(properties.getAlarmTopic(), properties.getQos());
        } catch (MqttException e) {
            log.error("Failed to subscribe MQTT topics", e);
        }
    }

    private void handleMessage(String topic, MqttMessage message) throws Exception {
        String payload = new String(message.getPayload());
        if (topicMatches(topic, properties.getEnvironmentTopic())) {
            ReportEnvironmentParam param = objectMapper.readValue(payload, ReportEnvironmentParam.class);
            if (param.getMonitorId() == null) {
                log.warn("Ignore MQTT environment payload without monitorId: {}", payload);
                return;
            }
            environmentDataService.report(param);
            log.info("MQTT environment ingested: topic={}, deviceCode={}", topic, param.getDeviceCode());
            return;
        }

        if (topicMatches(topic, properties.getAlarmTopic())) {
            ReportAlarmMqttParam param = objectMapper.readValue(payload, ReportAlarmMqttParam.class);
            if (param.getCameraId() == null || param.getCaseType() == null) {
                log.warn("Ignore MQTT alarm payload without cameraId/caseType: {}", payload);
                return;
            }
            String clipId = (param.getClipId() == null || param.getClipId().isBlank())
                    ? "mqtt-alarm"
                    : param.getClipId();
            iotAlarmIngressService.receiveAndDispatchAlarm(
                    param.getCameraId(),
                    param.getCaseType(),
                    clipId,
                    param.getOccurredAt()
            );
            log.info("MQTT alarm ingested: topic={}, cameraId={}, caseType={}",
                    topic, param.getCameraId(), param.getCaseType());
        }
    }

    private boolean topicMatches(String actual, String pattern) {
        String regex = pattern
                .replace("+", "[^/]+")
                .replace("#", ".+");
        return actual.matches(regex);
    }
}
