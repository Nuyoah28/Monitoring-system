-- Incremental migration for nearby resident push support.
-- Compatible with older MySQL versions that do not support
-- ADD COLUMN IF NOT EXISTS / CREATE INDEX IF NOT EXISTS.

SET @db_name = DATABASE();

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `user_info` ADD COLUMN `is_resident` TINYINT(1) NOT NULL DEFAULT 0 COMMENT ''是否居民用户''',
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
    'ALTER TABLE `user_info` ADD COLUMN `home_area` VARCHAR(50) DEFAULT NULL COMMENT ''常驻区域''',
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
    'ALTER TABLE `user_info` ADD COLUMN `notify_enabled` TINYINT(1) NOT NULL DEFAULT 1 COMMENT ''是否接收告警推送''',
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
    'ALTER TABLE `user_info` ADD COLUMN `push_cid` VARCHAR(128) DEFAULT NULL COMMENT ''UniPush 设备标识''',
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

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `system_message` ADD COLUMN `receiver_user_id` INT DEFAULT NULL COMMENT ''接收用户ID，NULL 表示全员可见''',
    'SELECT 1'
  )
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db_name
    AND TABLE_NAME = 'system_message'
    AND COLUMN_NAME = 'receiver_user_id'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `system_message` ADD INDEX `idx_system_message_receiver_user_id` (`receiver_user_id`)',
    'SELECT 1'
  )
  FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = @db_name
    AND TABLE_NAME = 'system_message'
    AND INDEX_NAME = 'idx_system_message_receiver_user_id'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

CREATE TABLE IF NOT EXISTS `alarm_push_record` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
    `alarm_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    `push_type` VARCHAR(20) NOT NULL COMMENT 'ws/unipush/system_message',
    `push_status` VARCHAR(20) NOT NULL COMMENT 'success/fail',
    `push_detail` VARCHAR(255) DEFAULT NULL,
    `created_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY `uk_alarm_user_type` (`alarm_id`, `user_id`, `push_type`),
    KEY `idx_alarm_id` (`alarm_id`),
    KEY `idx_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
