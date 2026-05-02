# 数据库表字段说明

本文档只解释“当前数据库里的 14 张表及其字段含义”，不再展开 SQL 脚本用途�?

当前 14 张表如下�?

1. `user_info`
2. `case_type_info`
3. `monitor`
4. `alarm_info`
5. `weather_info`
6. `system_message`
7. `alarm_push_record`
8. `device_repair_info`
9. `parking_space_info`
10. `visitor_info`
11. `environment_sensor_record`
12. `parking_area_status`
13. `parking_area_record`
14. `weather_region_config`

---

## 1. `user_info`

表用途：

- 存储系统用户信息
- 同时承载附近居民告警推送相关配�?

字段说明�?

- `id`
  用户主键 ID，自增，唯一标识一条用户记�?
- `user_name`
  用户名，用于登录、显示或用户识别
- `password`
  用户密码，通常应存加密后的密码�?
- `phone`
  用户手机号，用于联系、登录扩展或消息通知
- `role`
  用户角色标识，通常用于区分管理员、普通用户、物业人员等
- `is_resident`
  是否为居民用户，`0` 表示否，`1` 表示�?
- `home_area`
  用户常驻区域，例如小区楼栋、单元、片区，用于附近告警匹配
- `notify_enabled`
  是否启用告警推送，`0` 表示不接收，`1` 表示接收
- `push_cid`
  推送设备标识，例如移动端推送服务中�?client id

---

## 2. `case_type_info`

表用途：

- 存储告警事件类型字典
- �?`alarm_info.case_type` 提供可读名称

字段说明�?

- `id`
  事件类型主键 ID
- `case_type_name`
  事件类型名称，例如“烟雾”“明火”“摔倒�?

---

## 3. `monitor`

表用途：

- 存储监控点、摄像头、监测点位基础信息
- 同时记录该监控点启用了哪些算法能�?

字段说明�?

- `id`
  监控点主�?ID
- `name`
  监控点名称，例如“南门摄像头”�?号楼电梯厅�?
- `area`
  监控点所属区域，例如楼栋、街区、停车区
- `leader`
  该区域或设备的负责人
- `alarm_cnt`
  累计告警次数或当前统计的告警数量
- `stream_link`
  视频流地址，例�?RTMP、RTSP 或其他流媒体地址
- `running`
  该监控点是否启用或在线，`0` 表示关闭/未运行，`1` 表示运行�?
- `danger_area`
  是否启用危险区域识别
- `fall`
  是否启用摔倒识�?
- `flame`
  是否启用明火识别
- `smoke`
  是否启用烟雾识别
- `punch`
  是否启用打架/斗殴识别
- `rubbish`
  是否启用垃圾乱放识别
- `ice`
  是否启用冰面识别
- `ebike`
  是否启用电动车进楼识�?
- `vehicle`
  是否启用载具/车辆相关识别
- `wave`
  是否启用挥手呼救识别
- `left_x`
  监控画面中某个业务区域左上角或左边界�?X 坐标
- `left_y`
  监控画面中某个业务区域左上角或左边界�?Y 坐标
- `right_x`
  监控画面中某个业务区域右下角或右边界�?X 坐标
- `right_y`
  监控画面中某个业务区域右下角或右边界�?Y 坐标
- `latitude`
  监控点纬�?
- `longitude`
  监控点经�?

说明�?

- 一�?`left_x / left_y / right_x / right_y` 通常用来表达算法关注区域
- 多个算法开关字段本质上是“该监控点是否启用对应检测能力�?

---

## 4. `alarm_info`

表用途：

- 存储告警事件主记�?
- 是整个告警业务的核心表之一

字段说明�?

- `id`
  告警主键 ID
- `clip_link`
  告警视频片段链接、文件名或素材标�?
- `monitor_id`
  触发告警的监控点 ID，对�?`monitor.id`
- `case_type`
  告警类型 ID，对�?`case_type_info.id`
- `warning_level`
  告警等级，通常用于表示轻微、一般、严重、紧急等级别
- `create_time`
  告警产生时间
- `status`
  告警处理状态，通常 `0` 表示未处理，`1` 表示已处理，具体取值规则以业务代码为准
- `processing_content`
  告警处理说明，例如“已派人查看”“误报已关闭�?

---

## 5. `weather_info`

