-- =========================================================
-- User profile fields and relational constraints migration.
-- Run this on an existing SweatPear database. Safe to re-run.
-- =========================================================

SET NAMES utf8mb4;
SET @db_name = DATABASE();

-- user_info.avatar_url
SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `user_info` ADD COLUMN `avatar_url` VARCHAR(255) DEFAULT NULL COMMENT ''头像地址'' AFTER `phone`',
    'SELECT 1'
  )
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db_name
    AND TABLE_NAME = 'user_info'
    AND COLUMN_NAME = 'avatar_url'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- user_info resident / push fields
SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `user_info` ADD COLUMN `is_resident` TINYINT(1) NOT NULL DEFAULT 0 COMMENT ''是否居民用户'' AFTER `role`',
    'SELECT 1'
  )
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db_name
    AND TABLE_NAME = 'user_info'
    AND COLUMN_NAME = 'is_resident'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `user_info` ADD COLUMN `home_area` VARCHAR(50) DEFAULT NULL COMMENT ''常驻区域'' AFTER `is_resident`',
    'SELECT 1'
  )
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db_name
    AND TABLE_NAME = 'user_info'
    AND COLUMN_NAME = 'home_area'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `user_info` ADD COLUMN `notify_enabled` TINYINT(1) NOT NULL DEFAULT 1 COMMENT ''是否接收报警推送'' AFTER `home_area`',
    'SELECT 1'
  )
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db_name
    AND TABLE_NAME = 'user_info'
    AND COLUMN_NAME = 'notify_enabled'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `user_info` ADD COLUMN `push_cid` VARCHAR(128) DEFAULT NULL COMMENT ''UniPush设备标识'' AFTER `notify_enabled`',
    'SELECT 1'
  )
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db_name
    AND TABLE_NAME = 'user_info'
    AND COLUMN_NAME = 'push_cid'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

UPDATE `user_info`
SET `is_resident` = 1
WHERE `role` = 1
  AND (`is_resident` IS NULL OR `is_resident` = 0)
  AND `home_area` IS NOT NULL
  AND `home_area` <> '';

-- monitor latitude / longitude
SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `monitor` ADD COLUMN `latitude` DECIMAL(10,6) DEFAULT NULL COMMENT ''地图纬度'' AFTER `right_y`',
    'SELECT 1'
  )
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db_name
    AND TABLE_NAME = 'monitor'
    AND COLUMN_NAME = 'latitude'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `monitor` ADD COLUMN `longitude` DECIMAL(10,6) DEFAULT NULL COMMENT ''地图经度'' AFTER `latitude`',
    'SELECT 1'
  )
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db_name
    AND TABLE_NAME = 'monitor'
    AND COLUMN_NAME = 'longitude'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Align existing column definitions before adding constraints.
UPDATE `alarm_info`
SET `monitor_id` = 1
WHERE `monitor_id` IS NULL;

ALTER TABLE `alarm_info`
  MODIFY COLUMN `monitor_id` INT NOT NULL COMMENT '关联监控点ID',
  MODIFY COLUMN `processing_content` VARCHAR(255) DEFAULT NULL COMMENT '处理说明';

