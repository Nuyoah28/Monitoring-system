# MQTT Integration

This project now uses MQTT for the two IoT reporting paths that benefit most from event or telemetry messaging:

- sensor environment telemetry
- algorithm alarm events

## Topics

- environment publish topic:
  `iot/sensor/{deviceCode}/environment`
- alarm publish topic:
  `iot/algo/{deviceCode}/alarm`

Backend subscriptions:

- `iot/sensor/+/environment`
- `iot/algo/+/alarm`

## Payloads

Environment payload:

```json
{
  "monitorId": 1,
  "deviceCode": "iot-sensor-01",
  "temperature": 25.6,
  "humidity": 48.3,
  "pm25": 156.0,
  "combustibleGas": 13.3
}
```

Alarm payload:

```json
{
  "cameraId": 1,
  "caseType": 1,
  "clipId": "mqtt-alarm-1710000000",
  "occurredAt": "2026-05-02 12:00:00"
}
```

## IoT Environment Variables

Sensor uploader:

- `MQTT_BROKER_HOST`
- `MQTT_BROKER_PORT`
- `MQTT_USERNAME`
- `MQTT_PASSWORD`
- `MQTT_CLIENT_ID`
- `MQTT_TOPIC_ENVIRONMENT`

Algorithm alarm publisher:

- `MQTT_BROKER_HOST`
- `MQTT_BROKER_PORT`
- `MQTT_USERNAME`
- `MQTT_PASSWORD`
- `MQTT_CLIENT_ID`
- `MQTT_TOPIC_ALARM`
- `ALARM_CAMERA_ID`
- `ALARM_CASE_TYPE`
- `MQTT_ALARM_CLIP_PREFIX`

## Backend Configuration

Spring Boot config keys:

```yaml
iot:
  mqtt:
    enabled: true
    broker-url: tcp://127.0.0.1:1883
    client-id: monitoring-system-backend
    environment-topic: iot/sensor/+/environment
    alarm-topic: iot/algo/+/alarm
    qos: 1
```

## Suggested Local Test Flow

1. Start an MQTT broker such as Mosquitto on `127.0.0.1:1883`
2. Start the backend so it subscribes to the two IoT topics
3. Start `iot/sensor/sensor_uploader.py`
4. Start the algorithm side if you want alarm messages too
5. Check backend logs for MQTT ingestion success
