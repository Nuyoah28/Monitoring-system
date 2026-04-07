# 天气类技能 (Weather Skills)

## 概述
天气类技能用于查询监控点相关的天气信息。

## 技能列表

### 1. get_weather_newest - 最新天气查询
- **功能**: 查询指定监控点的最新天气
- **参数**:
  - `monitor_id`: 可选，监控点 ID
  - `monitor_name`: 可选，监控点名称

### 2. get_weather_history - 历史天气查询
- **功能**: 查询指定监控点的历史天气记录
- **参数**:
  - `monitor_id`: 可选，监控点 ID
  - `monitor_name`: 可选，监控点名称
  - `time_text`: 可选，自然语言时间，如 昨天、近7天

## 后端接口
- `GET /weather/newest/{monitor_id}` - 查询最新天气
- `GET /weather/all/{monitor_id}` - 查询历史天气
