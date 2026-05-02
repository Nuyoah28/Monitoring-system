-- =========================================================
-- Monitoring System 后端数据库最终演示数据脚本
-- 适用: MySQL 8.0+ / Navicat
-- 说明:
--   1. 新环境初始化请先执行 final_schema.sql，再执行本文件。
--   2. 本文件只写入/更新演示数据，不负责建表。
--   3. 本文件尽量可重复执行；固定主键的数据会用 ON DUPLICATE KEY UPDATE 覆盖为演示状态。
--   4. 默认演示账号密码均为 123456。
-- =========================================================

USE `SweatPear`;

SET NAMES utf8mb4;

-- 默认账号：
--   管理端: root / 123456
--   业主端: aaa  / 123456
--   业主端: bbb  / 123456
INSERT INTO `user_info`
  (`id`, `user_name`, `password`, `phone`, `avatar_url`, `role`, `is_resident`, `home_area`, `notify_enabled`, `push_cid`)
VALUES
  (1, 'root', '42f641872ae4070ed059696b1df93394', '000000', NULL, 0, 0, NULL, 1, NULL),
  (2, 'zbw',  '42f641872ae4070ed059696b1df93394', '111111', NULL, 1, 0, NULL, 1, NULL),
  (3, 'aaa',  '42f641872ae4070ed059696b1df93394', '13800138000', NULL, 1, 1, '小区东门街道', 1, NULL),
  (4, 'bbb',  '42f641872ae4070ed059696b1df93394', '13900139000', NULL, 1, 1, '小区西门街道', 1, NULL)
ON DUPLICATE KEY UPDATE
  `user_name` = VALUES(`user_name`),
  `password` = VALUES(`password`),
  `phone` = VALUES(`phone`),
  `avatar_url` = VALUES(`avatar_url`),
  `role` = VALUES(`role`),
  `is_resident` = VALUES(`is_resident`),
  `home_area` = VALUES(`home_area`),
  `notify_enabled` = VALUES(`notify_enabled`),
  `push_cid` = VALUES(`push_cid`);

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

INSERT INTO `monitor`
  (`id`, `name`, `area`, `leader`, `alarm_cnt`, `stream_link`, `running`, `danger_area`, `fall`, `flame`, `smoke`, `punch`, `rubbish`, `ice`, `ebike`, `vehicle`, `wave`, `left_x`, `left_y`, `right_x`, `right_y`, `latitude`, `longitude`)
VALUES
  (1, '小区东门街道摄像头', '小区东门街道', 'aaa', 0, 'rtmp://example.com/street1', 1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1, 100, 100, 500, 500, 39.904200, 116.407400),
  (2, '小区西门街道摄像头', '小区西门街道', 'bbb', 0, 'rtmp://example.com/street2', 1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 150, 150, 550, 550, 39.904800, 116.401900),
  (3, '3号楼1单元门口摄像头', '3号楼1单元门口', 'aaa', 0, 'rtmp://example.com/entrance1', 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 200, 200, 600, 600, 39.903600, 116.409000),
  (4, '5号楼2单元门口摄像头', '5号楼2单元门口', 'aaa', 0, 'rtmp://example.com/entrance2', 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 250, 250, 650, 650, 39.902900, 116.410500),
  (5, '2号楼电梯内摄像头', '2号楼电梯内', 'aaa', 0, 'rtmp://example.com/elevator1', 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 300, 300, 700, 700, 39.905300, 116.406500),
  (6, '4号楼楼道摄像头', '4号楼楼道', 'bbb', 0, 'rtmp://example.com/hallway1', 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 350, 350, 750, 750, 39.906000, 116.408100),
  (7, '7号楼南门摄像头', '7号楼南门', 'aaa', 0, 'http://172.20.10.2:8848/video/003.flv', 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 100, 100, 500, 500, 39.901800, 116.405200)
