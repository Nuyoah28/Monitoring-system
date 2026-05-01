# Docker 热更新与 GitHub 自动部署说明

## 1. 先说结论

你现在这套后端，建议分成两种运行方式：

- 本地开发：用 Docker 开发容器 + Spring Boot DevTools，支持改代码后自动重启
- 服务器部署：本地提交代码到 GitHub 后，由 GitHub Actions 自动连接服务器，拉取最新代码，重新构建镜像，再重建容器

这里第二种严格来说不是“容器内热更新”，而是“自动部署 + 自动重建容器”。
对你当前的 Spring Boot + Maven + Jib 项目，这是最稳妥的方案。

## 2. 当前生产镜像里的目录位置

当前项目通过 [pom.xml](../pom.xml) 里的 `jib-maven-plugin` 构建生产镜像。

- 基础镜像：`eclipse-temurin:17-jre-focal`
- 主启动类：`com.sipc.monitoringsystem.MonitoringSystemApplication`
- 端口：`10215`

Jib 没有自定义 `appRoot`，所以镜像内应用默认放在 `/app`：

- `/app/classes`：编译后的 class 文件
- `/app/resources`：资源文件
- `/app/libs`：依赖 jar

直跑模式下的文件位置：

PID：/opt/Monitoring-system/backend/run/backend.pid
日志目录：/opt/Monitoring-system/backend/logs/
当前最新日志：/opt/Monitoring-system/backend/logs/current.log

所以生产容器里运行的是已经打包好的应用，不是源码仓库目录。

## 3. 为什么不建议在生产容器里直接 `git pull`

原因很简单：

1. 生产容器是运行容器，不是开发容器
2. Jib 生产镜像里通常没有完整 Git 工作区
3. 即使把代码拉进容器，也不会自动替换 `/app/classes` 中正在运行的 class
4. Java 代码更新后仍然需要重新编译，并重启应用或重建容器

所以服务器正确做法不是：

- 进入正在运行的容器执行 `git pull`

而是：

- 在服务器宿主机的项目目录执行 `git pull`
- 重新构建镜像
- 重建后端容器

## 4. 你现在这套服务器自动更新方案

已经按你的仓库地址改成下面这条链路：

仓库地址：

```bash
https://github.com/Nuyoah28/Monitoring-system.git
```

自动流程如下：

1. 你在本地修改代码
2. push 到 GitHub 的 `main` 分支
3. GitHub Actions 自动触发
4. Actions 通过 SSH 登录服务器
5. 服务器执行部署脚本
6. 脚本自动 `git pull`
7. 脚本自动执行 `mvn -q -DskipTests compile jib:dockerBuild`
8. 脚本自动执行 `docker compose -f docker-compose.server.yml up -d --force-recreate backend`

## 5. 我已经替你改好的文件

- [docker-compose.server.yml](../docker-compose.server.yml)
- [scripts/deploy-server.sh](../scripts/deploy-server.sh)
- [.github/workflows/deploy-server.yml](../.github/workflows/deploy-server.yml)

### 5.1 服务器 Docker 配置

[docker-compose.server.yml](../docker-compose.server.yml) 现在改成了：

- 使用 `network_mode: host`
- 使用 `SPRING_PROFILES_ACTIVE=prod`

这样做的原因是：

你说服务器上的 MySQL、Redis 端口和密码都和开发机一样，而你当前 [application-prod.yml](../src/main/resources/application-prod.yml) 里数据库和 Redis 的地址也是 `localhost`。

如果服务器是 Linux，并且 Docker 使用 `host` 网络模式，那么容器会直接共享宿主机网络：

- 应用里的 `localhost:3306` 会访问服务器宿主机 MySQL
- 应用里的 `127.0.0.1:6379` 会访问服务器宿主机 Redis

这样你当前的 `application-prod.yml` 就不需要再改数据库和 Redis 地址。

注意：

- `network_mode: host` 只适合 Linux 服务器
- 如果你的服务器不是 Linux，或者你后面想把 MySQL/Redis 也容器化，这个方案要再调整

### 5.2 部署脚本

[deploy-server.sh](../scripts/deploy-server.sh) 现在支持：

- 如果服务器上还没有项目目录，会自动 `git clone`
- 如果已经有仓库，会自动 `git fetch + git pull`
- 自动构建 Jib 镜像
- 自动重建后端容器

默认参数已经改成：

