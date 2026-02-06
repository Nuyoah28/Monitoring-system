# API 接口文档

**Base URL**: `http://localhost:10215/api/v1`

**认证方式**: JWT Bearer Token（除标记为 `@Pass` 的接口外，其他接口都需要在请求头中携带 Token）

**请求头格式**: `Authorization: Bearer <token>`

---

## 用户管理 (`/api/v1/user`)

### 用户登录
**说明**: 用户登录，获取 JWT Token

```bash
curl -X POST http://localhost:10215/api/v1/user/login \
  -H "Content-Type: application/json" \
  -d '{"userName":"root","password":"123456"}'
```

### 用户注册
**说明**: 注册新用户

```bash
curl -X POST http://localhost:10215/api/v1/user/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"123456","role":1}'
```

### 刷新 Token
**说明**: 刷新即将过期的 Token

```bash
curl -X POST http://localhost:10215/api/v1/user/refresh \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"
```

### 修改密码
**说明**: 修改当前用户密码

```bash
curl -X POST http://localhost:10215/api/v1/user/update/password \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"oldPassword":"123456","newPassword":"newpass"}'
```

### 修改用户名
**说明**: 修改当前用户名

```bash
curl -X POST http://localhost:10215/api/v1/user/update/name/newName \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"
```

---

## 告警管理 (`/api/v1/alarm`)

### 接收告警
**说明**: 接收外部系统推送的告警信息（无需认证）

```bash
curl -X POST "http://localhost:10215/api/v1/alarm/receive?cameraId=1&caseType=3&clipId=abc123" \
  -H "Content-Type: application/json"
```

### 获取告警详情
**说明**: 根据告警ID获取告警详情（无需认证）

```bash
curl -X GET http://localhost:10215/api/v1/alarm/1 \
  -H "Content-Type: application/json"
```

### 查询告警列表
**说明**: 分页查询告警列表，支持多条件筛选

```bash
curl -X GET "http://localhost:10215/api/v1/alarm/query?pageNum=1&pageSize=10&caseType=3&status=0&warningLevel=4" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"
```

### 获取告警数量
**说明**: 根据条件统计告警数量（无需认证）

```bash
curl -X GET "http://localhost:10215/api/v1/alarm/query/cnt?caseType=3&time1=2023-01-01&time2=2023-12-31" \
  -H "Content-Type: application/json"
```

### 获取历史告警统计
**说明**: 获取历史告警统计数据（无需认证）

```bash
curl -X GET "http://localhost:10215/api/v1/alarm/query/cnt/history?defer=7" \
  -H "Content-Type: application/json"
```

### 更新告警状态
**说明**: 更新告警处理状态和处理内容（无需认证）

```bash
curl -X PUT http://localhost:10215/api/v1/alarm/update \
  -H "Content-Type: application/json" \
  -d '{"id":1,"status":1,"processingContent":"已处理"}'
```

### 删除告警
**说明**: 根据告警ID删除告警（无需认证）

```bash
curl -X DELETE http://localhost:10215/api/v1/alarm/1 \
  -H "Content-Type: application/json"
```

### 获取实时告警统计
**说明**: 获取实时告警统计数据（无需认证）

```bash
curl -X GET http://localhost:10215/api/v1/alarm/realtime \
  -H "Content-Type: application/json"
```

### 导出告警数据
**说明**: 导出告警数据为 Excel 文件（无需认证）

```bash
curl -X GET http://localhost:10215/api/v1/alarm/export \
  -H "Content-Type: application/json" \
  --output alarms.xlsx
```

---

## 监控点管理 (`/api/v1/monitor`)

### 获取监控点列表
**说明**: 获取当前用户有权限访问的监控点列表

```bash
curl -X GET http://localhost:10215/api/v1/monitor \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"
```

### 获取监控点地图位置
**说明**: 获取所有监控点的地图位置信息

```bash
curl -X GET http://localhost:10215/api/v1/monitor/map \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"
```

### 获取监控点信息（Flask）
**说明**: 通过监控点 Token 获取监控点信息

```bash
curl -X GET http://localhost:10215/api/v1/monitor/flask/info \
  -H "Authorization: Bearer <monitor_token>" \
  -H "Content-Type: application/json"
```

### 更新监控点
**说明**: 更新监控点信息

```bash
curl -X POST http://localhost:10215/api/v1/monitor/update \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"id":1,"name":"监控点1","department":"区域A","leader":"张三"}'
```

### 创建监控点（Flask）
**说明**: 创建新监控点，返回监控点ID和Token（无需认证）

```bash
curl -X POST http://localhost:10215/api/v1/monitor/flask/create \
  -H "Content-Type: application/json" \
  -d '{"name":"监控点1","department":"区域A","leader":"张三","longitude":116.397,"latitude":39.916}'
```

### 获取监控点图片
**说明**: 获取监控点图片URL

```bash
curl -X GET http://localhost:10215/api/v1/monitor/image/1 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"
```

### 开启/关闭监控点
**说明**: 切换监控点的运行状态

```bash
curl -X POST http://localhost:10215/api/v1/monitor/switch/1 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"
```

---

## 天气管理 (`/api/v1/weather`)

### 获取最新天气
**说明**: 获取指定监控点的最新天气信息

```bash
curl -X GET http://localhost:10215/api/v1/weather/newest/1 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"
```

### 获取天气历史
**说明**: 获取指定监控点的所有天气历史记录

```bash
curl -X GET http://localhost:10215/api/v1/weather/all/1 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"
```

### 添加天气数据
**说明**: 添加新的天气数据

```bash
curl -X POST http://localhost:10215/api/v1/weather/add \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"monitorId":1,"temperature":25,"humidity":60,"weather":"晴"}'
```

---

## 视频流 (`/video`)

### 获取 FLV 视频流
**说明**: 获取 FLV 格式的视频文件，支持 Range 请求（无需认证）

```bash
curl -X GET http://localhost:10215/video/001.flv \
  -H "Range: bytes=0-1023" \
  --output video.flv
```

---

## CBS 服务 (`/api/v1/cbs`)

### AI 对话
**说明**: 调用 AI 服务进行对话

```bash
curl -X POST http://localhost:10215/api/v1/cbs \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message":"你好"}'
```

---

## 响应格式

所有接口统一返回 `CommonResult` 格式：

```json
{
  "code": "00000",
  "message": "请求正常",
  "data": {}
}
```

### 错误码说明

| 错误码 | 说明 |
|--------|------|
| 00000 | 请求正常 |
| A1000 | 请求失败 |
| D0400 | Token 过期 |
| D0500 | Token 不存在 |

---

## 注意事项

1. **Token 有效期**: 30天，即将过期（剩余时间 < 7天）时会自动刷新
2. **无需认证的接口**: 标记为 `@Pass` 的接口不需要 Token
3. **分页参数**: `pageNum` 从 1 开始
4. **时间格式**: `yyyy-MM-dd HH:mm:ss` 或 `yyyy-MM-dd`