ON DUPLICATE KEY UPDATE
  `name` = VALUES(`name`),
  `area` = VALUES(`area`),
  `leader` = VALUES(`leader`),
  `stream_link` = VALUES(`stream_link`),
  `running` = VALUES(`running`),
  `danger_area` = VALUES(`danger_area`),
  `fall` = VALUES(`fall`),
  `flame` = VALUES(`flame`),
  `smoke` = VALUES(`smoke`),
  `punch` = VALUES(`punch`),
  `rubbish` = VALUES(`rubbish`),
  `ice` = VALUES(`ice`),
  `ebike` = VALUES(`ebike`),
  `vehicle` = VALUES(`vehicle`),
  `wave` = VALUES(`wave`),
  `left_x` = VALUES(`left_x`),
  `left_y` = VALUES(`left_y`),
  `right_x` = VALUES(`right_x`),
  `right_y` = VALUES(`right_y`),
  `latitude` = VALUES(`latitude`),
  `longitude` = VALUES(`longitude`);

INSERT INTO `monitor_recognition_rule`
  (`id`, `monitor_id`, `name`, `prompt`, `translated_prompt`, `risk_level`, `alert_hint`, `enabled`, `create_time`, `update_time`)
VALUES
  (1, 1, '明火烟雾识别', '重点关注画面中的明火、烟雾和异常燃烧迹象', 'Detect visible fire, smoke, or abnormal burning signs in the scene.', 3, '疑似火情，请立即查看东门街道现场', 1, NOW(), NOW()),
  (2, 1, '电动车进楼', '关注电动车进入楼栋、门厅或消防通道', 'Detect electric bikes entering buildings, lobbies, or fire exits.', 2, '发现电动车违规进入公共区域', 1, NOW(), NOW()),
  (3, 2, '车道占用', '关注车辆长时间占用主通道或消防通道', 'Detect vehicles blocking main lanes or fire lanes.', 2, '疑似车道占用，请安排巡查', 1, NOW(), NOW()),
  (4, 7, '挥手呼救', '关注人员持续挥手、倒地或求助动作', 'Detect waving for help, falling, or emergency gestures.', 3, '疑似人员求助，请尽快处理', 1, NOW(), NOW())
ON DUPLICATE KEY UPDATE
  `monitor_id` = VALUES(`monitor_id`),
  `name` = VALUES(`name`),
  `prompt` = VALUES(`prompt`),
  `translated_prompt` = VALUES(`translated_prompt`),
  `risk_level` = VALUES(`risk_level`),
  `alert_hint` = VALUES(`alert_hint`),
  `enabled` = VALUES(`enabled`),
  `update_time` = VALUES(`update_time`);

INSERT INTO `alarm_info`
  (`id`, `clip_link`, `monitor_id`, `case_type`, `warning_level`, `create_time`, `status`, `processing_content`)
VALUES
  (1,  'demo-fire-001',    1, 5, 3, DATE_SUB(NOW(), INTERVAL 2 HOUR), 0, NULL),
  (2,  'demo-smoke-001',   1, 2, 3, DATE_SUB(NOW(), INTERVAL 5 HOUR), 0, NULL),
  (3,  'demo-stay-001',    4, 3, 1, DATE_SUB(NOW(), INTERVAL 1 DAY), 0, NULL),
  (4,  'demo-fall-001',    3, 4, 3, DATE_SUB(NOW(), INTERVAL 2 DAY), 1, '已联系物业人员现场确认'),
  (5,  'demo-vehicle-001', 2, 11, 2, DATE_SUB(NOW(), INTERVAL 3 DAY), 0, NULL),
  (6,  'demo-ebike-001',   5, 10, 2, DATE_SUB(NOW(), INTERVAL 4 DAY), 1, '已通知业主移车'),
  (7,  'demo-rubbish-001', 1, 8, 1, DATE_SUB(NOW(), INTERVAL 5 DAY), 0, NULL),
  (8,  'demo-wave-001',    7, 12, 3, DATE_SUB(NOW(), INTERVAL 6 DAY), 0, NULL),
  (9,  'demo-fight-001',   6, 7, 3, DATE_SUB(NOW(), INTERVAL 8 DAY), 1, '保安已到场处理'),
  (10, 'demo-fire-002',    4, 5, 3, DATE_SUB(NOW(), INTERVAL 12 DAY), 0, NULL),
  (11, 'demo-smoke-002',   6, 2, 3, DATE_SUB(NOW(), INTERVAL 18 DAY), 1, '误报，已确认'),
  (12, 'demo-stay-002',    2, 3, 1, DATE_SUB(NOW(), INTERVAL 25 DAY), 0, NULL)
