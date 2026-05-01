# Sensor Uploader

This directory contains the standalone Python sensor side of the IoT project.

## Responsibility

- read STM32 environment data from a USB-TTL serial port
- validate supported serial formats
- publish environment data to MQTT

## Install

```bash
pip install -r requirements.txt
```

## Run

Windows example:

```powershell
$env:SERIAL_PORT="COM4"
$env:SERIAL_BAUD_RATE="115200"
$env:MONITOR_ID="1"
$env:DEVICE_CODE="iot-sensor-01"
$env:MQTT_BROKER_HOST="127.0.0.1"
$env:MQTT_BROKER_PORT="1883"
$env:MQTT_TOPIC_ENVIRONMENT="iot/sensor/iot-sensor-01/environment"
$env:REPORT_INTERVAL_SECONDS="120"
$env:MQ9_ADC_FULL_SCALE="4095"
$env:MQ9_PPM_FULL_SCALE="100"
python sensor_uploader.py
```

Linux example:

```bash
SERIAL_PORT=/dev/ttyUSB0 \
SERIAL_BAUD_RATE=115200 \
MONITOR_ID=1 \
DEVICE_CODE=iot-sensor-01 \
MQTT_BROKER_HOST=127.0.0.1 \
MQTT_BROKER_PORT=1883 \
MQTT_TOPIC_ENVIRONMENT=iot/sensor/iot-sensor-01/environment \
REPORT_INTERVAL_SECONDS=120 \
MQ9_ADC_FULL_SCALE=4095 \
MQ9_PPM_FULL_SCALE=100 \
python3 sensor_uploader.py
```

## Supported Input

The uploader accepts either of these serial formats:

- legacy temperature/humidity frame: `$IOT,1,ENV,<temperature_c>,<humidity_pct>*<checksum>`
- current STM32 text output with two lines:

```text
GP2Y ADC: 1892 | Voltage: 1.524V | Dust: 0.174mg/m3
MQ9  ADC:  546 | Voltage: 0.440V
```

Notes:

- `GP2Y` dust is converted from `mg/m3` to backend `pm25` in `ug/m3`
- `MQ9` currently uses ADC normalization to estimate `combustibleGas`
- `monitorId` and `deviceCode` are attached by the Python uploader before publish

## Protocol

See `STM32_SERIAL_PROTOCOL.md`.
