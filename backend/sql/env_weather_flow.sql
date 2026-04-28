CREATE TABLE IF NOT EXISTS `environment_sensor_record` (
  `id` int NOT NULL AUTO_INCREMENT,
  `monitor_id` int NOT NULL,
  `device_code` varchar(64) DEFAULT NULL,
  `temperature` float NOT NULL,
  `humidity` float NOT NULL,
  `pm25` float NOT NULL,
  `combustible_gas` float NOT NULL DEFAULT 0,
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_env_sensor_monitor_time` (`monitor_id`, `create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `weather_region_config` (
  `id` int NOT NULL AUTO_INCREMENT,
  `monitor_id` int NOT NULL,
  `region_name` varchar(128) NOT NULL,
  `latitude` decimal(10, 6) DEFAULT NULL,
  `longitude` decimal(10, 6) DEFAULT NULL,
  `timezone` varchar(64) NOT NULL DEFAULT 'Asia/Shanghai',
  `enabled` tinyint NOT NULL DEFAULT 1,
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_weather_region_monitor` (`monitor_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `weather_info` (
  `id` int NOT NULL AUTO_INCREMENT,
  `monitor_id` int NOT NULL,
  `region_name` varchar(128) DEFAULT NULL,
  `weather` varchar(32) NOT NULL,
  `weather_code` int DEFAULT NULL,
  `temperature` float NOT NULL,
  `humidity` float NOT NULL,
  `wind_speed` float DEFAULT NULL,
  `latitude` decimal(10, 6) DEFAULT NULL,
  `longitude` decimal(10, 6) DEFAULT NULL,
  `source` varchar(32) NOT NULL DEFAULT 'open-meteo',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_weather_monitor_time` (`monitor_id`, `create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

SET @db_name = DATABASE();

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `weather_info` ADD COLUMN `region_name` varchar(128) DEFAULT NULL AFTER `monitor_id`',
    'SELECT 1'
  )
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db_name
    AND TABLE_NAME = 'weather_info'
    AND COLUMN_NAME = 'region_name'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `weather_info` ADD COLUMN `weather_code` int DEFAULT NULL AFTER `weather`',
    'SELECT 1'
  )
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db_name
    AND TABLE_NAME = 'weather_info'
    AND COLUMN_NAME = 'weather_code'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `weather_info` ADD COLUMN `wind_speed` float DEFAULT NULL AFTER `humidity`',
    'SELECT 1'
  )
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db_name
    AND TABLE_NAME = 'weather_info'
    AND COLUMN_NAME = 'wind_speed'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `weather_info` ADD COLUMN `latitude` decimal(10, 6) DEFAULT NULL AFTER `wind_speed`',
    'SELECT 1'
  )
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db_name
    AND TABLE_NAME = 'weather_info'
    AND COLUMN_NAME = 'latitude'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `weather_info` ADD COLUMN `longitude` decimal(10, 6) DEFAULT NULL AFTER `latitude`',
    'SELECT 1'
  )
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db_name
    AND TABLE_NAME = 'weather_info'
    AND COLUMN_NAME = 'longitude'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `weather_info` ADD COLUMN `source` varchar(32) NOT NULL DEFAULT ''open-meteo'' AFTER `longitude`',
    'SELECT 1'
  )
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db_name
    AND TABLE_NAME = 'weather_info'
    AND COLUMN_NAME = 'source'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `environment_sensor_record` ADD COLUMN `combustible_gas` float NOT NULL DEFAULT 0 AFTER `pm25`',
    'SELECT 1'
  )
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db_name
    AND TABLE_NAME = 'environment_sensor_record'
    AND COLUMN_NAME = 'combustible_gas'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Optional migration from the old table:
-- INSERT INTO `environment_sensor_record`
--   (`monitor_id`, `device_code`, `temperature`, `humidity`, `pm25`, `combustible_gas`, `create_time`)
-- SELECT `monitor_id`, `device_code`, `temperature`, `humidity`, `pm25`, 0, `create_time`
-- FROM `environment_record`;