表用途：

- 存储天气信息记录
- 供前端展示、环境联动、天气趋势统计使�?

字段说明�?

- `id`
  天气记录主键 ID
- `monitor_id`
  关联监控�?ID
- `region_name`
  天气所属区域名称，例如“东区停车场”“A栋周边�?
- `weather`
  天气文本描述，例如“晴”“多云”“小雨�?
- `weather_code`
  天气代码，通常来自第三方天气服�?
- `temperature`
  温度
- `humidity`
  湿度
- `wind_speed`
  风�?
- `latitude`
  本次天气数据对应的纬�?
- `longitude`
  本次天气数据对应的经�?
- `source`
  天气数据来源，默认值是 `open-meteo`
- `create_time`
  这条天气记录写入数据库的时间

说明�?

- 这张表是“天气历史记录表”，不是单纯的当前状态表

---

## 6. `system_message`

表用途：

- 存储系统消息、站内消息、告警通知消息

字段说明�?

- `id`
  消息主键 ID
- `message`
  消息正文内容
- `receiver_user_id`
  接收用户 ID
  如果�?`NULL`，表示全员可�?
  如果有值，表示定向发给某个用户
- `timestamp`
  消息创建时间

---

## 7. `alarm_push_record`

表用途：

- 存储告警推送发送记�?
- 用于审计、重试、排查推送失�?

字段说明�?

- `id`
  推送记录主�?ID
- `alarm_id`
  对应的告�?ID，即这条推送是为哪一条告警产生的
- `user_id`
  被推送的用户 ID
- `push_type`
  推送方式，例如�?
  `ws`、`unipush`、`system_message`
- `push_status`
  推送结果状态，例如�?
  `success`、`fail`
- `push_detail`
  推送结果补充说明，例如错误信息、失败原因、返回内容摘�?
- `created_time`
  推送记录创建时�?

说明�?

- 同一�?`alarm_id + user_id + push_type` 在表中通常只保留一条唯一记录

---

## 8. `device_repair_info`

表用途：

- 存储设备报修信息

字段说明�?

- `id`
  报修记录主键 ID
- `device_name`
  报修设备名称
- `location`
  设备所在位�?
- `report_time`
  报修时间
- `repair_detail`
  报修描述，说明故障现象或维修诉求
- `publisher`
  报修发布�?

---

## 9. `parking_space_info`

表用途：

- 存储基础车位信息
- 偏静态或简化展示用�?

字段说明�?

- `id`
  车位记录主键 ID
- `location`
  车位位置描述
- `occupied_vehicle`
  当前占用车辆信息，例如车牌号、车主标识或临时占用说明
- `total_spaces`
  该记录对应的总车位数

说明�?

- 这张表更像“基础停车信息表�?
- 更完整的动态停车统计主要在 `parking_area_status` �?`parking_area_record`

---

## 10. `visitor_info`

表用途：

- 存储访客登记信息

字段说明�?

- `id`
  访客记录主键 ID
- `visitor_name`
  访客姓名
- `visit_time`
  到访时间
- `plate_number`
  来访车辆车牌�?

---

## 11. `environment_sensor_record`

表用途：

- 存储 IoT 环境传感器上报记�?
- 是环境监测的历史流水�?

字段说明�?

- `id`
  环境记录主键 ID
- `monitor_id`
  关联监控�?ID
- `device_code`
  上报设备编号，用来区分不�?IoT 设备
- `temperature`
  温度�?
- `humidity`
  湿度�?
- `pm25`
  PM2.5 数�?
- `combustible_gas`
  可燃气体浓度
- `create_time`
  采集时间或上报时�?

说明�?

- 这张表是“时间序列记录表”，每次上报都会新增一�?

---

## 12. `parking_area_status`

表用途：

- 存储停车区域的“当前状态�?
- 面向实时展示和当前余位查�?

字段说明�?

- `id`
  当前状态记录主�?ID
- `monitor_id`
  关联监控�?ID
- `device_code`
  上报该状态的设备编号
- `area_code`
  停车区域编码，通常用于系统内部唯一识别区域
- `area_name`
  停车区域名称，面向展�?
- `total_spaces`
  该停车区域总车位数
- `occupied_spaces`
  当前已占用车位数
- `create_time`
  首次创建该状态记录的时间
