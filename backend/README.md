# Backend

后端服务目录。

## SQL 脚本使用说明

SQL 脚本统一放在 [sql](./sql) 目录下。使用前先确认：

- MySQL 版本建议 `8.0+`
- 数据库字符集建议 `utf8mb4`
- 执行前先切换到目标数据库，或在脚本里确认 `USE xxx;`

## 推荐执行方式

不要在 Windows PowerShell 里使用：

```powershell
Get-Content .\backend\sql\quick_create.sql | mysql -u root -p Sweatpear
```

原因是 `Get-Content` 会先把 SQL 文件读成 PowerShell 字符串，再通过管道发送给 `mysql`，中文内容很容易在这个过程中被转成乱码或 `?`，最终导致语法错误。


先进入 MySQL：

```bash
mysql --default-character-set=utf8mb4 -u root -p
```

然后执行：

```sql
CREATE DATABASE IF NOT EXISTS Sweatpear DEFAULT CHARSET utf8mb4;
USE Sweatpear;
SOURCE sql/quick_create.sql;
SOURCE sql/iot_env_parking.sql;
SOURCE sql/env_weather_flow.sql;
SOURCE sql/migrate_nearby_push.sql;
```


## 各脚本用途

### 1. `quick_create.sql`

适合“快速初始化整库”。
它是一个较完整的数据库导出脚本，包含建表和大量初始数据。

适用场景：

- 本地第一次搭环境
- 需要快速拿到一套可运行的测试数据库

注意：

- 脚本里包含 `DROP TABLE`
- 脚本里自带 `USE Sweatpear;`
- 执行前先确认数据库名是否与你当前环境一致

### 2. `table.sql`

适合“只创建基础表结构”。
如果你只想先把主业务表建出来，不立即导入整套演示数据，可以优先执行它。

适用场景：

- 新库建表
- 需要自己控制初始化数据

### 3. `insert_data.sql`

适合“补充演示/测试数据”。
会向部分表插入示例数据，便于联调。

注意：

- 里面有些表会先 `DELETE` 再 `INSERT`
- 不建议直接在生产库执行

### 4. `migrate_nearby_push.sql`

这是“邻近居民告警推送”相关的增量迁移脚本。
主要用于补充：

- `user_info` 新字段
- `system_message` 接收人字段
- `alarm_push_record` 推送记录表

适用场景：

- 老库升级到支持附近居民推送的版本

### 5. `iot_env_parking.sql`

这是 IoT 环境与车位数据相关表的建表脚本，主要新增：

- `environment_sensor_record`
- `parking_area_status`
- `parking_area_record`

适用场景：

- 接入环境传感器数据
- 接入车位状态和车位历史数据

### 6. `env_weather_flow.sql`

这是环境与天气流程的增量脚本，主要补充：

- `environment_sensor_record` 的可燃气体字段
- `weather_region_config`
- `weather_info`

同时包含对老表的 `ALTER TABLE` 兼容处理。

适用场景：

- 已有环境表，需要继续接入天气能力
- 老库升级到“环境 + 天气”新流程

## 服务器部署补充

当前仓库支持两种后端部署模式：

- `docker`
  通过 `jib:dockerBuild` 构建镜像，再用 `docker compose` 重建 `backend` 容器
- `process`
  直接在服务器上执行 `mvn clean package`，再用 `nohup java -jar` 启动 Spring Boot

GitHub Actions 目前默认使用 `process` 模式，配置位置在 [.github/workflows/deploy-server.yml](../.github/workflows/deploy-server.yml) 里的 `DEPLOY_MODE`。

### `process` 模式日志位置

如果使用服务器直跑模式：

- 进程 PID 文件：`backend/run/backend.pid`
- 历史日志目录：`backend/logs/`
- 当前最新日志软链接：`backend/logs/current.log`

常用排查命令：

```bash
cd /opt/Monitoring-system/backend
cat run/backend.pid
tail -f logs/current.log
ps -fp "$(cat run/backend.pid)"
```


