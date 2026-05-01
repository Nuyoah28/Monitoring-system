-- =========================================================
-- Monitoring System 后端数据库最终建库脚本
-- 适用: MySQL 8.0+ / MySQL 9.x
-- 说明:
--   1. 执行后会重建 SweatPear 库下的项目表，请勿在有重要数据的库中直接执行。
--   2. 该脚本包含项目运行所需的完整表结构、基础用户、监控点、报警类型、演示报警和天气数据。
--   3. 主脚本只加入低风险核心外键，保证告警、环境、车位、天气数据必须挂到真实监控点位。
-- =========================================================

CREATE DATABASE IF NOT EXISTS `SweatPear`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_general_ci;

USE `SweatPear`;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `alarm_push_record`;
DROP TABLE IF EXISTS `system_message`;
DROP TABLE IF EXISTS `parking_area_record`;
DROP TABLE IF EXISTS `parking_area_status`;
DROP TABLE IF EXISTS `environment_sensor_record`;
DROP TABLE IF EXISTS `weather_info`;
DROP TABLE IF EXISTS `weather_region_config`;
DROP TABLE IF EXISTS `alarm_info`;
DROP TABLE IF EXISTS `visitor_info`;
DROP TABLE IF EXISTS `parking_space_info`;
DROP TABLE IF EXISTS `device_repair_info`;
DROP TABLE IF EXISTS `monitor`;
DROP TABLE IF EXISTS `case_type_info`;
DROP TABLE IF EXISTS `user_info`;

SET FOREIGN_KEY_CHECKS = 1;

-- =========================
-- 用户表
-- role: 0 管理员, 1 普通用户/负责人/居民
-- =========================
CREATE TABLE `user_info` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `user_name` VARCHAR(255) NOT NULL COMMENT '用户名',
  `password` VARCHAR(255) NOT NULL COMMENT '密码MD5值',
  `phone` VARCHAR(255) DEFAULT NULL COMMENT '手机号',
  `role` INT NOT NULL COMMENT '角色: 0管理员, 1普通用户',
  `is_resident` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否居民用户',
  `home_area` VARCHAR(50) DEFAULT NULL COMMENT '常驻区域',
  `notify_enabled` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否接收报警推送',
  `push_cid` VARCHAR(128) DEFAULT NULL COMMENT 'UniPush设备标识',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_name` (`user_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='用户表';

-- =========================
-- 报警类型表
-- id 必须与算法端 warningList 索引 + 1 保持一致。
-- =========================
CREATE TABLE `case_type_info` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '报警类型ID',
  `case_type_name` VARCHAR(255) NOT NULL COMMENT '报警类型名称',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_case_type_name` (`case_type_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='报警类型表';

