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

唯一完整建库脚本，适合新环境初始化。

包含：

- 主业务表结构
- 告警类型、默认等级和启用状态
- IoT 环境、车位、天气、推送相关表
- 基础演示数据

注意：

- 脚本里包含 `DROP TABLE`
- 脚本里自带 `CREATE DATABASE` 和 `USE SweatPear`
- 已有数据库不要直接执行这个文件

### 2. `migrate_case_type_warning_level.sql`

适合已有数据库升级到“告警等级由 `case_type_info` 配置”的版本。

主要用于：

- 给 `case_type_info` 增加 `warning_level`、`enabled`
- 写入 12 类告警类型的默认等级
- 将吸烟、冰面设为隐藏/停用
- 同步历史 `alarm_info.warning_level`

### 3. `migrate_nearby_push.sql`

这是“邻近居民告警推送”相关的增量迁移脚本。

### 4. `iot_env_parking.sql`

这是 IoT 环境与车位数据相关表的建表脚本，历史环境可按需参考；新环境已合并进 `final_schema.sql`。

### 5. `env_weather_flow.sql`

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


