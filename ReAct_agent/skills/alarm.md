# 告警类技能 (Alarm Skills)

## 概述
告警类技能用于查询、统计和管理系统中的告警信息。

## 技能列表

### 1. get_alarm_list - 告警列表查询
- **功能**: 查询告警列表，支持类型、状态、等级和时间筛选
- **参数**:
  - `case_types`: 可选，int 数组，例如 [5] 表示明火
  - `status`: 可选，0=未处理，1=已处理
  - `warning_levels`: 可选，int 数组，例如 [4, 5]
  - `page_size`: 可选，返回条数，默认 10
  - `time_text`: 可选，自然语言时间，如 今天、近7天

### 2. get_alarm_count - 告警数量统计
- **功能**: 统计符合筛选条件的告警数量
- **参数**:
  - `case_types`: 可选，int 数组，例如 [5]
  - `status`: 可选，0=未处理，1=已处理
  - `warning_levels`: 可选，int 数组，例如 [4, 5]
  - `time_text`: 可选，自然语言时间，如 今天、近7天

### 3. get_alarm_detail - 告警详情查询
- **功能**: 按告警 ID 查询告警详情
- **参数**:
  - `alarm_id`: 必填，告警 ID

### 4. get_alarm_history - 历史告警查询
- **功能**: 查询告警趋势和历史变化
- **参数**:
  - `defer`: 可选，1/3/7/30，分别表示今天、近3天、近7天、近30天

### 5. get_realtime_alarm - 实时告警
- **功能**: 查询实时告警概况和大屏态势数据
- **参数**: 无

### 6. update_alarm_status - 更新告警状态
- **功能**: 更新告警处理状态，可标记为已处理或未处理
- **参数**:
  - `alarm_id`: 必填，告警 ID
  - `status`: 必填，0=未处理，1=已处理
  - `processing_content`: 可选，处理说明

## 后端接口
- `GET /alarm/query` - 分页查询告警列表
- `GET /alarm/query/cnt/history` - 查询历史告警统计
- `GET /alarm/realtime` - 查询实时告警
- `GET /alarm/{alarm_id}` - 查询告警详情
- `PUT /alarm/update` - 更新告警状态