-- =========================
-- 监控设备表
-- leader 当前按 user_info.user_name 文本匹配，暂不做物理外键。
-- =========================
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
  `latitude` DECIMAL(10,6) DEFAULT NULL COMMENT '地图纬度，当前后端实体未直接使用，预留',
  `longitude` DECIMAL(10,6) DEFAULT NULL COMMENT '地图经度，当前后端实体未直接使用，预留',
  PRIMARY KEY (`id`),
  KEY `idx_monitor_leader` (`leader`),
  KEY `idx_monitor_running` (`running`),
  KEY `idx_monitor_area` (`area`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='监控设备表';

-- =========================
-- 告警信息表
-- status: 0 未处理, 1 已处理
-- =========================
CREATE TABLE `alarm_info` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '告警ID',
  `clip_link` VARCHAR(100) DEFAULT NULL COMMENT '报警视频片段ID/链接',
  `monitor_id` INT NOT NULL COMMENT '关联监控点ID',
  `case_type` INT NOT NULL COMMENT '报警类型ID',
  `warning_level` INT NOT NULL DEFAULT 1 COMMENT '告警等级',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `status` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '处理状态: 0未处理, 1已处理',
  `processing_content` VARCHAR(255) DEFAULT NULL COMMENT '处理说明',
  PRIMARY KEY (`id`),
  KEY `idx_alarm_monitor_id` (`monitor_id`),
  KEY `idx_alarm_case_type` (`case_type`),
  KEY `idx_alarm_status_time` (`status`, `create_time`),
  KEY `idx_alarm_monitor_status_time` (`monitor_id`, `status`, `create_time`),
  KEY `idx_alarm_case_status_time` (`case_type`, `status`, `create_time`),
  CONSTRAINT `fk_alarm_monitor`
    FOREIGN KEY (`monitor_id`) REFERENCES `monitor` (`id`)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT `fk_alarm_case_type`
    FOREIGN KEY (`case_type`) REFERENCES `case_type_info` (`id`)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='告警信息表';

-- =========================
-- 系统消息表
-- receiver_user_id 为 NULL 表示全员可见。
-- 该字段外键放在 optional_foreign_keys.sql 中，避免影响手动广播消息。
-- =========================
CREATE TABLE `system_message` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '消息ID',
  `message` VARCHAR(255) NOT NULL COMMENT '消息内容',
  `receiver_user_id` INT DEFAULT NULL COMMENT '接收用户ID，NULL表示全员可见',
  `timestamp` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '消息时间',
  PRIMARY KEY (`id`),
  KEY `idx_system_message_receiver_user_id` (`receiver_user_id`),
  KEY `idx_system_message_time` (`timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='系统消息表';

-- =========================
-- 报警推送记录表
-- 推送记录属于日志/审计表，外键放在 optional_foreign_keys.sql 中。
-- =========================
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
  KEY `idx_alarm_push_created_time` (`created_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='报警推送记录表';

-- =========================
-- 环境传感器记录表
-- =========================
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
  CONSTRAINT `fk_env_monitor`
    FOREIGN KEY (`monitor_id`) REFERENCES `monitor` (`id`)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='环境传感器记录表';

-- =========================
-- 停车区域实时状态表
-- =========================
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
  CONSTRAINT `fk_parking_status_monitor`
    FOREIGN KEY (`monitor_id`) REFERENCES `monitor` (`id`)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='停车区域实时状态表';

-- =========================
-- 停车区域历史记录表
-- =========================
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
  CONSTRAINT `fk_parking_record_monitor`
    FOREIGN KEY (`monitor_id`) REFERENCES `monitor` (`id`)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='停车区域历史记录表';

-- =========================
-- 天气区域配置表
-- =========================
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
  CONSTRAINT `fk_weather_region_monitor`
    FOREIGN KEY (`monitor_id`) REFERENCES `monitor` (`id`)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='天气区域配置表';

-- =========================
-- 天气信息表
-- =========================
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
  CONSTRAINT `fk_weather_info_monitor`
    FOREIGN KEY (`monitor_id`) REFERENCES `monitor` (`id`)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='天气信息表';

-- =========================
-- 设备报修信息表
-- =========================
CREATE TABLE `device_repair_info` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '报修ID',
  `device_name` VARCHAR(100) NOT NULL COMMENT '设备名称',
  `location` VARCHAR(100) NOT NULL COMMENT '位置',
  `report_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '报修时间',
  `repair_detail` TEXT NOT NULL COMMENT '报修信息详情',
  `publisher` VARCHAR(50) NOT NULL COMMENT '发布者',
  PRIMARY KEY (`id`),
  KEY `idx_device_repair_report_time` (`report_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='设备报修信息表';

-- =========================
-- 车位信息表
-- =========================
CREATE TABLE `parking_space_info` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '车位ID',
  `location` VARCHAR(100) NOT NULL COMMENT '车位位置',
  `occupied_vehicle` VARCHAR(100) DEFAULT NULL COMMENT '占用车辆',
  `total_spaces` INT NOT NULL COMMENT '总车位数',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='车位信息表';

-- =========================
-- 访客表
-- =========================
CREATE TABLE `visitor_info` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '访客ID',
  `visitor_name` VARCHAR(50) NOT NULL COMMENT '访客姓名',
  `visit_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '到访时间',
  `plate_number` VARCHAR(20) DEFAULT NULL COMMENT '车牌号',
  PRIMARY KEY (`id`),
  KEY `idx_visitor_visit_time` (`visit_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='访客表';

-- =========================================================
-- 基础数据
-- 默认登录密码: 123456
-- 密码哈希规则: MD5(明文密码 + 'HuaWuWin!')
-- =========================================================
INSERT INTO `user_info`
  (`id`, `user_name`, `password`, `phone`, `role`, `is_resident`, `home_area`, `notify_enabled`, `push_cid`)
VALUES
  (1, 'root', '42f641872ae4070ed059696b1df93394', '000000', 0, 0, NULL, 1, NULL),
  (2, 'zbw',  '42f641872ae4070ed059696b1df93394', '111111', 1, 0, NULL, 1, NULL),
  (3, 'aaa',  '42f641872ae4070ed059696b1df93394', '13800138000', 1, 1, '小区东门街道', 1, NULL),
  (4, 'bbb',  '42f641872ae4070ed059696b1df93394', '13900139000', 1, 0, NULL, 1, NULL);

INSERT INTO `case_type_info` (`id`, `case_type_name`) VALUES
  (1, '进入危险区域'),
  (2, '烟雾'),
  (3, '区域停留'),
  (4, '摔倒'),
  (5, '明火'),
  (6, '吸烟'),
  (7, '打架'),
  (8, '垃圾乱放'),
  (9, '冰面'),
  (10, '电动车进楼'),
  (11, '载具占用车道'),
  (12, '挥手呼救');

INSERT INTO `monitor`
  (`id`, `name`, `area`, `leader`, `alarm_cnt`, `stream_link`, `running`, `danger_area`, `fall`, `flame`, `smoke`, `punch`, `rubbish`, `ice`, `ebike`, `vehicle`, `wave`, `left_x`, `left_y`, `right_x`, `right_y`, `latitude`, `longitude`)
VALUES
  (1, '小区东门街道摄像头', '小区东门街道', 'aaa', 3, 'rtmp://example.com/street1', 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 100, 100, 500, 500, 39.904200, 116.407400),
  (2, '小区西门街道摄像头', '小区西门街道', 'bbb', 2, 'rtmp://example.com/street2', 1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 150, 150, 550, 550, 39.904800, 116.401900),
  (3, '3号楼1单元门口摄像头', '3号楼1单元门口', 'aaa', 1, 'rtmp://example.com/entrance1', 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 200, 200, 600, 600, 39.903600, 116.409000),
  (4, '5号楼2单元门口摄像头', '5号楼2单元门口', 'aaa', 5, 'rtmp://example.com/entrance2', 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 250, 250, 650, 650, 39.902900, 116.410500),
  (5, '2号楼电梯内摄像头', '2号楼电梯内', 'aaa', 1, 'rtmp://example.com/elevator1', 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 300, 300, 700, 700, 39.905300, 116.406500),
  (6, '4号楼楼道摄像头', '4号楼楼道', 'bbb', 0, 'rtmp://example.com/hallway1', 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 350, 350, 750, 750, 39.906000, 116.408100),
  (7, '7号楼南门摄像头', '7号楼南门', 'aaa', 0, 'http://172.20.10.2:8848/video/003.flv', 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 100, 100, 500, 500, 39.901800, 116.405200);

INSERT INTO `alarm_info`
  (`id`, `clip_link`, `monitor_id`, `case_type`, `warning_level`, `create_time`, `status`, `processing_content`)
VALUES
  (1,  'xS5hpPA89A',       4, 3, 4, '2023-09-22 22:38:12', 0, NULL),
  (2,  'Hm7tG6BzyJ',       2, 6, 2, '2023-09-26 14:30:15', 0, NULL),
  (3,  '4okMFqZteg',       4, 3, 3, '2023-09-22 17:23:09', 0, NULL),
  (4,  '4Sh0DzFWvt',       3, 2, 5, '2023-09-18 12:39:12', 0, NULL),
  (5,  'gtmDGU1EZ7',       2, 4, 1, '2023-09-26 12:53:10', 0, NULL),
  (6,  'iOMh3u4g6z',       5, 5, 4, '2023-09-26 10:52:19', 0, NULL),
  (7,  'Yq3CDS3jx0',       4, 5, 4, '2023-09-28 13:30:29', 1, '已处理'),
  (8,  'dla6wJbiEF',       1, 2, 3, '2023-09-13 12:16:12', 0, NULL),
  (9,  'ECgrl1Sivu',       4, 5, 2, '2023-09-15 03:39:28', 0, NULL),
  (10, 'MeaDx5or3F',       4, 3, 2, '2023-09-25 23:06:03', 1, '已经解决'),
  (11, 'test123',          1, 5, 1, '2026-04-25 11:46:06', 1, '已经处理'),
  (12, 'test-1777465117',  1, 5, 1, '2026-04-29 20:18:37', 0, NULL);

INSERT INTO `system_message` (`id`, `message`, `receiver_user_id`, `timestamp`) VALUES
  (1, '【小区东门街道】发生明火，请注意安全并留意物业通知。', 3, '2026-04-25 11:46:06'),
  (2, '【小区东门街道】发生明火，请注意安全并留意物业通知。', 3, '2026-04-29 20:18:38');

INSERT INTO `weather_info`
  (`id`, `monitor_id`, `region_name`, `temperature`, `humidity`, `wind_speed`, `latitude`, `longitude`, `source`, `weather`, `weather_code`, `create_time`)
VALUES
  (1,  1, NULL, 25.5, 60, NULL, NULL, NULL, 'open-meteo', '多云', NULL, '2023-09-22 10:00:00'),
  (2,  2, NULL, 26.0, 55, NULL, NULL, NULL, 'open-meteo', '多云', NULL, '2023-09-22 11:00:00'),
  (3,  3, NULL, 24.8, 65, NULL, NULL, NULL, 'open-meteo', '小雨', NULL, '2023-09-22 12:00:00'),
  (4,  4, NULL, 27.2, 50, NULL, NULL, NULL, 'open-meteo', '晴', NULL, '2023-09-22 13:00:00'),
  (5,  5, NULL, 28.5, 45, NULL, NULL, NULL, 'open-meteo', '雷阵雨', NULL, '2023-09-22 14:00:00'),
  (6,  1, NULL, 26.8, 58, NULL, NULL, NULL, 'open-meteo', '晴', NULL, '2023-09-22 15:00:00'),
  (7,  2, NULL, 27.5, 52, NULL, NULL, NULL, 'open-meteo', '暴雨', NULL, '2023-09-22 16:00:00'),
  (8,  3, NULL, 25.2, 62, NULL, NULL, NULL, 'open-meteo', '阴', NULL, '2023-09-22 17:00:00'),
  (9,  4, NULL, 28.0, 48, NULL, NULL, NULL, 'open-meteo', '晴', NULL, '2023-09-22 18:00:00'),
  (10, 5, NULL, 29.3, 43, NULL, NULL, NULL, 'open-meteo', '多云', NULL, '2023-09-22 19:00:00'),
  (11, 1, NULL, 26.5, 56, NULL, NULL, NULL, 'open-meteo', '晴', NULL, '2023-09-22 20:00:00'),
  (12, 2, NULL, 27.0, 51, NULL, NULL, NULL, 'open-meteo', '多云', NULL, '2023-09-22 21:00:00'),
  (13, 3, NULL, 24.5, 63, NULL, NULL, NULL, 'open-meteo', '大雨', NULL, '2023-09-22 22:00:00'),
  (14, 4, NULL, 28.5, 47, NULL, NULL, NULL, 'open-meteo', '晴', NULL, '2023-09-22 23:00:00'),
  (15, 5, NULL, 29.8, 42, NULL, NULL, NULL, 'open-meteo', '中雨', NULL, '2023-09-23 00:00:00');

-- 保证后续自增值从现有演示数据之后开始。
ALTER TABLE `user_info` AUTO_INCREMENT = 5;
ALTER TABLE `case_type_info` AUTO_INCREMENT = 13;
ALTER TABLE `monitor` AUTO_INCREMENT = 8;
ALTER TABLE `alarm_info` AUTO_INCREMENT = 13;
ALTER TABLE `system_message` AUTO_INCREMENT = 3;
ALTER TABLE `weather_info` AUTO_INCREMENT = 16;

-- 最终校准监控点报警数量，避免 alarm_cnt 与 alarm_info 真实数量不一致。
UPDATE `monitor` m
LEFT JOIN (
  SELECT `monitor_id`, COUNT(*) AS `cnt`
  FROM `alarm_info`
  GROUP BY `monitor_id`
) a ON m.`id` = a.`monitor_id`
SET m.`alarm_cnt` = COALESCE(a.`cnt`, 0);