ON DUPLICATE KEY UPDATE
  `clip_link` = VALUES(`clip_link`),
  `monitor_id` = VALUES(`monitor_id`),
  `case_type` = VALUES(`case_type`),
  `warning_level` = VALUES(`warning_level`),
  `create_time` = VALUES(`create_time`),
  `status` = VALUES(`status`),
  `processing_content` = VALUES(`processing_content`);

INSERT INTO `system_message` (`id`, `message`, `receiver_user_id`, `timestamp`) VALUES
  (1, '【小区东门街道】发生明火，请注意安全并留意物业通知。', 3, DATE_SUB(NOW(), INTERVAL 2 HOUR)),
  (2, '【小区东门街道】发生烟雾告警，请关闭门窗并等待物业确认。', 3, DATE_SUB(NOW(), INTERVAL 5 HOUR)),
  (3, '【小区西门街道】今日地库车位较紧张，建议错峰出行。', 4, DATE_SUB(NOW(), INTERVAL 1 DAY)),
  (4, '社区将于本周进行消防通道巡检，请勿占用公共通道。', NULL, DATE_SUB(NOW(), INTERVAL 2 DAY))
ON DUPLICATE KEY UPDATE
  `message` = VALUES(`message`),
  `receiver_user_id` = VALUES(`receiver_user_id`),
  `timestamp` = VALUES(`timestamp`);

INSERT INTO `alarm_push_record`
  (`id`, `alarm_id`, `user_id`, `push_type`, `push_status`, `push_detail`, `created_time`)
VALUES
  (1, 1, 1, 'ws', 'success', 'manager_or_admin', DATE_SUB(NOW(), INTERVAL 2 HOUR)),
  (2, 1, 3, 'ws', 'success', 'resident_by_area', DATE_SUB(NOW(), INTERVAL 2 HOUR)),
  (3, 1, 3, 'system_message', 'success', 'resident_by_area', DATE_SUB(NOW(), INTERVAL 2 HOUR)),
  (4, 2, 1, 'ws', 'success', 'manager_or_admin', DATE_SUB(NOW(), INTERVAL 5 HOUR)),
  (5, 2, 3, 'system_message', 'success', 'resident_by_area', DATE_SUB(NOW(), INTERVAL 5 HOUR))
ON DUPLICATE KEY UPDATE
  `alarm_id` = VALUES(`alarm_id`),
  `user_id` = VALUES(`user_id`),
  `push_type` = VALUES(`push_type`),
  `push_status` = VALUES(`push_status`),
  `push_detail` = VALUES(`push_detail`),
  `created_time` = VALUES(`created_time`);

INSERT INTO `weather_region_config`
  (`id`, `monitor_id`, `region_name`, `latitude`, `longitude`, `timezone`, `enabled`, `create_time`, `update_time`)
VALUES
  (1, 1, '小区东门街道', 39.904200, 116.407400, 'Asia/Shanghai', 1, NOW(), NOW()),
  (2, 2, '小区西门街道', 39.904800, 116.401900, 'Asia/Shanghai', 1, NOW(), NOW()),
  (3, 3, '3号楼1单元门口', 39.903600, 116.409000, 'Asia/Shanghai', 1, NOW(), NOW()),
  (4, 4, '5号楼2单元门口', 39.902900, 116.410500, 'Asia/Shanghai', 1, NOW(), NOW()),
  (5, 5, '2号楼电梯内', 39.905300, 116.406500, 'Asia/Shanghai', 1, NOW(), NOW()),
  (6, 6, '4号楼楼道', 39.906000, 116.408100, 'Asia/Shanghai', 1, NOW(), NOW()),
  (7, 7, '7号楼南门', 39.901800, 116.405200, 'Asia/Shanghai', 1, NOW(), NOW())
ON DUPLICATE KEY UPDATE
  `monitor_id` = VALUES(`monitor_id`),
  `region_name` = VALUES(`region_name`),
  `latitude` = VALUES(`latitude`),
  `longitude` = VALUES(`longitude`),
  `timezone` = VALUES(`timezone`),
  `enabled` = VALUES(`enabled`),
  `update_time` = VALUES(`update_time`);

