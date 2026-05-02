-- =========================================================
-- Monitoring System 后端数据库最终表结构脚本
-- 适用: MySQL 8.0+ / Navicat
-- 说明:
--   1. 本文件只负责建库、建表、索引和外键，不写入演示数据。
--   2. 新环境初始化先执行本文件，再执行 final_seed_data.sql。
--   3. 本文件会 DROP 旧表；已有数据库不要直接执行，请使用 migrate_*.sql 增量迁移。
--   4. 告警等级以 case_type_info.warning_level 为默认配置，alarm_info.warning_level 保存发生时快照。
-- =========================================================

CREATE DATABASE IF NOT EXISTS `SweatPear`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_general_ci;

USE `SweatPear`;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `alarm_push_record`;
DROP TABLE IF EXISTS `system_message`;
DROP TABLE IF EXISTS `parking_traffic_flow_record`;
DROP TABLE IF EXISTS `parking_area_record`;
DROP TABLE IF EXISTS `parking_area_status`;
DROP TABLE IF EXISTS `environment_sensor_record`;
DROP TABLE IF EXISTS `weather_info`;
DROP TABLE IF EXISTS `weather_region_config`;
DROP TABLE IF EXISTS `monitor_recognition_rule`;
DROP TABLE IF EXISTS `alarm_info`;
DROP TABLE IF EXISTS `visitor_info`;
DROP TABLE IF EXISTS `parking_space_info`;
DROP TABLE IF EXISTS `device_repair_info`;
DROP TABLE IF EXISTS `monitor`;
DROP TABLE IF EXISTS `case_type_info`;
DROP TABLE IF EXISTS `user_info`;

SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE `user_info` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `user_name` VARCHAR(255) NOT NULL COMMENT '用户名',
  `password` VARCHAR(255) NOT NULL COMMENT '密码MD5值',
  `phone` VARCHAR(255) DEFAULT NULL COMMENT '手机号',
  `avatar_url` VARCHAR(255) DEFAULT NULL COMMENT '头像地址',
  `role` INT NOT NULL COMMENT '角色: 0管理员, 1普通用户',
  `is_resident` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否居民用户',
  `home_area` VARCHAR(50) DEFAULT NULL COMMENT '常驻区域',
  `notify_enabled` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否接收报警推送',
  `push_cid` VARCHAR(128) DEFAULT NULL COMMENT 'UniPush设备标识',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_name` (`user_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='用户表';

