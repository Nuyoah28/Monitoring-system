-- Owner scope migration for visitor and device repair data.
-- Run on existing databases. Safe to re-run.

SET NAMES utf8mb4;

SET @db_name = DATABASE();

SET @owner_user_id = (
  SELECT `id`
  FROM `user_info`
  WHERE `role` = 1
  ORDER BY `id`
  LIMIT 1
);

SET @owner_user_id = COALESCE(@owner_user_id, 1);

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `visitor_info` ADD COLUMN `owner_user_id` INT DEFAULT NULL COMMENT ''业主用户ID'' AFTER `plate_number`',
    'SELECT 1'
  )
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db_name
    AND TABLE_NAME = 'visitor_info'
    AND COLUMN_NAME = 'owner_user_id'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `visitor_info` ADD INDEX `idx_visitor_owner_user_id` (`owner_user_id`)',
    'SELECT 1'
  )
  FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = @db_name
    AND TABLE_NAME = 'visitor_info'
    AND INDEX_NAME = 'idx_visitor_owner_user_id'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `device_repair_info` ADD COLUMN `owner_user_id` INT DEFAULT NULL COMMENT ''业主用户ID'' AFTER `publisher`',
    'SELECT 1'
  )
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db_name
    AND TABLE_NAME = 'device_repair_info'
    AND COLUMN_NAME = 'owner_user_id'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `device_repair_info` ADD INDEX `idx_device_repair_owner_user_id` (`owner_user_id`)',
    'SELECT 1'
  )
  FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = @db_name
    AND TABLE_NAME = 'device_repair_info'
    AND INDEX_NAME = 'idx_device_repair_owner_user_id'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

UPDATE `visitor_info`
SET `owner_user_id` = COALESCE(`owner_user_id`, @owner_user_id)
WHERE `owner_user_id` IS NULL;

UPDATE `device_repair_info`
SET `owner_user_id` = COALESCE(`owner_user_id`, @owner_user_id),
    `publisher` = COALESCE(`publisher`, (SELECT `user_name` FROM `user_info` WHERE `id` = @owner_user_id))
WHERE `owner_user_id` IS NULL;

SELECT `id`, `visitor_name`, `owner_user_id` FROM `visitor_info` ORDER BY `id`;
SELECT `id`, `device_name`, `publisher`, `owner_user_id` FROM `device_repair_info` ORDER BY `id`;
