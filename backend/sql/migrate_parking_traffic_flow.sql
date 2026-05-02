-- =========================================================
-- 停车车流量统计增量迁移脚本
-- 适用: 已有 SweatPear 数据库
-- 说明:
--   1. 给新增的车位检测算法保存入口/出口车流量。
--   2. 可直接在当前数据库执行；不会删除已有数据。
--   3. final_schema.sql 已包含这张表，新环境不用重复执行本文件。
-- =========================================================

USE `SweatPear`;

CREATE TABLE IF NOT EXISTS `parking_traffic_flow_record` (
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
  KEY `idx_parking_flow_batch` (`batch_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='停车车流量记录表';

SET @fk_exists := (
  SELECT COUNT(*)
  FROM information_schema.TABLE_CONSTRAINTS
  WHERE CONSTRAINT_SCHEMA = DATABASE()
    AND TABLE_NAME = 'parking_traffic_flow_record'
    AND CONSTRAINT_NAME = 'fk_parking_flow_monitor'
);

SET @sql := IF(
  @fk_exists = 0,
  'ALTER TABLE `parking_traffic_flow_record` ADD CONSTRAINT `fk_parking_flow_monitor` FOREIGN KEY (`monitor_id`) REFERENCES `monitor` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

INSERT INTO `parking_traffic_flow_record`
  (`id`, `monitor_id`, `device_code`, `batch_no`, `in_count`, `out_count`, `net_flow`, `total_flow`, `create_time`)
SELECT *
FROM (
  SELECT 1 AS `id`, 1 AS `monitor_id`, 'PARK-EAST-01' AS `device_code`, 'flow-east-01' AS `batch_no`, 18 AS `in_count`, 10 AS `out_count`, 8 AS `net_flow`, 28 AS `total_flow`, DATE_SUB(NOW(), INTERVAL 12 HOUR) AS `create_time`
  UNION ALL SELECT 2, 1, 'PARK-EAST-01', 'flow-east-02', 26, 18, 8, 44, DATE_SUB(NOW(), INTERVAL 8 HOUR)
  UNION ALL SELECT 3, 1, 'PARK-EAST-01', 'flow-east-03', 21, 24, -3, 45, DATE_SUB(NOW(), INTERVAL 5 HOUR)
  UNION ALL SELECT 4, 1, 'PARK-EAST-01', 'flow-east-04', 38, 27, 11, 65, DATE_SUB(NOW(), INTERVAL 2 HOUR)
  UNION ALL SELECT 5, 1, 'PARK-EAST-01', 'flow-east-05', 12, 9, 3, 21, DATE_SUB(NOW(), INTERVAL 20 MINUTE)
  UNION ALL SELECT 6, 2, 'PARK-WEST-01', 'flow-west-01', 14, 9, 5, 23, DATE_SUB(NOW(), INTERVAL 10 HOUR)
  UNION ALL SELECT 7, 2, 'PARK-WEST-01', 'flow-west-02', 19, 16, 3, 35, DATE_SUB(NOW(), INTERVAL 5 HOUR)
  UNION ALL SELECT 8, 2, 'PARK-WEST-01', 'flow-west-03', 9, 11, -2, 20, DATE_SUB(NOW(), INTERVAL 35 MINUTE)
) seed
WHERE NOT EXISTS (
  SELECT 1 FROM `parking_traffic_flow_record` LIMIT 1
);

ALTER TABLE `parking_traffic_flow_record` AUTO_INCREMENT = 9;