INSERT INTO `weather_info`
  (`id`, `monitor_id`, `region_name`, `temperature`, `humidity`, `wind_speed`, `latitude`, `longitude`, `source`, `weather`, `weather_code`, `create_time`)
VALUES
  (1, 1, '小区东门街道', 25.5, 60, 2.4, 39.904200, 116.407400, 'demo', '多云', 2, DATE_SUB(NOW(), INTERVAL 3 HOUR)),
  (2, 2, '小区西门街道', 26.0, 55, 2.8, 39.904800, 116.401900, 'demo', '晴', 0, DATE_SUB(NOW(), INTERVAL 3 HOUR)),
  (3, 3, '3号楼1单元门口', 24.8, 65, 1.9, 39.903600, 116.409000, 'demo', '小雨', 61, DATE_SUB(NOW(), INTERVAL 4 HOUR)),
  (4, 4, '5号楼2单元门口', 27.2, 50, 2.1, 39.902900, 116.410500, 'demo', '晴', 0, DATE_SUB(NOW(), INTERVAL 5 HOUR)),
  (5, 5, '2号楼电梯内', 28.5, 45, 1.5, 39.905300, 116.406500, 'demo', '多云', 2, DATE_SUB(NOW(), INTERVAL 6 HOUR)),
  (6, 6, '4号楼楼道', 26.8, 58, 2.0, 39.906000, 116.408100, 'demo', '阴', 3, DATE_SUB(NOW(), INTERVAL 7 HOUR)),
  (7, 7, '7号楼南门', 27.5, 52, 2.6, 39.901800, 116.405200, 'demo', '多云', 2, DATE_SUB(NOW(), INTERVAL 8 HOUR))
ON DUPLICATE KEY UPDATE
  `monitor_id` = VALUES(`monitor_id`),
  `region_name` = VALUES(`region_name`),
  `temperature` = VALUES(`temperature`),
  `humidity` = VALUES(`humidity`),
  `wind_speed` = VALUES(`wind_speed`),
  `latitude` = VALUES(`latitude`),
  `longitude` = VALUES(`longitude`),
  `source` = VALUES(`source`),
  `weather` = VALUES(`weather`),
  `weather_code` = VALUES(`weather_code`),
  `create_time` = VALUES(`create_time`);

INSERT INTO `environment_sensor_record`
  (`id`, `monitor_id`, `device_code`, `temperature`, `humidity`, `pm25`, `combustible_gas`, `create_time`)
VALUES
  (1, 1, 'ENV-EAST-01', 24.8, 58, 18, 0, DATE_SUB(NOW(), INTERVAL 22 HOUR)),
  (2, 1, 'ENV-EAST-01', 25.1, 57, 20, 0, DATE_SUB(NOW(), INTERVAL 18 HOUR)),
  (3, 1, 'ENV-EAST-01', 25.6, 55, 24, 1, DATE_SUB(NOW(), INTERVAL 14 HOUR)),
  (4, 1, 'ENV-EAST-01', 26.0, 54, 29, 1, DATE_SUB(NOW(), INTERVAL 10 HOUR)),
  (5, 1, 'ENV-EAST-01', 26.4, 52, 34, 2, DATE_SUB(NOW(), INTERVAL 6 HOUR)),
  (6, 1, 'ENV-EAST-01', 25.9, 56, 27, 1, DATE_SUB(NOW(), INTERVAL 2 HOUR)),
  (7, 2, 'ENV-WEST-01', 24.2, 61, 16, 0, DATE_SUB(NOW(), INTERVAL 22 HOUR)),
  (8, 2, 'ENV-WEST-01', 24.9, 60, 19, 0, DATE_SUB(NOW(), INTERVAL 16 HOUR)),
  (9, 2, 'ENV-WEST-01', 25.3, 58, 23, 1, DATE_SUB(NOW(), INTERVAL 10 HOUR)),
  (10, 2, 'ENV-WEST-01', 25.6, 57, 26, 1, DATE_SUB(NOW(), INTERVAL 3 HOUR)),
  (11, 3, 'ENV-B3-01', 23.8, 63, 14, 0, DATE_SUB(NOW(), INTERVAL 8 HOUR)),
  (12, 4, 'ENV-B5-02', 24.4, 59, 21, 0, DATE_SUB(NOW(), INTERVAL 8 HOUR)),
  (13, 5, 'ENV-ELEV-02', 27.1, 47, 30, 1, DATE_SUB(NOW(), INTERVAL 8 HOUR)),
  (14, 6, 'ENV-HALL-04', 24.7, 62, 22, 0, DATE_SUB(NOW(), INTERVAL 8 HOUR)),
  (15, 7, 'ENV-SOUTH-07', 25.0, 56, 25, 1, DATE_SUB(NOW(), INTERVAL 8 HOUR))
