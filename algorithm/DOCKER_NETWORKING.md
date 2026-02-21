# Docker网络配置说明

## 最简单的解决方案

为了让Docker容器内的进程访问宿主机上的服务（端口映射到1935），在Docker容器内使用 `host.docker.internal` 作为主机名。

### 启动Docker容器时：

```bash
# 如果使用Docker Desktop（Windows/Mac），默认支持host.docker.internal
docker run -it your-image-name

# 在Linux上，需要额外配置
docker run -it --add-host=host.docker.internal:host-gateway your-image-name
```

### 配置说明：

- 配置文件中已设置 `STREAM_URL = "rtmp://host.docker.internal:1935"`
- 容器内的videoProcess.py将使用这个地址连接到宿主机上的RTMP服务器
- test.py在宿主机上推送流到localhost:1935，通过端口映射到达RTMP服务器
- videoProcess.py在容器内通过host.docker.internal:1935访问宿主机上的RTMP服务器

### Linux特殊说明：

在Linux上，Docker默认不支持`host.docker.internal`，需要在启动容器时添加：

```bash
--add-host=host.docker.internal:host-gateway
```

### 验证连接：

在容器内执行：
```bash
telnet host.docker.internal 1935
```

如果连接成功，则videoProcess.py应该能够访问到RTMP流。