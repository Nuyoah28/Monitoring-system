-- 为每个摄像头保存自定义识别规则/关注内容
-- 执行时机：升级现有数据库时执行一次

CREATE TABLE IF NOT EXISTS `monitor_recognition_rule` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '识别规则ID',
  `monitor_id` INT NOT NULL COMMENT '关联监控点ID',
  `name` VARCHAR(100) NOT NULL COMMENT '规则名称/事件名称',
  `prompt` TEXT NOT NULL COMMENT '关注内容描述',
  `translated_prompt` TEXT DEFAULT NULL COMMENT '算力节点返回的识别描述',
  `risk_level` TINYINT NOT NULL DEFAULT 2 COMMENT '风险等级：1低，2中，3高',
  `alert_hint` VARCHAR(255) DEFAULT '请及时查看现场情况' COMMENT '告警提示',
  `enabled` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用：1启用，0停用',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_monitor_recognition_rule_monitor_id` (`monitor_id`),
  KEY `idx_monitor_recognition_rule_enabled` (`enabled`),
  CONSTRAINT `fk_monitor_recognition_rule_monitor` FOREIGN KEY (`monitor_id`) REFERENCES `monitor` (`id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='摄像头自定义识别规则表';