- `update_time`
  最近一次更新该状态的时间

说明�?

- 一般同一�?`monitor_id + area_code` 只保留一条当前状�?

---

## 13. `parking_area_record`

表用途：

- 存储停车区域的历史记�?
- 面向统计分析、趋势回放、批次追�?

字段说明�?

- `id`
  历史记录主键 ID
- `monitor_id`
  关联监控�?ID
- `device_code`
  上报设备编号
- `batch_no`
  上报批次号，用于把同一次上报的多条区域记录归为一�?
- `area_code`
  停车区域编码
- `area_name`
  停车区域名称
- `total_spaces`
  区域总车位数
- `occupied_spaces`
  当时已占用车位数
- `create_time`
  该条历史记录生成时间

说明�?

- �?`parking_area_status` 的区别是�?
  `parking_area_status` 保存“当前值�?
  `parking_area_record` 保存“历史过程值�?

---

## 14. `weather_region_config`

表用途：

- 存储监控点对应的天气区域配置
- 用于天气采集任务知道“该去查哪一个区域的天气�?

字段说明�?

- `id`
  配置主键 ID
- `monitor_id`
  关联监控�?ID
- `region_name`
  区域名称
- `latitude`
  天气查询使用的纬�?
- `longitude`
  天气查询使用的经�?
- `timezone`
  区域时区，默�?`Asia/Shanghai`
- `enabled`
  是否启用该天气配置，`1` 启用，`0` 停用
- `create_time`
  配置创建时间
- `update_time`
  配置最近更新时�?

说明�?

- 这张表是“配置表”，不是天气结果�?
- 真正的天气结果记录在 `weather_info`

---

## 表关系概�?

为了更容易理解，可以�?14 张表分为 4 类：

### 1. 用户与消�?

- `user_info`
- `system_message`
- `alarm_push_record`

### 2. 监控与告�?

- `monitor`
- `case_type_info`
- `alarm_info`

### 3. 环境与天�?

- `environment_sensor_record`
- `weather_region_config`
- `weather_info`

### 4. 停车、访客与运维

- `parking_space_info`
- `parking_area_status`
- `parking_area_record`
- `visitor_info`
- `device_repair_info`

---

## 常见关联关系

虽然数据库里不一定都写了外键，但业务上通常有这些关系：

- `alarm_info.monitor_id` 对应 `monitor.id`
- `alarm_info.case_type` 对应 `case_type_info.id`
- `weather_info.monitor_id` 对应 `monitor.id`
- `weather_region_config.monitor_id` 对应 `monitor.id`
- `environment_sensor_record.monitor_id` 对应 `monitor.id`
- `parking_area_status.monitor_id` 对应 `monitor.id`
- `parking_area_record.monitor_id` 对应 `monitor.id`
- `alarm_push_record.alarm_id` 对应 `alarm_info.id`
- `alarm_push_record.user_id` 对应 `user_info.id`
- `system_message.receiver_user_id` 对应 `user_info.id`

---

## 从零开始创建数据库

推荐先登�?MySQL，再手动创建数据库和用户，然后执行初始化 SQL�?
### 1. 登录 MySQL

```bash
mysql -u root -p
```

如果�?Ubuntu �?root 使用 `auth_socket`�?
```bash
sudo mysql
```

### 2. 创建数据�?
```sql
CREATE DATABASE IF NOT EXISTS SweatPear
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;
```


### 3. 切换到数据库

```sql
USE SweatPear;
```

### 5. 执行完整初始化脚本?
```bash
mysql --default-character-set=utf8mb4 -u root -p SweatPear < sql/final_schema.sql
```

如果你已经先进入 MySQL，也可以�?MySQL 命令行里执行�?
```sql
SOURCE sql/final_schema.sql;
```

### 6. 验证数据库是否创建成�?
```sql
SHOW DATABASES LIKE 'SweatPear';
USE SweatPear;
SHOW TABLES;
```

### 7. 后端配置建议

把后端连接账号改成业务用户，不要继续使用 `root`�?
```bash
export MYSQL_HOST=127.0.0.1
export MYSQL_PORT=3306
export MYSQL_DATABASE=SweatPear
export MYSQL_USERNAME=monitoring_app
export MYSQL_PASSWORD='replace-with-strong-password'
```

---



