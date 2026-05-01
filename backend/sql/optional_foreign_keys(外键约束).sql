-- =========================================================
-- 可选外键增强脚本
-- 使用前提:
--   1. 已执行 backend/sql/final_schema.sql。
--   2. alarm_push_record 和 system_message 中不存在无效的 alarm_id/user_id。
-- 说明:
--   这些约束更偏日志/消息完整性，不是项目运行必需。
--   如果你希望删除用户/报警时保留更自由的手动清理能力，可以不执行本脚本。
-- =========================================================

USE `SweatPear`;
SET NAMES utf8mb4;

ALTER TABLE `alarm_push_record`
  ADD CONSTRAINT `fk_alarm_push_alarm`
    FOREIGN KEY (`alarm_id`) REFERENCES `alarm_info` (`id`)
    ON UPDATE CASCADE ON DELETE CASCADE,
  ADD CONSTRAINT `fk_alarm_push_user`
    FOREIGN KEY (`user_id`) REFERENCES `user_info` (`id`)
    ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE `system_message`
  ADD CONSTRAINT `fk_system_message_receiver`
    FOREIGN KEY (`receiver_user_id`) REFERENCES `user_info` (`id`)
    ON UPDATE CASCADE ON DELETE SET NULL;
