-- =========================
-- Monitoring System backend schema (MySQL 8)
-- =========================

CREATE DATABASE IF NOT EXISTS `SweatPear`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_general_ci;

USE `SweatPear`;

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `alarm_push_record`;
DROP TABLE IF EXISTS `system_message`;
DROP TABLE IF EXISTS `weather_info`;
DROP TABLE IF EXISTS `alarm_info`;
DROP TABLE IF EXISTS `visitor_info`;
DROP TABLE IF EXISTS `parking_space_info`;
DROP TABLE IF EXISTS `device_repair_info`;
DROP TABLE IF EXISTS `monitor`;
DROP TABLE IF EXISTS `case_type_info`;
DROP TABLE IF EXISTS `user_info`;

SET FOREIGN_KEY_CHECKS = 1;

-- 用户
CREATE TABLE `user_info` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_name` VARCHAR(255) NOT NULL,
  `password` VARCHAR(255) NOT NULL,
  `phone` VARCHAR(255) DEFAULT NULL,
  `role` INT NOT NULL,
  `is_resident` TINYINT(1) NOT NULL DEFAULT 0,
  `home_area` VARCHAR(50) DEFAULT NULL,
  `notify_enabled` TINYINT(1) NOT NULL DEFAULT 1,
  `push_cid` VARCHAR(128) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 案件类型
CREATE TABLE `case_type_info` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `case_type_name` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 监控
CREATE TABLE `monitor` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(50) NOT NULL,
  `area` VARCHAR(50) DEFAULT NULL,
  `leader` VARCHAR(30) DEFAULT NULL,
  `alarm_cnt` INT DEFAULT 0,
  `stream_link` VARCHAR(255) DEFAULT NULL,
  `running` TINYINT(1) DEFAULT 0,
  `danger_area` TINYINT(1) DEFAULT 0,
  `fall` TINYINT(1) DEFAULT 0,
  `flame` TINYINT(1) DEFAULT 0,
  `smoke` TINYINT(1) DEFAULT 0,
  `punch` TINYINT(1) DEFAULT 0,
  `rubbish` TINYINT(1) DEFAULT 0,
  `ice` TINYINT(1) DEFAULT 0,
  `ebike` TINYINT(1) DEFAULT 0,
  `vehicle` TINYINT(1) DEFAULT 0,
  `wave` TINYINT(1) DEFAULT 0,
  `left_x` INT DEFAULT NULL,
  `left_y` INT DEFAULT NULL,
  `right_x` INT DEFAULT NULL,
  `right_y` INT DEFAULT NULL,
  `latitude` DOUBLE DEFAULT NULL,
  `longitude` DOUBLE DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 告警
CREATE TABLE `alarm_info` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `clip_link` VARCHAR(100) DEFAULT NULL,
  `monitor_id` INT DEFAULT NULL,
  `case_type` INT NOT NULL,
  `warning_level` INT NOT NULL DEFAULT 1,
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` TINYINT(1) NOT NULL DEFAULT 0,
  `processing_content` VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_alarm_monitor_id` (`monitor_id`),
  KEY `idx_alarm_case_type` (`case_type`),
  KEY `idx_alarm_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 天气
CREATE TABLE `weather_info` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `monitor_id` INT NOT NULL,
  `temperature` FLOAT NOT NULL,
  `humidity` FLOAT NOT NULL,
  `weather` VARCHAR(255) NOT NULL,
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_monitor_id` (`monitor_id`),
  KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 系统消息
CREATE TABLE `system_message` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `message` VARCHAR(255) NOT NULL,
  `receiver_user_id` INT DEFAULT NULL,
  `timestamp` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_system_message_receiver_user_id` (`receiver_user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 推送记录
CREATE TABLE `alarm_push_record` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `alarm_id` INT NOT NULL,
  `user_id` INT NOT NULL,
  `push_type` VARCHAR(20) NOT NULL,
  `push_status` VARCHAR(20) NOT NULL,
  `push_detail` VARCHAR(255) DEFAULT NULL,
  `created_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_alarm_user_type` (`alarm_id`,`user_id`,`push_type`),
  KEY `idx_alarm_id` (`alarm_id`),
  KEY `idx_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 设备报修
CREATE TABLE `device_repair_info` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `device_name` VARCHAR(100) NOT NULL,
  `location` VARCHAR(100) NOT NULL,
  `report_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `repair_detail` TEXT NOT NULL,
  `publisher` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 车位
CREATE TABLE `parking_space_info` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `location` VARCHAR(100) NOT NULL,
  `occupied_vehicle` VARCHAR(100) DEFAULT NULL,
  `total_spaces` INT NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 访客
CREATE TABLE `visitor_info` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `visitor_name` VARCHAR(50) NOT NULL,
  `visit_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `plate_number` VARCHAR(20) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 12类事件（和当前后端能力映射一致）
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
