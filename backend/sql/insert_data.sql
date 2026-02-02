-- 用户表：仅添加新数据，保留现有数据
INSERT INTO user_info (id, user_name, password, phone, role) VALUES 
(3, 'aaa', '42f641872ae4070ed059696b1df93394', '13800138000', 0),
(4, 'bbb', '42f641872ae4070ed059696b1df93394', '13900139000', 1);

-- 案例类型表：删除现有数据并重新插入
DELETE FROM case_type_info;
INSERT INTO case_type_info (id, case_type_name) VALUES 
(1, '进入危险区域'),
(2, '烟雾'),
(3, '打架斗殴'),
(4, '摔倒'),
(5, '明火'),
(6, '吸烟');

-- 监控设备表：删除现有数据并重新插入
DELETE FROM monitor;
INSERT INTO monitor (id, name, area, leader, alarm_cnt, stream_link, latitude, longitude, danger_area, fall, flame, smoke, wave, punch, running, left_x, left_y, right_x, right_y) VALUES 
(1, '1号病房摄像头', '1号病房', 'aaa', 5, 'rtmp://example.com/stream1', 39.9042, 116.4074, 1, 1, 1, 1, 0, 0, 0, 100, 100, 500, 500),
(2, '医院大厅摄像头', '医院大厅', 'bbb', 3, 'rtmp://example.com/stream2', 39.9052, 116.4084, 0, 1, 0, 1, 0, 0, 1, 150, 150, 550, 550),
(3, '海底捞摄像头', '海底捞', 'aaa', 7, 'rtmp://example.com/stream3', 39.9062, 116.4094, 1, 1, 1, 0, 0, 0, 0, 200, 200, 600, 600),
(4, '正阳春摄像头', '正阳春', 'bbb', 2, 'rtmp://example.com/stream4', 39.9072, 116.4104, 0, 0, 1, 1, 0, 0, 1, 250, 250, 650, 650),
(5, '115摄像头', '115', 'bbb', 8, 'rtmp://example.com/stream5', 39.9082, 116.4114, 1, 1, 0, 0, 0, 1, 0, 300, 300, 700, 700);

-- 告警信息表：删除现有数据并重新插入（关联到monitor和case_type）
DELETE FROM alarm_info;
INSERT INTO alarm_info (id, clip_link, monitor_id, case_type, warning_level, create_time, status, processing_content) VALUES 
(1, 'xS5hpPA89A', 4, 3, 4, '2023-09-22 22:38:12', 0, NULL),
(2, 'Hm7tG6BzyJ', 2, 6, 2, '2023-09-26 14:30:15', 0, NULL),
(3, '4okMFqZteg', 4, 3, 3, '2023-09-22 17:23:09', 0, NULL),
(4, '4Sh0DzFWvt', 3, 2, 5, '2023-09-18 12:39:12', 0, NULL),
(5, 'gtmDGU1EZ7', 2, 4, 1, '2023-09-26 12:53:10', 0, NULL),
(6, 'iOMh3u4g6z', 5, 5, 4, '2023-09-26 10:52:19', 0, NULL),
(7, 'Yq3CDS3jx0', 4, 5, 4, '2023-09-28 13:30:29', 0, NULL),
(8, 'dla6wJbiEF', 1, 2, 3, '2023-09-13 12:16:12', 0, NULL),
(9, 'ECgrl1Sivu', 4, 5, 2, '2023-09-15 03:39:28', 0, NULL),
(10, 'MeaDx5or3F', 4, 3, 2, '2023-09-25 23:06:03', 0, NULL);