ON DUPLICATE KEY UPDATE
  `monitor_id` = VALUES(`monitor_id`),
  `device_code` = VALUES(`device_code`),
  `temperature` = VALUES(`temperature`),
  `humidity` = VALUES(`humidity`),
  `pm25` = VALUES(`pm25`),
  `combustible_gas` = VALUES(`combustible_gas`),
  `create_time` = VALUES(`create_time`);

INSERT INTO `parking_area_status`
  (`id`, `monitor_id`, `device_code`, `area_code`, `area_name`, `total_spaces`, `occupied_spaces`, `create_time`, `update_time`)
VALUES
  (1, 1, 'PARK-EAST-01', 'A', '地库A区', 56, 33, DATE_SUB(NOW(), INTERVAL 1 DAY), NOW()),
  (2, 1, 'PARK-EAST-01', 'B', '地库B区', 48, 25, DATE_SUB(NOW(), INTERVAL 1 DAY), NOW()),
  (3, 1, 'PARK-EAST-01', 'EAST', '地面东侧', 32, 17, DATE_SUB(NOW(), INTERVAL 1 DAY), NOW()),
  (4, 1, 'PARK-EAST-01', 'WEST', '地面西侧', 28, 19, DATE_SUB(NOW(), INTERVAL 1 DAY), NOW()),
  (5, 2, 'PARK-WEST-01', 'A', '西门地库A区', 44, 21, DATE_SUB(NOW(), INTERVAL 1 DAY), NOW()),
  (6, 2, 'PARK-WEST-01', 'B', '西门地库B区', 36, 24, DATE_SUB(NOW(), INTERVAL 1 DAY), NOW())
ON DUPLICATE KEY UPDATE
  `device_code` = VALUES(`device_code`),
  `area_name` = VALUES(`area_name`),
  `total_spaces` = VALUES(`total_spaces`),
  `occupied_spaces` = VALUES(`occupied_spaces`),
  `update_time` = VALUES(`update_time`);

INSERT INTO `parking_area_record`
  (`id`, `monitor_id`, `device_code`, `batch_no`, `area_code`, `area_name`, `total_spaces`, `occupied_spaces`, `create_time`)