- 项目目录：`/opt/monitoring-system/backend`
- 分支：`main`
- 仓库地址：`https://github.com/Nuyoah28/Monitoring-system.git`

### 5.3 GitHub Actions

[deploy-server.yml](../.github/workflows/deploy-server.yml) 现在已经是正式工作流，不再是示例文件。

只要你把它提交到 GitHub，并配置好 Secrets，push 到 `main` 就会自动部署。

## 6. 你还需要改什么配置

还需要你手动确认或配置下面这些项。

### 6.1 GitHub Secrets

去 GitHub 仓库的：

`Settings -> Secrets and variables -> Actions`

新增这些 Secrets：

- `SERVER_HOST`
- `SERVER_PORT`
- `SERVER_USER`
- `SERVER_SSH_KEY`
- `SERVER_PROJECT_DIR`

建议：

- `SERVER_HOST`：你的服务器公网 IP 或域名
- `SERVER_PORT`：SSH 端口，默认一般是 `22`
- `SERVER_USER`：登录服务器的用户，例如 `root` 或部署用户
- `SERVER_SSH_KEY`：对应服务器公钥登录的私钥内容
- `SERVER_PROJECT_DIR`：建议填 `/opt/monitoring-system/backend`

### 6.2 服务器基础环境

服务器上需要提前装好：

- Git
- Docker
- Docker Compose Plugin
- JDK 17
- Maven

因为当前部署流程是在服务器上执行：

```bash
mvn -q -DskipTests compile jib:dockerBuild
```

所以服务器必须具备 Java 和 Maven 环境。

### 6.3 服务器 SSH 公钥登录

GitHub Actions 是通过 SSH 连服务器的，所以你还需要：

1. 在本地生成一对 SSH 密钥，或单独给部署创建一对密钥
2. 把公钥放到服务器用户的 `~/.ssh/authorized_keys`
3. 把私钥内容保存到 GitHub Secret `SERVER_SSH_KEY`

### 6.4 服务器防火墙

你还需要确认服务器放行了：

- `22` 或你的 SSH 端口
- `10215` 后端服务端口

### 6.5 Java 生产配置

在你当前前提下，`application-prod.yml` 里的 MySQL 和 Redis 地址可以先保持不变，因为现在服务器 compose 已经改成 `host` 网络模式了。

也就是说当前这些地址仍然有效：

- MySQL：`localhost:3306`
- Redis：`127.0.0.1:6379`

但前提是：

- MySQL 确实跑在服务器宿主机上
- Redis 也确实跑在服务器宿主机上
- 它们的账号、密码、库名和你 `application-prod.yml` 中一致

如果以后数据库不在宿主机上，而是在别的机器或别的容器里，就必须再改 `application-prod.yml`。

## 7. 整体配置流程

你可以直接按这个顺序做。

1. 把当前改动提交并 push 到 GitHub
2. 在服务器安装 Git、Docker、Compose、JDK17、Maven
3. 在服务器创建部署目录，例如 `/opt/monitoring-system`
4. 确认服务器本机 MySQL 和 Redis 已经启动，并且账号密码与 `application-prod.yml` 一致
5. 在 GitHub 仓库里配置 `SERVER_HOST`、`SERVER_PORT`、`SERVER_USER`、`SERVER_SSH_KEY`、`SERVER_PROJECT_DIR`
6. 确认服务器 SSH 可以通过密钥登录
7. push 到 `main` 分支，触发 Actions 自动部署
8. GitHub Actions 会自动 SSH 到服务器执行部署脚本
9. 部署脚本会自动 clone 或 pull 仓库、构建镜像、重建容器

## 8. 建议你手动先跑一次

第一次建议你先在服务器手动执行一次，确认环境没问题：

```bash
sh /opt/monitoring-system/backend/scripts/deploy-server.sh /opt/monitoring-system/backend main https://github.com/Nuyoah28/Monitoring-system.git
```

如果这一步能成功，再交给 GitHub Actions 自动跑，排错会轻松很多。

## 9. 目前这套方案的边界

这套方案的优点是简单、稳定、容易维护。

它的限制也很明确：

- 部署时会有短暂重启
- 不属于零停机发布
- 依赖服务器本机已经装好 Maven 和 JDK

如果你下一步想把它升级成“几乎不停机”的版本，我可以继续帮你改成：

- Nginx + 双容器蓝绿发布
- 或 GitHub Actions 构建镜像后推送仓库，再让服务器只负责拉镜像重启
