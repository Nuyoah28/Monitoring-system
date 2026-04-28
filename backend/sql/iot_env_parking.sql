CREATE TABLE IF NOT EXISTS `environment_record` (
  `id` int NOT NULL AUTO_INCREMENT,
  `monitor_id` int NOT NULL COMMENT '关联监控点ID',
  `device_code` varchar(64) DEFAULT NULL COMMENT 'IoT设备编号',
  `weather` varchar(32) NOT NULL COMMENT '天气状态',
  `temperature` float NOT NULL COMMENT '温度',
  `humidity` float NOT NULL COMMENT '湿度',
  `pm25` float NOT NULL COMMENT 'PM2.5',
  `aqi` int NOT NULL COMMENT 'AQI',
  `create_time` datetime NOT NULL COMMENT '上报时间',
  PRIMARY KEY (`id`),
  KEY `idx_env_monitor_time` (`monitor_id`, `create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='环境数据上报历史表';

CREATE TABLE IF NOT EXISTS `parking_area_status` (
  `id` int NOT NULL AUTO_INCREMENT,
  `monitor_id` int NOT NULL COMMENT '关联监控点ID',
  `device_code` varchar(64) DEFAULT NULL COMMENT 'IoT设备编号',
  `area_code` varchar(64) NOT NULL COMMENT '区域编码',
  `area_name` varchar(100) NOT NULL COMMENT '区域名称',
  `total_spaces` int NOT NULL COMMENT '总车位数',
  `occupied_spaces` int NOT NULL COMMENT '已占用车位数',
  `create_time` datetime NOT NULL COMMENT '首次创建时间',
  `update_time` datetime NOT NULL COMMENT '最近更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_monitor_area` (`monitor_id`, `area_code`),
  KEY `idx_parking_status_time` (`monitor_id`, `update_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='车位区域当前状态表';

CREATE TABLE IF NOT EXISTS `parking_area_record` (
  `id` int NOT NULL AUTO_INCREMENT,
  `monitor_id` int NOT NULL COMMENT '关联监控点ID',
  `device_code` varchar(64) DEFAULT NULL COMMENT 'IoT设备编号',
  `batch_no` varchar(64) NOT NULL COMMENT '同批次上报编号',
  `area_code` varchar(64) NOT NULL COMMENT '区域编码',
  `area_name` varchar(100) NOT NULL COMMENT '区域名称',
  `total_spaces` int NOT NULL COMMENT '总车位数',
  `occupied_spaces` int NOT NULL COMMENT '已占用车位数',
  `create_time` datetime NOT NULL COMMENT '上报时间',
  PRIMARY KEY (`id`),
  KEY `idx_parking_record_time` (`monitor_id`, `create_time`),
  KEY `idx_parking_record_batch` (`batch_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='车位区域历史快照表';
