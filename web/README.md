## 启动

```bash
npm install
npm run serve
```

生产构建：

```bash
npm run build
```

## 配置文件

### 1. `src/config/config.ts`

这是 Web 前端的运行时配置中心，页面里涉及下面这些内容时，都应该从这里读取：

- 后端 API 地址 `baseUrl`
- WebSocket 地址 `webSocketBaseUrl`
- 算法服务地址 `algorithmUrl`
- Agent 服务地址 `agentBaseUrl`
- 演示视频地址 `demoVideoBaseUrl`
- 监控流地址 `rtmpAddressList` / `rtmpAddress`
- 告警默认视频 `alarmDefaultVideo`
- 演示联动频道名 `simulateChannelName`
- 高德地图配置 `amapConfig`

现在地图、演示告警视频、监控默认流、联动频道都已经收口到这个文件，业务组件里不应该再写死 URL。

### 2. `.env.example`

这是 `config.ts` 对应的环境变量示例。推荐做法：

1. 复制一份为 `.env.local`
2. 按本机环境修改地址和端口
3. 重新启动 `npm run serve`

主要变量：

- `VUE_APP_API_BASE_URL`：Java 后端地址
- `VUE_APP_WS_BASE_URL`：告警 WebSocket 基地址
- `VUE_APP_ALGORITHM_URL`：算法服务地址
- `VUE_APP_AGENT_BASE_URL`：Agent 服务地址
- `VUE_APP_DEMO_VIDEO_BASE_URL`：演示视频目录
- `VUE_APP_MONITOR_STREAMS`：监控流列表，逗号分隔
- `VUE_APP_ALARM_DEFAULT_VIDEO`：默认告警回放地址
- `VUE_APP_SIMULATE_CHANNEL`：演示广播频道名
- `VUE_APP_AMAP_*`：高德地图 Key、版本、默认中心点
- `VUE_APP_DEV_PROXY_TARGET`：本地开发代理目标
- `VUE_APP_DEV_SERVER_PORT`：本地开发端口

### 3. `src/config/digitalHuman.ts`

这是数字人模块的专用配置，负责：

- 数字人模式切换：`live2d` / `video` / `mascot`
- Live2D 模型地址、Cubism 运行时、动作组
- 视频数字人待机/聆听/说话素材

### 4. `.env.digital-human.example`

这是数字人配置的环境变量模板。如果要替换模型、切换视频数字人、修改动作组，优先改这里，而不是去页面组件里找地址。

### 5. `vue.config.js`

这是 Vue CLI 开发配置文件，主要负责：

- `publicPath`
- 开发端口
- `/api` 代理目标

现在代理目标不再写死在文件里，而是优先读取：

- `VUE_APP_DEV_PROXY_TARGET`
- 如果没配，再回退到 `VUE_APP_API_BASE_URL`

## 推荐修改方式

- 改接口地址：优先改 `.env.local`
- 改演示视频、默认流、地图参数：改 `src/config/config.ts` 或对应环境变量
- 改数字人素材：改 `.env.digital-human.local` 或 `src/config/digitalHuman.ts`
- 不要在 `src/pages`、`src/components` 里直接写 `http://...`
