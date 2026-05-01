import json
import os
import re
import sys
import time
from dataclasses import dataclass
from typing import Optional

import paho.mqtt.client as mqtt
import serial


SERIAL_PORT = os.getenv("SERIAL_PORT", "")
SERIAL_BAUD_RATE = int(os.getenv("SERIAL_BAUD_RATE", "115200"))
REPORT_INTERVAL_SECONDS = int(os.getenv("REPORT_INTERVAL_SECONDS", "120"))
MONITOR_ID = int(os.getenv("MONITOR_ID", "1"))
DEVICE_CODE = os.getenv("DEVICE_CODE", "iot-sensor-01")
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "127.0.0.1")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
MQTT_TOPIC_ENVIRONMENT = os.getenv(
    "MQTT_TOPIC_ENVIRONMENT",
    f"iot/sensor/{DEVICE_CODE}/environment",
)
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", f"{DEVICE_CODE}-sensor-uploader")
MQ9_ADC_FULL_SCALE = float(os.getenv("MQ9_ADC_FULL_SCALE", "4095"))
MQ9_PPM_FULL_SCALE = float(os.getenv("MQ9_PPM_FULL_SCALE", "100"))

GP2Y_LINE_RE = re.compile(
    r"GP2Y\s*ADC:\s*(?P<adc>\d+).*?(?P<dust>[0-9]+(?:\.[0-9]+)?)\s*mg/m",
    re.IGNORECASE,
)
MQ9_LINE_RE = re.compile(
    r"MQ9\s*ADC:\s*(?P<adc>\d+).*?(?P<voltage>[0-9]+(?:\.[0-9]+)?)\s*V",
    re.IGNORECASE,
)


@dataclass
class SensorReading:
    temperature_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    pm25_ug_m3: Optional[float] = None
    combustible_gas_ppm: Optional[float] = None

    def merge(self, other: "SensorReading") -> "SensorReading":
        return SensorReading(
            temperature_c=other.temperature_c if other.temperature_c is not None else self.temperature_c,
            humidity_pct=other.humidity_pct if other.humidity_pct is not None else self.humidity_pct,
            pm25_ug_m3=other.pm25_ug_m3 if other.pm25_ug_m3 is not None else self.pm25_ug_m3,
            combustible_gas_ppm=(
                other.combustible_gas_ppm
                if other.combustible_gas_ppm is not None
                else self.combustible_gas_ppm
            ),
        )

    def can_upload(self) -> bool:
        return any(
            value is not None
            for value in (
                self.temperature_c,
                self.humidity_pct,
                self.pm25_ug_m3,
                self.combustible_gas_ppm,
            )
        )

    def summary(self) -> str:
        parts = []
        if self.temperature_c is not None:
            parts.append(f"temperature={self.temperature_c:.1f}C")
        if self.humidity_pct is not None:
            parts.append(f"humidity={self.humidity_pct:.1f}%")
        if self.pm25_ug_m3 is not None:
            parts.append(f"pm25={self.pm25_ug_m3:.1f}ug/m3")
        if self.combustible_gas_ppm is not None:
            parts.append(f"combustibleGas={self.combustible_gas_ppm:.1f}ppm")
        return " ".join(parts) if parts else "no valid values"


def compute_checksum(body: str) -> int:
    checksum = 0
    for ch in body.encode("ascii"):
        checksum ^= ch
    return checksum


def parse_iot_frame(line: str) -> Optional[SensorReading]:
    frame = line.strip()
    if not frame or not frame.startswith("$"):
        return None

    checksum_sep = frame.find("*")
    if checksum_sep == -1 or checksum_sep + 2 >= len(frame):
        return None

    body = frame[1:checksum_sep]
    checksum_hex = frame[checksum_sep + 1:checksum_sep + 3]

    try:
        expected_checksum = int(checksum_hex, 16)
    except ValueError:
        return None

    if compute_checksum(body) != expected_checksum:
        return None

    fields = body.split(",")
    if len(fields) != 5:
        return None

    if fields[0] != "IOT" or fields[1] != "1" or fields[2] != "ENV":
        return None

    try:
        temperature_c = float(fields[3])
        humidity_pct = float(fields[4])
    except ValueError:
        return None

    if not (-40.0 <= temperature_c <= 125.0):
        return None
    if not (0.0 <= humidity_pct <= 100.0):
        return None

    return SensorReading(temperature_c=temperature_c, humidity_pct=humidity_pct)


def parse_gp2y_line(line: str) -> Optional[SensorReading]:
    match = GP2Y_LINE_RE.search(line)
    if match is None:
        return None

    dust_mg_m3 = float(match.group("dust"))
    if dust_mg_m3 < 0:
        return None

    # The STM32 output uses mg/m3, while the dashboard and backend store PM2.5 as ug/m3.
    pm25_ug_m3 = dust_mg_m3 * 1000.0
    return SensorReading(pm25_ug_m3=pm25_ug_m3)