VALUES
  (1, 1, 'PARK-EAST-01', 'demo-east-01', 'A', '地库A区', 56, 27, DATE_SUB(NOW(), INTERVAL 20 HOUR)),
  (2, 1, 'PARK-EAST-01', 'demo-east-01', 'B', '地库B区', 48, 21, DATE_SUB(NOW(), INTERVAL 20 HOUR)),
  (3, 1, 'PARK-EAST-01', 'demo-east-02', 'A', '地库A区', 56, 31, DATE_SUB(NOW(), INTERVAL 16 HOUR)),
  (4, 1, 'PARK-EAST-01', 'demo-east-02', 'B', '地库B区', 48, 24, DATE_SUB(NOW(), INTERVAL 16 HOUR)),
  (5, 1, 'PARK-EAST-01', 'demo-east-03', 'A', '地库A区', 56, 35, DATE_SUB(NOW(), INTERVAL 12 HOUR)),
  (6, 1, 'PARK-EAST-01', 'demo-east-03', 'B', '地库B区', 48, 29, DATE_SUB(NOW(), INTERVAL 12 HOUR)),
  (7, 1, 'PARK-EAST-01', 'demo-east-04', 'A', '地库A区', 56, 38, DATE_SUB(NOW(), INTERVAL 8 HOUR)),
  (8, 1, 'PARK-EAST-01', 'demo-east-04', 'B', '地库B区', 48, 31, DATE_SUB(NOW(), INTERVAL 8 HOUR)),
  (9, 1, 'PARK-EAST-01', 'demo-east-05', 'A', '地库A区', 56, 33, DATE_SUB(NOW(), INTERVAL 4 HOUR)),
  (10, 1, 'PARK-EAST-01', 'demo-east-05', 'B', '地库B区', 48, 25, DATE_SUB(NOW(), INTERVAL 4 HOUR)),
  (11, 2, 'PARK-WEST-01', 'demo-west-01', 'A', '西门地库A区', 44, 18, DATE_SUB(NOW(), INTERVAL 20 HOUR)),
  (12, 2, 'PARK-WEST-01', 'demo-west-01', 'B', '西门地库B区', 36, 17, DATE_SUB(NOW(), INTERVAL 20 HOUR)),
  (13, 2, 'PARK-WEST-01', 'demo-west-02', 'A', '西门地库A区', 44, 22, DATE_SUB(NOW(), INTERVAL 12 HOUR)),
  (14, 2, 'PARK-WEST-01', 'demo-west-02', 'B', '西门地库B区', 36, 23, DATE_SUB(NOW(), INTERVAL 12 HOUR)),
  (15, 2, 'PARK-WEST-01', 'demo-west-03', 'A', '西门地库A区', 44, 21, DATE_SUB(NOW(), INTERVAL 4 HOUR)),
  (16, 2, 'PARK-WEST-01', 'demo-west-03', 'B', '西门地库B区', 36, 24, DATE_SUB(NOW(), INTERVAL 4 HOUR))
ON DUPLICATE KEY UPDATE
  `monitor_id` = VALUES(`monitor_id`),
  `device_code` = VALUES(`device_code`),
  `batch_no` = VALUES(`batch_no`),
  `area_code` = VALUES(`area_code`),
  `area_name` = VALUES(`area_name`),
  `total_spaces` = VALUES(`total_spaces`),
  `occupied_spaces` = VALUES(`occupied_spaces`),
  `create_time` = VALUES(`create_time`);

INSERT INTO `parking_traffic_flow_record`
  (`id`, `monitor_id`, `device_code`, `batch_no`, `in_count`, `out_count`, `net_flow`, `total_flow`, `create_time`)
VALUES
  (1, 1, 'PARK-EAST-01', 'flow-east-01', 18, 10, 8, 28, DATE_SUB(NOW(), INTERVAL 12 HOUR)),
  (2, 1, 'PARK-EAST-01', 'flow-east-02', 26, 18, 8, 44, DATE_SUB(NOW(), INTERVAL 8 HOUR)),
  (3, 1, 'PARK-EAST-01', 'flow-east-03', 21, 24, -3, 45, DATE_SUB(NOW(), INTERVAL 5 HOUR)),
  (4, 1, 'PARK-EAST-01', 'flow-east-04', 38, 27, 11, 65, DATE_SUB(NOW(), INTERVAL 2 HOUR)),
  (5, 1, 'PARK-EAST-01', 'flow-east-05', 12, 9, 3, 21, DATE_SUB(NOW(), INTERVAL 20 MINUTE)),
  (6, 2, 'PARK-WEST-01', 'flow-west-01', 14, 9, 5, 23, DATE_SUB(NOW(), INTERVAL 10 HOUR)),
  (7, 2, 'PARK-WEST-01', 'flow-west-02', 19, 16, 3, 35, DATE_SUB(NOW(), INTERVAL 5 HOUR)),
  (8, 2, 'PARK-WEST-01', 'flow-west-03', 9, 11, -2, 20, DATE_SUB(NOW(), INTERVAL 35 MINUTE))
ON DUPLICATE KEY UPDATE
  `monitor_id` = VALUES(`monitor_id`),
  `device_code` = VALUES(`device_code`),
  `batch_no` = VALUES(`batch_no`),
  `in_count` = VALUES(`in_count`),
  `out_count` = VALUES(`out_count`),
  `net_flow` = VALUES(`net_flow`),
  `total_flow` = VALUES(`total_flow`),
  `create_time` = VALUES(`create_time`);