ALTER TABLE `alarm_push_record`
  MODIFY COLUMN `created_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间';

-- Add missing indexes first.
SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `monitor` ADD INDEX `idx_monitor_leader` (`leader`)',
    'SELECT 1'
  )
  FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = @db_name
    AND TABLE_NAME = 'monitor'
    AND INDEX_NAME = 'idx_monitor_leader'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `monitor` ADD INDEX `idx_monitor_running` (`running`)',
    'SELECT 1'
  )
  FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = @db_name
    AND TABLE_NAME = 'monitor'
    AND INDEX_NAME = 'idx_monitor_running'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `monitor` ADD INDEX `idx_monitor_area` (`area`)',
    'SELECT 1'
  )
  FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = @db_name
    AND TABLE_NAME = 'monitor'
    AND INDEX_NAME = 'idx_monitor_area'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `alarm_info` ADD INDEX `idx_alarm_monitor_id` (`monitor_id`)',
    'SELECT 1'
  )
  FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = @db_name
    AND TABLE_NAME = 'alarm_info'
    AND INDEX_NAME = 'idx_alarm_monitor_id'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `alarm_info` ADD INDEX `idx_alarm_case_type` (`case_type`)',
    'SELECT 1'
  )
  FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = @db_name
    AND TABLE_NAME = 'alarm_info'
    AND INDEX_NAME = 'idx_alarm_case_type'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `alarm_info` ADD INDEX `idx_alarm_status_time` (`status`, `create_time`)',
    'SELECT 1'
  )
  FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = @db_name
    AND TABLE_NAME = 'alarm_info'
    AND INDEX_NAME = 'idx_alarm_status_time'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add foreign keys when missing. These statements assume referenced data is clean.
SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `monitor_recognition_rule` ADD CONSTRAINT `fk_monitor_recognition_rule_monitor` FOREIGN KEY (`monitor_id`) REFERENCES `monitor` (`id`) ON UPDATE CASCADE ON DELETE CASCADE',
    'SELECT 1'
  )
  FROM information_schema.REFERENTIAL_CONSTRAINTS
  WHERE CONSTRAINT_SCHEMA = @db_name
    AND CONSTRAINT_NAME = 'fk_monitor_recognition_rule_monitor'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `alarm_info` ADD CONSTRAINT `fk_alarm_monitor` FOREIGN KEY (`monitor_id`) REFERENCES `monitor` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT',
    'SELECT 1'
  )
  FROM information_schema.REFERENTIAL_CONSTRAINTS
  WHERE CONSTRAINT_SCHEMA = @db_name
    AND CONSTRAINT_NAME = 'fk_alarm_monitor'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `alarm_info` ADD CONSTRAINT `fk_alarm_case_type` FOREIGN KEY (`case_type`) REFERENCES `case_type_info` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT',
    'SELECT 1'
  )
  FROM information_schema.REFERENTIAL_CONSTRAINTS
  WHERE CONSTRAINT_SCHEMA = @db_name
    AND CONSTRAINT_NAME = 'fk_alarm_case_type'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `system_message` ADD CONSTRAINT `fk_system_message_receiver` FOREIGN KEY (`receiver_user_id`) REFERENCES `user_info` (`id`) ON UPDATE CASCADE ON DELETE SET NULL',
    'SELECT 1'
  )
  FROM information_schema.REFERENTIAL_CONSTRAINTS
  WHERE CONSTRAINT_SCHEMA = @db_name
    AND CONSTRAINT_NAME = 'fk_system_message_receiver'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `alarm_push_record` ADD CONSTRAINT `fk_alarm_push_alarm` FOREIGN KEY (`alarm_id`) REFERENCES `alarm_info` (`id`) ON UPDATE CASCADE ON DELETE CASCADE',
    'SELECT 1'
  )
  FROM information_schema.REFERENTIAL_CONSTRAINTS
  WHERE CONSTRAINT_SCHEMA = @db_name
    AND CONSTRAINT_NAME = 'fk_alarm_push_alarm'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `alarm_push_record` ADD CONSTRAINT `fk_alarm_push_user` FOREIGN KEY (`user_id`) REFERENCES `user_info` (`id`) ON UPDATE CASCADE ON DELETE CASCADE',
    'SELECT 1'
  )
  FROM information_schema.REFERENTIAL_CONSTRAINTS
  WHERE CONSTRAINT_SCHEMA = @db_name
    AND CONSTRAINT_NAME = 'fk_alarm_push_user'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `environment_sensor_record` ADD CONSTRAINT `fk_env_monitor` FOREIGN KEY (`monitor_id`) REFERENCES `monitor` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT',
    'SELECT 1'
  )
  FROM information_schema.REFERENTIAL_CONSTRAINTS
  WHERE CONSTRAINT_SCHEMA = @db_name
    AND CONSTRAINT_NAME = 'fk_env_monitor'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `parking_area_status` ADD CONSTRAINT `fk_parking_status_monitor` FOREIGN KEY (`monitor_id`) REFERENCES `monitor` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT',
    'SELECT 1'
  )
  FROM information_schema.REFERENTIAL_CONSTRAINTS
  WHERE CONSTRAINT_SCHEMA = @db_name
    AND CONSTRAINT_NAME = 'fk_parking_status_monitor'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `parking_area_record` ADD CONSTRAINT `fk_parking_record_monitor` FOREIGN KEY (`monitor_id`) REFERENCES `monitor` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT',
    'SELECT 1'
  )
  FROM information_schema.REFERENTIAL_CONSTRAINTS
  WHERE CONSTRAINT_SCHEMA = @db_name
    AND CONSTRAINT_NAME = 'fk_parking_record_monitor'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `weather_region_config` ADD CONSTRAINT `fk_weather_region_monitor` FOREIGN KEY (`monitor_id`) REFERENCES `monitor` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT',
    'SELECT 1'
  )
  FROM information_schema.REFERENTIAL_CONSTRAINTS
  WHERE CONSTRAINT_SCHEMA = @db_name
    AND CONSTRAINT_NAME = 'fk_weather_region_monitor'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `weather_info` ADD CONSTRAINT `fk_weather_info_monitor` FOREIGN KEY (`monitor_id`) REFERENCES `monitor` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT',
    'SELECT 1'
  )
  FROM information_schema.REFERENTIAL_CONSTRAINTS
  WHERE CONSTRAINT_SCHEMA = @db_name
    AND CONSTRAINT_NAME = 'fk_weather_info_monitor'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT 'user profile and constraints migration completed' AS message;
