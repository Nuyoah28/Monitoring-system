-- 近邻居民报警推送改造（增量脚本）
-- 执行环境：MySQL 8+

-- 1) user_info：补充居民推送所需字段
ALTER TABLE user_info
    ADD COLUMN IF NOT EXISTS is_resident TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否居民用户',
    ADD COLUMN IF NOT EXISTS home_area VARCHAR(50) DEFAULT NULL COMMENT '常驻区域',
    ADD COLUMN IF NOT EXISTS notify_enabled TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否接收报警推送',
    ADD COLUMN IF NOT EXISTS push_cid VARCHAR(128) DEFAULT NULL COMMENT 'UniPush 设备标识';

-- 2) system_message：支持“定向给某个用户”的通知
ALTER TABLE system_message
    ADD COLUMN IF NOT EXISTS receiver_user_id INT DEFAULT NULL COMMENT '接收用户ID，NULL 表示全员可见';

CREATE INDEX IF NOT EXISTS idx_system_message_receiver_user_id
    ON system_message(receiver_user_id);

-- 3) 推送记录表：便于审计和防重
CREATE TABLE IF NOT EXISTS alarm_push_record (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    alarm_id INT NOT NULL,
    user_id INT NOT NULL,
    push_type VARCHAR(20) NOT NULL COMMENT 'ws/unipush/system_message',
    push_status VARCHAR(20) NOT NULL COMMENT 'success/fail',
    push_detail VARCHAR(255) DEFAULT NULL,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_alarm_user_type (alarm_id, user_id, push_type),
    KEY idx_alarm_id (alarm_id),
    KEY idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