INSERT INTO `parking_space_info` (`id`, `location`, `occupied_vehicle`, `total_spaces`) VALUES
  (1, '地下车库A区', '京A12345', 56),
  (2, '地下车库B区', NULL, 48),
  (3, '地面东侧临停车位', '京B23456', 32),
  (4, '地面西侧临停车位', NULL, 28)
ON DUPLICATE KEY UPDATE
  `location` = VALUES(`location`),
  `occupied_vehicle` = VALUES(`occupied_vehicle`),
  `total_spaces` = VALUES(`total_spaces`);

INSERT INTO `visitor_info`
  (`id`, `visitor_name`, `visit_time`, `plate_number`, `owner_user_id`)
VALUES
  (1, '张三', DATE_ADD(NOW(), INTERVAL 2 HOUR), '京A8K123', 3),
  (2, '李四', DATE_ADD(NOW(), INTERVAL 1 DAY), '京B6M456', 3),
  (3, '王五', DATE_SUB(NOW(), INTERVAL 1 DAY), '京C9N789', 4),
  (4, '赵六', DATE_ADD(NOW(), INTERVAL 3 DAY), NULL, 4)
ON DUPLICATE KEY UPDATE
  `visitor_name` = VALUES(`visitor_name`),
  `visit_time` = VALUES(`visit_time`),
  `plate_number` = VALUES(`plate_number`),
  `owner_user_id` = VALUES(`owner_user_id`);

INSERT INTO `device_repair_info`
  (`id`, `device_name`, `location`, `report_time`, `repair_detail`, `publisher`, `owner_user_id`)
VALUES
  (1, '楼道照明灯', '3号楼1单元2层', DATE_SUB(NOW(), INTERVAL 3 HOUR), '楼道灯闪烁，夜间通行不方便。', 'aaa', 3),
  (2, '单元门禁', '3号楼1单元门口', DATE_SUB(NOW(), INTERVAL 1 DAY), '门禁刷卡偶发失灵。', 'aaa', 3),
  (3, '停车场道闸', '西门地下车库入口', DATE_SUB(NOW(), INTERVAL 2 DAY), '道闸抬杆较慢，早高峰排队。', 'bbb', 4),
  (4, '楼道摄像头', '4号楼3层楼道', DATE_SUB(NOW(), INTERVAL 4 DAY), '画面偶尔卡顿，请检修网络。', 'bbb', 4)
ON DUPLICATE KEY UPDATE
  `device_name` = VALUES(`device_name`),
  `location` = VALUES(`location`),
  `report_time` = VALUES(`report_time`),
  `repair_detail` = VALUES(`repair_detail`),
  `publisher` = VALUES(`publisher`),
  `owner_user_id` = VALUES(`owner_user_id`);

UPDATE `monitor` m
LEFT JOIN (
  SELECT `monitor_id`, COUNT(*) AS `cnt`
  FROM `alarm_info`
  GROUP BY `monitor_id`
) a ON m.`id` = a.`monitor_id`
SET m.`alarm_cnt` = COALESCE(a.`cnt`, 0);

ALTER TABLE `user_info` AUTO_INCREMENT = 5;
ALTER TABLE `case_type_info` AUTO_INCREMENT = 13;
ALTER TABLE `monitor` AUTO_INCREMENT = 8;
ALTER TABLE `monitor_recognition_rule` AUTO_INCREMENT = 5;
ALTER TABLE `alarm_info` AUTO_INCREMENT = 13;
ALTER TABLE `system_message` AUTO_INCREMENT = 5;
ALTER TABLE `alarm_push_record` AUTO_INCREMENT = 6;
ALTER TABLE `weather_region_config` AUTO_INCREMENT = 8;
ALTER TABLE `weather_info` AUTO_INCREMENT = 8;
ALTER TABLE `environment_sensor_record` AUTO_INCREMENT = 16;
ALTER TABLE `parking_area_status` AUTO_INCREMENT = 7;
ALTER TABLE `parking_area_record` AUTO_INCREMENT = 17;
ALTER TABLE `parking_traffic_flow_record` AUTO_INCREMENT = 9;
ALTER TABLE `parking_space_info` AUTO_INCREMENT = 5;
ALTER TABLE `visitor_info` AUTO_INCREMENT = 5;
ALTER TABLE `device_repair_info` AUTO_INCREMENT = 5;
