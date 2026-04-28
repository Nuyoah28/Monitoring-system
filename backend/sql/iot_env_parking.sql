CREATE TABLE IF NOT EXISTS `environment_sensor_record` (
  `id` int NOT NULL AUTO_INCREMENT,
  `monitor_id` int NOT NULL,
  `device_code` varchar(64) DEFAULT NULL,
  `temperature` float NOT NULL,
  `humidity` float NOT NULL,
  `pm25` float NOT NULL,
  `combustible_gas` float NOT NULL DEFAULT 0,
  `create_time` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_env_monitor_time` (`monitor_id`, `create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `parking_area_status` (
  `id` int NOT NULL AUTO_INCREMENT,
  `monitor_id` int NOT NULL,
  `device_code` varchar(64) DEFAULT NULL,
  `area_code` varchar(64) NOT NULL,
  `area_name` varchar(100) NOT NULL,
  `total_spaces` int NOT NULL,
  `occupied_spaces` int NOT NULL,
  `create_time` datetime NOT NULL,
  `update_time` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_monitor_area` (`monitor_id`, `area_code`),
  KEY `idx_parking_status_time` (`monitor_id`, `update_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `parking_area_record` (
  `id` int NOT NULL AUTO_INCREMENT,
  `monitor_id` int NOT NULL,
  `device_code` varchar(64) DEFAULT NULL,
  `batch_no` varchar(64) NOT NULL,
  `area_code` varchar(64) NOT NULL,
  `area_name` varchar(100) NOT NULL,
  `total_spaces` int NOT NULL,
  `occupied_spaces` int NOT NULL,
  `create_time` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_parking_record_time` (`monitor_id`, `create_time`),
  KEY `idx_parking_record_batch` (`batch_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