def parse_mq9_line(line: str) -> Optional[SensorReading]:
    match = MQ9_LINE_RE.search(line)
    if match is None:
        return None

    adc_value = float(match.group("adc"))
    if adc_value < 0 or MQ9_ADC_FULL_SCALE <= 0 or MQ9_PPM_FULL_SCALE <= 0:
        return None

    combustible_gas_ppm = adc_value / MQ9_ADC_FULL_SCALE * MQ9_PPM_FULL_SCALE
    return SensorReading(combustible_gas_ppm=combustible_gas_ppm)


def parse_line(line: str) -> Optional[SensorReading]:
    reading = parse_iot_frame(line)
    if reading is not None:
        return reading

    reading = parse_gp2y_line(line)
    if reading is not None:
        return reading

    return parse_mq9_line(line)


def decode_serial_line(raw: bytes) -> str:
    for encoding in ("utf-8", "gb18030", "ascii"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def build_mqtt_client() -> mqtt.Client:
    client = mqtt.Client(client_id=MQTT_CLIENT_ID)
    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD or None)
    client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, keepalive=60)
    client.loop_start()
    return client


def publish_environment(client: mqtt.Client, reading: SensorReading) -> None:
    payload = {
        "monitorId": MONITOR_ID,
        "deviceCode": DEVICE_CODE,
        "temperature": round(reading.temperature_c, 1) if reading.temperature_c is not None else None,
        "humidity": round(reading.humidity_pct, 1) if reading.humidity_pct is not None else None,
        "pm25": round(reading.pm25_ug_m3, 1) if reading.pm25_ug_m3 is not None else None,
        "combustibleGas": (
            round(reading.combustible_gas_ppm, 1)
            if reading.combustible_gas_ppm is not None
            else None
        ),
    }
    info = client.publish(
        MQTT_TOPIC_ENVIRONMENT,
        json.dumps(payload, ensure_ascii=True),
        qos=1,
    )
    info.wait_for_publish()
    if info.rc != mqtt.MQTT_ERR_SUCCESS:
        raise RuntimeError(mqtt.error_string(info.rc))
    print(f"[sensor] publish ok topic={MQTT_TOPIC_ENVIRONMENT} payload={payload}")


def main() -> int:
    if not SERIAL_PORT:
        print("[sensor] SERIAL_PORT is required, for example COM3 or /dev/ttyUSB0")
        return 1

    print(
        f"[sensor] starting uploader port={SERIAL_PORT} baud={SERIAL_BAUD_RATE} "
        f"mqtt={MQTT_BROKER_HOST}:{MQTT_BROKER_PORT} interval={REPORT_INTERVAL_SECONDS}s "
        f"mq9Scale={MQ9_PPM_FULL_SCALE:.1f}ppm/{MQ9_ADC_FULL_SCALE:.0f}adc"
    )

    mqtt_client: Optional[mqtt.Client] = None
    while True:
        try:
            mqtt_client = build_mqtt_client()
            print(f"[sensor] mqtt connected: {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
            break
        except Exception as exc:
            print(f"[sensor] mqtt connect error: {exc}; retry in 5s")
            time.sleep(5)

    latest_reading: Optional[SensorReading] = None
    last_report_at = 0.0

    try:
        while True:
            try:
                with serial.Serial(SERIAL_PORT, SERIAL_BAUD_RATE, timeout=1) as ser:
                    print(f"[sensor] serial connected: {SERIAL_PORT}")
                    while True:
                        raw = ser.readline()
                        if raw:
                            line = decode_serial_line(raw)
                            reading = parse_line(line)
                            if reading is not None:
                                latest_reading = (
                                    latest_reading.merge(reading)
                                    if latest_reading is not None
                                    else reading
                                )
                                print(f"[sensor] frame ok {latest_reading.summary()}")
                            elif line.strip().startswith("$"):
                                print(f"[sensor] ignored line: {line.strip()}")

                        now = time.time()
                        if (
                            latest_reading is not None
                            and latest_reading.can_upload()
                            and now - last_report_at >= REPORT_INTERVAL_SECONDS
                        ):
                            try:
                                publish_environment(mqtt_client, latest_reading)
                                last_report_at = now
                            except Exception as exc:
                                print(f"[sensor] mqtt publish error: {exc}; retry on next interval")
                                time.sleep(2)
            except serial.SerialException as exc:
                print(f"[sensor] serial error: {exc}; retry in 5s")
                time.sleep(5)
    except KeyboardInterrupt:
        print("[sensor] stopped by user")
        return 0
    finally:
        if mqtt_client is not None:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()


if __name__ == "__main__":
    sys.exit(main())
