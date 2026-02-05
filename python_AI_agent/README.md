# 智能监控系统 AI Agent

### 运行Agent

#### 方式一：HTTP API 服务（推荐）

```bash
# 普通模式
python agent_api.py

# 流式模式（支持实时输出）
python agent_api_stream.py
```

服务将在 `http://localhost:5000` 启动

#### 方式二：交互式命令行

```bash
python intelligent_agent.py
```

### HTTP API 调用

```bash
# 普通模式
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "有哪些告警？", "token": "your_jwt_token"}'

# 流式模式（SSE）
curl -X POST http://localhost:5000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"question": "有哪些告警？", "token": "your_jwt_token"}'
```