CREATE TABLE `case_type_info` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '报警类型ID',
  `case_type_name` VARCHAR(255) NOT NULL COMMENT '报警类型名称',
  `warning_level` TINYINT NOT NULL DEFAULT 1 COMMENT '默认告警等级：1低，2中，3高',
  `enabled` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用：1启用，0隐藏/停用',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_case_type_name` (`case_type_name`),
  KEY `idx_case_type_enabled` (`enabled`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='报警类型表';

CREATE TABLE `monitor` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '监控点ID',
  `name` VARCHAR(50) NOT NULL COMMENT '监控名称',
  `area` VARCHAR(50) DEFAULT NULL COMMENT '所在区域',
  `leader` VARCHAR(30) DEFAULT NULL COMMENT '负责人用户名',
  `alarm_cnt` INT NOT NULL DEFAULT 0 COMMENT '报警次数冗余统计',
  `stream_link` VARCHAR(255) DEFAULT NULL COMMENT '视频流链接',
  `running` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否运行中',
  `danger_area` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否检测危险区域',
  `fall` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否检测摔倒',
  `flame` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否检测明火',
  `smoke` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否检测烟雾/吸烟',
  `punch` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否检测打架',
  `rubbish` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否检测垃圾乱放',
  `ice` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否检测冰面',
  `ebike` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否检测电动车进楼',
  `vehicle` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否检测载具占用车道',
  `wave` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否检测挥手呼救',
  `left_x` INT DEFAULT NULL COMMENT '危险区域左上角X',
  `left_y` INT DEFAULT NULL COMMENT '危险区域左上角Y',
  `right_x` INT DEFAULT NULL COMMENT '危险区域右下角X',
  `right_y` INT DEFAULT NULL COMMENT '危险区域右下角Y',
  `latitude` DECIMAL(10,6) DEFAULT NULL COMMENT '地图纬度',
  `longitude` DECIMAL(10,6) DEFAULT NULL COMMENT '地图经度',
  PRIMARY KEY (`id`),
  KEY `idx_monitor_leader` (`leader`),
  KEY `idx_monitor_running` (`running`),
  KEY `idx_monitor_area` (`area`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='监控设备表';

CREATE TABLE `monitor_recognition_rule` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '识别规则ID',
  `monitor_id` INT NOT NULL COMMENT '关联监控点ID',
  `name` VARCHAR(100) NOT NULL COMMENT '规则名称/事件名称',
  `prompt` TEXT NOT NULL COMMENT '关注内容描述',
  `translated_prompt` TEXT DEFAULT NULL COMMENT '算力节点返回的识别描述',
  `risk_level` TINYINT NOT NULL DEFAULT 2 COMMENT '风险等级：1低，2中，3高',
  `alert_hint` VARCHAR(255) DEFAULT '请及时查看现场情况' COMMENT '告警提示',
  `enabled` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用：1启用，0停用',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_monitor_recognition_rule_monitor_id` (`monitor_id`),
  KEY `idx_monitor_recognition_rule_enabled` (`enabled`),
  CONSTRAINT `fk_monitor_recognition_rule_monitor` FOREIGN KEY (`monitor_id`) REFERENCES `monitor` (`id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='摄像头自定义识别规则表';

CREATE TABLE `alarm_info` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '告警ID',
  `clip_link` VARCHAR(100) DEFAULT NULL COMMENT '报警视频片段ID/链接',
  `monitor_id` INT NOT NULL COMMENT '关联监控点ID',
  `case_type` INT NOT NULL COMMENT '报警类型ID',
  `warning_level` TINYINT NOT NULL DEFAULT 1 COMMENT '告警等级快照：1低，2中，3高',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `status` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '处理状态: 0未处理, 1已处理',
  `processing_content` VARCHAR(255) DEFAULT NULL COMMENT '处理说明',
  PRIMARY KEY (`id`),
  KEY `idx_alarm_monitor_id` (`monitor_id`),
  KEY `idx_alarm_case_type` (`case_type`),
  KEY `idx_alarm_status_time` (`status`, `create_time`),
  KEY `idx_alarm_monitor_status_time` (`monitor_id`, `status`, `create_time`),
  KEY `idx_alarm_case_status_time` (`case_type`, `status`, `create_time`),
  CONSTRAINT `fk_alarm_monitor` FOREIGN KEY (`monitor_id`) REFERENCES `monitor` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT `fk_alarm_case_type` FOREIGN KEY (`case_type`) REFERENCES `case_type_info` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='告警信息表';

CREATE TABLE `system_message` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '消息ID',
  `message` VARCHAR(255) NOT NULL COMMENT '消息内容',
  `receiver_user_id` INT DEFAULT NULL COMMENT '接收用户ID，NULL表示全员可见',
  `timestamp` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '消息时间',
  PRIMARY KEY (`id`),
  KEY `idx_system_message_receiver_user_id` (`receiver_user_id`),
  KEY `idx_system_message_time` (`timestamp`),
  CONSTRAINT `fk_system_message_receiver` FOREIGN KEY (`receiver_user_id`) REFERENCES `user_info` (`id`) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='系统消息表';

CREATE TABLE `alarm_push_record` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '推送记录ID',
  `alarm_id` INT NOT NULL COMMENT '告警ID',
  `user_id` INT NOT NULL COMMENT '接收用户ID',
  `push_type` VARCHAR(20) NOT NULL COMMENT 'ws/unipush/system_message',
  `push_status` VARCHAR(20) NOT NULL COMMENT 'success/fail',
  `push_detail` VARCHAR(255) DEFAULT NULL COMMENT '推送详情',
  `created_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_alarm_user_type` (`alarm_id`, `user_id`, `push_type`),
  KEY `idx_alarm_push_alarm_id` (`alarm_id`),
  KEY `idx_alarm_push_user_id` (`user_id`),
  KEY `idx_alarm_push_created_time` (`created_time`),
  CONSTRAINT `fk_alarm_push_alarm` FOREIGN KEY (`alarm_id`) REFERENCES `alarm_info` (`id`) ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT `fk_alarm_push_user` FOREIGN KEY (`user_id`) REFERENCES `user_info` (`id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='报警推送记录表';

CREATE TABLE `environment_sensor_record` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '环境记录ID',
  `monitor_id` INT NOT NULL COMMENT '关联监控点ID',
  `device_code` VARCHAR(64) DEFAULT NULL COMMENT '传感器设备编号',
  `temperature` FLOAT NOT NULL COMMENT '温度',
  `humidity` FLOAT NOT NULL COMMENT '湿度',
  `pm25` FLOAT NOT NULL COMMENT 'PM2.5',
  `combustible_gas` FLOAT NOT NULL DEFAULT 0 COMMENT '可燃气体浓度',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录时间',
  PRIMARY KEY (`id`),
  KEY `idx_env_sensor_monitor_time` (`monitor_id`, `create_time`),
  CONSTRAINT `fk_env_monitor` FOREIGN KEY (`monitor_id`) REFERENCES `monitor` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='环境传感器记录表';

CREATE TABLE `parking_area_status` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '停车区域状态ID',
  `monitor_id` INT NOT NULL COMMENT '关联监控点ID',
  `device_code` VARCHAR(64) DEFAULT NULL COMMENT '设备编号',
  `area_code` VARCHAR(64) NOT NULL COMMENT '区域编码',
  `area_name` VARCHAR(100) NOT NULL COMMENT '区域名称',
  `total_spaces` INT NOT NULL COMMENT '总车位数',
  `occupied_spaces` INT NOT NULL COMMENT '已占用车位数',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_monitor_area` (`monitor_id`, `area_code`),
  KEY `idx_parking_status_time` (`monitor_id`, `update_time`),
  CONSTRAINT `fk_parking_status_monitor` FOREIGN KEY (`monitor_id`) REFERENCES `monitor` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='停车区域实时状态表';

CREATE TABLE `parking_area_record` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '停车区域记录ID',
  `monitor_id` INT NOT NULL COMMENT '关联监控点ID',
  `device_code` VARCHAR(64) DEFAULT NULL COMMENT '设备编号',
  `batch_no` VARCHAR(64) NOT NULL COMMENT '上报批次号',
  `area_code` VARCHAR(64) NOT NULL COMMENT '区域编码',
  `area_name` VARCHAR(100) NOT NULL COMMENT '区域名称',
  `total_spaces` INT NOT NULL COMMENT '总车位数',
  `occupied_spaces` INT NOT NULL COMMENT '已占用车位数',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录时间',
  PRIMARY KEY (`id`),
  KEY `idx_parking_record_time` (`monitor_id`, `create_time`),
  KEY `idx_parking_record_batch` (`batch_no`),
  CONSTRAINT `fk_parking_record_monitor` FOREIGN KEY (`monitor_id`) REFERENCES `monitor` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='停车区域历史记录表';

CREATE TABLE `parking_traffic_flow_record` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '车流量记录ID',
  `monitor_id` INT NOT NULL COMMENT '关联监控点ID',
  `device_code` VARCHAR(64) DEFAULT NULL COMMENT '设备编号',
  `batch_no` VARCHAR(64) DEFAULT NULL COMMENT '上报批次号',
  `in_count` INT NOT NULL DEFAULT 0 COMMENT '入口车辆数',
  `out_count` INT NOT NULL DEFAULT 0 COMMENT '出口车辆数',
  `net_flow` INT NOT NULL DEFAULT 0 COMMENT '净流入车辆数',
  `total_flow` INT NOT NULL DEFAULT 0 COMMENT '总车流量',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录时间',
  PRIMARY KEY (`id`),
  KEY `idx_parking_flow_monitor_time` (`monitor_id`, `create_time`),
  KEY `idx_parking_flow_batch` (`batch_no`),
  CONSTRAINT `fk_parking_flow_monitor` FOREIGN KEY (`monitor_id`) REFERENCES `monitor` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='停车车流量记录表';

CREATE TABLE `weather_region_config` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '天气区域配置ID',
  `monitor_id` INT NOT NULL COMMENT '关联监控点ID',
  `region_name` VARCHAR(128) NOT NULL COMMENT '区域名称',
  `latitude` DECIMAL(10,6) DEFAULT NULL COMMENT '纬度',
  `longitude` DECIMAL(10,6) DEFAULT NULL COMMENT '经度',
  `timezone` VARCHAR(64) NOT NULL DEFAULT 'Asia/Shanghai' COMMENT '时区',
  `enabled` TINYINT NOT NULL DEFAULT 1 COMMENT '是否启用',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_weather_region_monitor` (`monitor_id`),
  CONSTRAINT `fk_weather_region_monitor` FOREIGN KEY (`monitor_id`) REFERENCES `monitor` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='天气区域配置表';

CREATE TABLE `weather_info` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '天气记录ID',
  `monitor_id` INT NOT NULL COMMENT '关联监控点ID',
  `region_name` VARCHAR(128) DEFAULT NULL COMMENT '区域名称',
  `temperature` FLOAT NOT NULL COMMENT '温度(摄氏度)',
  `humidity` FLOAT NOT NULL COMMENT '湿度(%)',
  `wind_speed` FLOAT DEFAULT NULL COMMENT '风速',
  `latitude` DECIMAL(10,6) DEFAULT NULL COMMENT '纬度',
  `longitude` DECIMAL(10,6) DEFAULT NULL COMMENT '经度',
  `source` VARCHAR(32) NOT NULL DEFAULT 'open-meteo' COMMENT '数据来源',
  `weather` VARCHAR(255) NOT NULL COMMENT '天气状况',
  `weather_code` INT DEFAULT NULL COMMENT '天气编码',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录时间',
  PRIMARY KEY (`id`),
  KEY `idx_weather_monitor_time` (`monitor_id`, `create_time`),
  KEY `idx_weather_create_time` (`create_time`),
  CONSTRAINT `fk_weather_info_monitor` FOREIGN KEY (`monitor_id`) REFERENCES `monitor` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='天气信息表';

CREATE TABLE `device_repair_info` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '报修ID',
  `device_name` VARCHAR(100) NOT NULL COMMENT '设备名称',
  `location` VARCHAR(100) NOT NULL COMMENT '位置',
  `report_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '报修时间',
  `repair_detail` TEXT NOT NULL COMMENT '报修信息详情',
  `publisher` VARCHAR(50) NOT NULL COMMENT '发布者',
  `owner_user_id` INT DEFAULT NULL COMMENT '业主用户ID',
  PRIMARY KEY (`id`),
  KEY `idx_device_repair_report_time` (`report_time`),
  KEY `idx_device_repair_owner_user_id` (`owner_user_id`),
  CONSTRAINT `fk_device_repair_owner` FOREIGN KEY (`owner_user_id`) REFERENCES `user_info` (`id`) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='设备报修信息表';

CREATE TABLE `parking_space_info` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '车位ID',
  `location` VARCHAR(100) NOT NULL COMMENT '车位位置',
  `occupied_vehicle` VARCHAR(100) DEFAULT NULL COMMENT '占用车辆',
  `total_spaces` INT NOT NULL COMMENT '总车位数',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='车位信息表';

CREATE TABLE `visitor_info` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '访客ID',
  `visitor_name` VARCHAR(50) NOT NULL COMMENT '访客姓名',
  `visit_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '到访时间',
  `plate_number` VARCHAR(20) DEFAULT NULL COMMENT '车牌号',
  `owner_user_id` INT DEFAULT NULL COMMENT '业主用户ID',
  PRIMARY KEY (`id`),
  KEY `idx_visitor_visit_time` (`visit_time`),
  KEY `idx_visitor_owner_user_id` (`owner_user_id`),
  CONSTRAINT `fk_visitor_owner` FOREIGN KEY (`owner_user_id`) REFERENCES `user_info` (`id`) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='访客表';
