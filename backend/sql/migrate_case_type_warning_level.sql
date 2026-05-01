-- =========================================================
-- case_type_info 告警等级与启用状态迁移脚本
-- 适用: Navicat / MySQL 8.0+
-- 说明:
--   1. 给已有数据库执行，不删表、不重建库。
--   2. 执行前请先在 Navicat 选中项目数据库。
--   3. 执行后 case_type_info 成为告警默认等级配置来源。
-- =========================================================

SET NAMES utf8mb4;

SET @schema_name = DATABASE();

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `case_type_info` ADD COLUMN `warning_level` TINYINT NOT NULL DEFAULT 1 COMMENT ''默认告警等级：1低，2中，3高'' AFTER `case_type_name`',
    'SELECT ''case_type_info.warning_level already exists'' AS message'
  )
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = @schema_name
    AND TABLE_NAME = 'case_type_info'
    AND COLUMN_NAME = 'warning_level'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `case_type_info` ADD COLUMN `enabled` TINYINT(1) NOT NULL DEFAULT 1 COMMENT ''是否启用：1启用，0隐藏/停用'' AFTER `warning_level`',
    'SELECT ''case_type_info.enabled already exists'' AS message'
  )
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = @schema_name
    AND TABLE_NAME = 'case_type_info'
    AND COLUMN_NAME = 'enabled'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `case_type_info` ADD INDEX `idx_case_type_enabled` (`enabled`)',
    'SELECT ''case_type_info.idx_case_type_enabled already exists'' AS message'
  )
  FROM INFORMATION_SCHEMA.STATISTICS
  WHERE TABLE_SCHEMA = @schema_name
    AND TABLE_NAME = 'case_type_info'
    AND INDEX_NAME = 'idx_case_type_enabled'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

INSERT INTO `case_type_info` (`id`, `case_type_name`, `warning_level`, `enabled`) VALUES
  (1, '进入危险区域', 2, 1),
  (2, '烟雾', 3, 1),
  (3, '区域停留', 1, 1),
  (4, '摔倒', 3, 1),
  (5, '明火', 3, 1),
  (6, '吸烟', 1, 0),
  (7, '打架', 3, 1),
  (8, '垃圾乱放', 1, 1),
  (9, '冰面', 1, 0),
  (10, '电动车进楼', 2, 1),
  (11, '载具占用车道', 2, 1),
  (12, '挥手呼救', 3, 1)
ON DUPLICATE KEY UPDATE
  `case_type_name` = VALUES(`case_type_name`),
  `warning_level` = VALUES(`warning_level`),
  `enabled` = VALUES(`enabled`);

UPDATE `case_type_info`
SET `enabled` = 0
WHERE `id` IN (6, 9);

UPDATE `alarm_info` a
INNER JOIN `case_type_info` c ON a.`case_type` = c.`id`
SET a.`warning_level` = c.`warning_level`;

SELECT * FROM `case_type_info` ORDER BY `id`;

SELECT `case_type`, `warning_level`, COUNT(*) AS `cnt`
FROM `alarm_info`
GROUP BY `case_type`, `warning_level`
ORDER BY `case_type`, `warning_level`;
