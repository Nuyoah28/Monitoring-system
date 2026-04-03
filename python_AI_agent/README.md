# 智行护卫 AI Agent

当前后端已经统一成 `ReAct + Skill Registry` 架构，支持多用户上下文记忆、多线程并发和实时语音链路。

## 快速开始

```bash
cd python_AI_agent
pip install -r requirements.txt
python agent_api.py
```

默认启动在 `5000` 端口。

## 目录说明

核心入口：

- `python_AI_agent/agent_api.py`
- `python_AI_agent/intelligent_agent.py`

核心流程：

- `python_AI_agent/agent_core/react_agent.py`
- `python_AI_agent/agent_core/planner.py`
- `python_AI_agent/agent_core/prompts.py`
- `python_AI_agent/agent_core/memory.py`
- `python_AI_agent/agent_core/backend_client.py`
- `python_AI_agent/agent_core/skill_support.py`

Skill 目录：

- `python_AI_agent/skills/`

统一配置：

- `python_AI_agent/agent_config.json`
- `python_AI_agent/agent_config.example.json`

## 当前能力

- 告警查询、统计、详情、状态更新
- 监控点信息与天气查询
- 检测目标下发
- 多用户上下文记忆
- 多线程并发处理
- 实时语音链路

## 配置说明

统一配置文件：

- `python_AI_agent/agent_config.json`

配置示例：

- `python_AI_agent/agent_config.example.json`

### backend

后端接口登录与请求地址：

```json
{
  "backend": {
    "base_url": "http://localhost:10215/api/v1",
    "username": "root",
    "password": "123456"
  }
}
```

### runtime

运行期参数：

```json
{
  "runtime": {
    "max_history_messages": 6,
    "max_alarm_fetch_pages": 30,
    "alarm_page_size": 100,
    "memory_ttl_seconds": 7200,
    "max_agent_workers": 16
  }
}
```

### ai

当前支持两类 provider：

- `spark`
- `openai_compatible`

腾讯云 DeepSeek 示例：

```json
{
  "ai": {
    "active_provider": "openai_compatible",
    "providers": {
      "openai_compatible": {
        "enabled": true,
        "type": "openai_compatible",
        "base_url": "https://api.lkeap.cloud.tencent.com/v1",
        "api_key": "你的腾讯云 DeepSeek Key",
        "model": "deepseek-v3.2",
        "temperature": 0.5,
        "max_tokens": 2048
      }
    }
  }
}
```

可替换模型名示例：

- `deepseek-v3.2`
- `deepseek-v3.1-terminus`
- `deepseek-v3-0324`
- `deepseek-r1-0528`

兼容说明：

- 默认从 `agent_config.json` 读取配置
- 也可以用环境变量 `AGENT_CONFIG_PATH` 指向另一份配置文件
- 为兼容旧部署，`AGENT_AI_CONFIG_PATH` 仍可作为旧环境变量别名使用

## 如何更换 AI

主配置文件：

- `python_AI_agent/agent_config.json`

最常改的字段：

- `ai.active_provider`
- `ai.providers.openai_compatible.base_url`
- `ai.providers.openai_compatible.api_key`
- `ai.providers.openai_compatible.model`

## 如何更换系统提示词

系统提示词集中在：

- `python_AI_agent/agent_core/prompts.py`

最常改的是这几个位置：

- `ANSWER_SYSTEM_PROMPT`
- `TOOL_SELECTION_TEMPLATE`
- `build_local_capability_answer()`

建议：

- 改回答风格时优先修改 `ANSWER_SYSTEM_PROMPT`
- 改 tool 选择行为时优先修改 `TOOL_SELECTION_TEMPLATE`
- 不要在提示词里暴露内部 skill 名给最终用户

## 如何新增 Skill

skill 采用自动发现机制：

- `python_AI_agent/skills/registry.py`

只要在 `skills/` 下新增 Python 文件，并提供 `build_skill()`，系统启动时就会自动加载。

常见新增步骤：

1. 在 `python_AI_agent/agent_core/backend_client.py` 中补后端接口调用
2. 在 `python_AI_agent/agent_core/skill_support.py` 中补业务整理逻辑
3. 在 `python_AI_agent/skills/` 下新增 skill 文件
4. 如果想提高命中率，再去 `python_AI_agent/agent_core/constants.py` 和 `python_AI_agent/agent_core/planner.py` 补规则路由

skill 模板：

```python
from __future__ import annotations

from skills.base import AgentSkill, SkillRuntime


class GetXxxSkill(AgentSkill):
    name = "get_xxx"
    description = "查询 xxx 信息。"
    parameters = {
        "id": "可选，业务 ID",
    }

    def run(self, params: dict, runtime: SkillRuntime) -> str:
        return runtime.support.handle_get_xxx(runtime.request_context, params)


def build_skill() -> AgentSkill:
    return GetXxxSkill()
```

## 如何删除 Skill

建议按这个顺序处理：

1. 删除 `python_AI_agent/skills/` 下对应的 skill 文件
2. 删除 `python_AI_agent/agent_core/planner.py` 中对这个 skill 的显式引用
3. 删除 `python_AI_agent/agent_core/constants.py` 中只服务于这个 skill 的关键词
4. 视情况删除 `python_AI_agent/agent_core/skill_support.py` 和 `python_AI_agent/agent_core/backend_client.py` 中对应的辅助方法

## 上下文记忆

记忆主要在：

- `python_AI_agent/agent_core/memory.py`
- `python_AI_agent/agent_core/skill_support.py`

当前机制：

- 按 `user_token` / `conversation_key` 隔离不同用户
- 保存最近几轮对话和最近一次 skill 状态

因此系统能理解：

- “那昨天呢”
- “上一个告警”
- “把刚才那个标已处理”

## 验证方式

语法检查：

```bash
python -m compileall python_AI_agent
```

运行后可测试：

- `POST /chat`
- `POST /chat/stream`
- `POST /chat/voice`
