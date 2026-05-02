# Backend

后端服务目录。

## SQL 脚本使用说明

SQL 脚本统一放在 [sql](./sql) 目录下。使用前先确认：

- MySQL 版本建议 `8.0+`
- 数据库字符集建议 `utf8mb4`
- 执行前先切换到目标数据库，或在脚本里确认 `USE xxx;`

## 推荐执行方式

不要在 Windows PowerShell 里使用 `Get-Content ... | mysql` 执行包含中文的 SQL 文件。

原因是 `Get-Content` 会先把 SQL 文件读成 PowerShell 字符串，再通过管道发送给 `mysql`，中文内容很容易在这个过程中被转成乱码或 `?`，最终导致语法错误。

建议使用 Navicat 查询窗口直接打开并执行 SQL，或先进入 MySQL：

```bash
mysql --default-character-set=utf8mb4 -u root -p
```

## 各脚本用途

### 1. `final_schema.sql`

最终表结构脚本，适合新环境初始化的第一步。

包含：

- 主业务表结构
- 索引和外键
- IoT 环境、车位、天气、推送相关表
- 业主端访客/报修隔离字段
- 个人中心头像、住户区域、推送配置字段
- 摄像头自定义识别规则表

注意：

- 脚本里包含 `DROP TABLE`
- 脚本里自带 `CREATE DATABASE` 和 `USE SweatPear`
- 已有数据库不要直接执行这个文件
- 这个文件不包含演示数据

### 2. `final_seed_data.sql`

最终演示数据脚本，适合新环境初始化的第二步。

包含：

- 默认账号，密码均为 `123456`
- 12 类告警类型及默认等级
- 摄像头/监控点演示数据
- 告警、社区消息、报警推送记录
- 环境监测、天气、停车服务演示数据
- 访客登记、设备报修演示数据
- 摄像头自定义识别规则演示数据

新机器初始化顺序：

```sql
source backend/sql/final_schema.sql;
source backend/sql/final_seed_data.sql;
```

如果用 Navicat，就先打开并执行 `final_schema.sql`，再打开并执行 `final_seed_data.sql`。

### 3. `migrate_case_type_warning_level.sql`

适合已有数据库升级到“告警等级由 `case_type_info` 配置”的版本。

主要用于：

- 给 `case_type_info` 增加 `warning_level`、`enabled`
- 写入 12 类告警类型的默认等级
- 将吸烟、冰面设为隐藏/停用
- 同步历史 `alarm_info.warning_level`

### 4. `migrate_nearby_push.sql`

这是“邻近居民告警推送”相关的增量迁移脚本。

### 5. `iot_env_parking.sql`

这是 IoT 环境与车位数据相关表的建表脚本，历史环境可按需参考；新环境已合并进 `final_schema.sql`。

### 6. `env_weather_flow.sql`

这是环境与天气流程的增量脚本，历史环境可按需参考；新环境已合并进 `final_schema.sql`。

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

## Ubuntu server runtime config

Use environment variables for server-specific addresses and credentials instead
of editing `application-*.yml` directly.

Example:

```bash
export SPRING_PROFILES_ACTIVE=prod
export MYSQL_HOST=127.0.0.1
export MYSQL_PORT=3306
export MYSQL_DATABASE=SweatPear
export MYSQL_USERNAME=monitoring_app
export MYSQL_PASSWORD='replace-me'
export REDIS_HOST=127.0.0.1
export REDIS_PORT=6379
export REDIS_PASSWORD=''
export AGENT_API_URL=http://127.0.0.1:5050
export ALGORITHM_API_URL=http://127.0.0.1:6006
export IOT_MQTT_ENABLED=true
export IOT_MQTT_BROKER_URL=tcp://127.0.0.1:1883
```

Important:

- Ubuntu MySQL often maps `root@localhost` to `auth_socket`, which causes
  error `1698 Access denied` for password logins from the app. Prefer a
  dedicated MySQL user for Spring Boot instead of `root`.
- If MongoDB logs still show `localhost:27017`, that value is not coming from
  the tracked Spring YAML files in this repo. Check the server process
  environment, startup script, or any untracked profile files on the server.

## 腾讯云 COS 配置

项目里已经接入腾讯云 COS SDK，配置统一走 Spring Boot 的 `oss` 配置项。不要把 SecretId / SecretKey 写进仓库，建议在本机或服务器环境变量里配置：

```bash
export COS_SECRET_ID='你的 SecretId'
export COS_SECRET_KEY='你的 SecretKey'
export COS_REGION='ap-beijing'
export COS_BUCKET='my-server-1397492316'
export COS_BASE_URL='https://my-server-1397492316.cos.ap-beijing.myqcloud.com'
```

对应配置文件：

- `application-dev.yml`
- `application-dev-my.yml`
- `application-prod.yml`

报警视频仍然保存对象 key / clipId 到数据库，后端服务层会把它转换成 COS 访问链接。这样数据库迁移到新机器时不需要因为 COS 域名变化批量改历史数据。
