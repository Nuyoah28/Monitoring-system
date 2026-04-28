# City App Frontend

`city_app/` 是 uni-app 移动端前端，包含管理端与业主端两套入口。

## 配置文件在哪里

### 1. `common/config.js`

这是移动端的运行时配置中心，负责统一管理：

- Java 后端地址 `API_BASE_URL`
- 告警 WebSocket 地址 `WS_ALARM_URL`
- AI Agent HTTP 地址 `AI_HTTP_URL`
- AI Agent WebSocket 地址 `AI_WS_URL`
- 演示视频目录 `DEMO_VIDEO_BASE_URL`
- 演示告警视频映射 `DEMO_ALARM_VIDEO_MAP`
- 模拟告警视频解析 `resolveDemoAlarmVideo`

页面和公共工具如果要访问接口、连 WebSocket、展示模拟告警视频，都应该从这里读取，不要在页面里直接写死 IP 或 `localhost` 地址。

### 2. `common/app-config.js`

这是应用模式配置：

- `manage`：管理端登录后的首页、路由跳转方式、是否启用 WebSocket
- `owner`：业主端登录后的首页、路由跳转方式、是否启用 WebSocket

如果要修改“登录成功后跳到哪一页”“当前是管理端还是业主端”，改这个文件。

### 3. `manifest.json`

这是 uni-app / HBuilderX 的构建期配置，不是普通运行时配置。这里的内容不能随便搬到 JS 文件里，因为打包器要求它们必须放在 `manifest.json`：

- `appid`
- Android / iOS 权限
- 高德地图 SDK Key
- 原生模块声明
- 小程序平台的 `appid`
- 推送、定位、地图等原生能力配置

也就是说：

- 接口地址、演示视频地址可以放 `common/config.js`
- `manifest.json` 里的平台能力和打包参数必须保留在这里

### 4. `pages.json`

这是页面路由与 tabBar 配置文件，主要表示：

- 页面注册顺序
- 每个页面的标题栏样式
- 是否下拉刷新
- tabBar 的图标、文字、跳转页面

如果是“页面路径、导航栏、tabBar”相关修改，改这里，不改 `common/config.js`。

## 相关调用关系

- `api/request.js` 从 `common/config.js` 读取 `API_BASE_URL`
- `common/websocket.js` 从 `common/config.js` 读取 `WS_ALARM_URL`
- AI 页面从 `common/config.js` 读取 `AI_HTTP_URL` / `AI_WS_URL`
- 实时告警详情页现在从 `common/config.js` 读取演示视频映射，不再在页面里写死视频地址

## 当前约定

- 运行时地址统一改 `common/config.js`
- 应用模式统一改 `common/app-config.js`
- 打包、权限、SDK Key 统一改 `manifest.json`
- 路由与 tabBar 统一改 `pages.json`

## 这次已经收口的硬编码

- 管理端告警详情页里的演示视频地址
- `SIM_BIKE_DEMO` / `SIM_FIRE_DEMO` / `SIM_GARBAGE_DEMO` 的视频解析逻辑

如果后面还要新增模拟资源，优先扩展 `common/config.js`，不要再把地址直接写进页面。
