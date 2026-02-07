# 智能监控系统 AI Agent

直接运行agent_api.py文件即可启动agent服务 开放在5000端口

前端悬浮窗可拖动询问 

支持实时流式回复

```
python agent_api.py
```

LLM 驱动的 Tool-Calling agent
# 运行流程
AI先识别问题选择所需的tools和参数，向后端发送请求获取数据，之后根据数据和用户问题给出答案与建议

