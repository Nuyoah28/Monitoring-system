# 智行护卫 AI Agent

当前后端已经统一成 `ReAct + Skill Registry` 架构，支持多用户上下文记忆、多线程并发和实时语音链路。

## 网关层（QQ）

新增了可选的网关层，支持仿 OpenClaw 风格将外部 IM 消息转为 Agent 请求。

当前已提供 QQ 网关 webhook：

- `POST /gateway/qq/webhook`
- `GET /gateway/qq/ping`

当接入 OneBot/CQHTTP 等 QQ 机器人平台时，可将事件回调到该 webhook。

### QQ 网关配置（.env）

```env
AGENT_QQ_GATEWAY_ENABLED=false
AGENT_QQ_GATEWAY_VERIFY_TOKEN=
AGENT_QQ_API_BASE_URL=http://127.0.0.1:5700
AGENT_QQ_API_ACCESS_TOKEN=
AGENT_QQ_GROUP_REQUIRE_AT=true
AGENT_QQ_REQUEST_TIMEOUT_SECONDS=8
```

说明：

- 开启网关：`AGENT_QQ_GATEWAY_ENABLED=true`
- 若配置了 `AGENT_QQ_GATEWAY_VERIFY_TOKEN`，请求需带 `X-QQ-Token`。
- 群聊默认要求 `@机器人` 才处理，避免刷屏。

### 事件处理流程

1. 接收 QQ webhook 事件。
2. 解析 `message_type`、`raw_message`、`user_id`、`group_id`。
3. 生成会话 key（群和私聊隔离）。
4. 调用 Agent 执行。
5. 回调 QQ API 发送回复：
   - 群聊 `send_group_msg`
   - 私聊 `send_private_msg`

## 快速开始

```bash
cd python_AI_agent
pip install -r requirements.txt
python agent_api.py
```

默认启动在 `5050` 端口。

## cli启动 
```bash
python cli.py
```

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

先说结论：

- 不是大多数场景下“只添加一个 skill 文件就够了”
- 只有当这个 skill 是完全自包含的，或者你愿意只依赖 LLM 规划它时，才可能只加一个 skill 文件
- 如果这个 skill 要调用你们后端接口，通常至少还要补 `backend_client.py` 和 `skill_support.py`
- 如果你希望这个 skill 稳定命中，而不是完全靠大模型猜，还要补 `planner.py` 和必要的关键词常量

### 最小可用条件

一个 skill 文件至少要满足这几个条件：

1. 放在 `python_AI_agent/skills/` 目录下
2. 定义一个继承 `AgentSkill` 的类
3. 填写 `name`、`description`、`parameters`
4. 实现 `run()`
5. 暴露 `build_skill()`，并返回 skill 实例

最小模板：

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

如果只是做一个非常简单的本地 skill，例如固定返回说明文本、拼接已有上下文、或者完全不依赖新后端接口，那么到这一步就已经能被自动加载了。

### 什么时候“只加 skill 文件”就够

通常只在下面几种情况成立：

- skill 完全不需要新接口，直接在 `run()` 里就能完成
- skill 只依赖 `runtime.support` 里已经存在的方法
- skill 不要求高命中率，允许完全靠 LLM 读到 `description` 后决定是否调用

例如：

- 返回一段固定帮助文案
- 对已有查询结果做一次简单格式整理
- 调用 `runtime.support` 里已经存在的现成方法

### 什么时候“只加 skill 文件”不够

下面这些情况，通常都不够：

- 你要调用一个新的后端接口
- 你需要把后端原始数据整理成用户可读文本
- 你需要记录上下文状态，支持“上一个”“刚才那个”
- 你希望这个 skill 更稳定地被命中
- 你希望它支持规则优先，而不是纯靠 LLM 规划

这也是你们项目里大多数业务 skill 的真实情况。

### 标准接入流程

如果是“新增一个调用后端接口的业务 skill”，建议按下面顺序做。

#### 第 1 步：补后端接口调用

位置：

- `python_AI_agent/agent_core/backend_client.py`

职责：

- 只负责请求后端
- 只负责鉴权、参数传递、接口返回解析
- 不要在这里写太多面向用户的文案

示例：

```python
def get_xxx(self, user_token: Optional[str] = None) -> Optional[dict]:
    response = self._request(
        "GET",
        "/xxx",
        timeout=10,
        require_auth=True,
        user_token=user_token,
    )
    data = response.json()
    if data.get("code") != "00000":
        return None
    return data.get("data")
```

#### 第 2 步：补业务整理逻辑

位置：

- `python_AI_agent/agent_core/skill_support.py`

职责：

- 调用 `backend_client`
- 把后端原始结果整理成可读文本
- 按需要记录上下文状态

示例：

```python
def handle_get_xxx(self, request_context: RequestContext, params: dict[str, Any]) -> str:
    data = self.backend.get_xxx(user_token=request_context.user_token)
    if not data:
        return "未查询到相关数据。"

    self.remember_tool_state(request_context, "get_xxx", params)
    return f"查询结果：{data}"
```

如果这个 skill 支持连续对话，例如：

- “上一个告警”
- “刚才那个”
- “那昨天呢”

那么状态记录和上下文补全也应该放在 `skill_support.py` 里做。

#### 第 3 步：新增 skill 文件

位置：

- `python_AI_agent/skills/get_xxx.py`

职责：

- 定义 skill 元信息
- 接收参数
- 调用 `runtime.support.handle_xxx(...)`
- 返回用户可读文本

建议保持 skill 文件本身很薄，不要把大量业务逻辑重新堆回 skill 文件。

#### 第 4 步：决定是否补规则路由

位置：

- `python_AI_agent/agent_core/constants.py`
- `python_AI_agent/agent_core/planner.py`

这是很多人最容易漏掉的一步。

当前系统的 skill 触发分两层：

1. 规则命中
2. LLM 规划

如果你不补 `planner.py`，理论上 LLM 还是可能调用这个 skill，因为它会读取 skill 的 `description` 和 `parameters`。

但这样有几个问题：

- 命中不稳定
- 对中文口语表达不一定敏感
- 用户稍微换个说法就可能打不到

所以如果这个 skill 很重要、很高频，建议一定补规则。

常见做法：

1. 在 `constants.py` 补关键词
2. 在 `planner.py` 的 `_rule_based_skill_calls()` 中加入命中逻辑
3. 如果需要连续对话，再看 `_build_contextual_skill_calls()` 是否要补

### 推荐的判断标准

你可以按这张表来判断要做多少工作：

- 纯本地 skill：通常只加 skill 文件就够
- 复用现有 support 方法的 skill：一般加 skill 文件即可
- 新增后端接口 skill：至少要加 `backend_client.py` + `skill_support.py` + skill 文件
- 高频业务 skill：在上一步基础上，再补 `constants.py` 和 `planner.py`
- 支持上下文引用的 skill：再补 `skill_support.py` 的状态记录和上下文解析

### 完整 checklist

新增一个业务 skill 时，建议逐项检查：

1. `skills/xxx.py` 已创建
2. `build_skill()` 已返回实例
3. `name` 唯一，且和规划器里使用的名字一致
4. `run()` 返回的是用户可读文本，不是内部方法名
5. 如果有新接口，`backend_client.py` 已补
6. 如果要整理结果，`skill_support.py` 已补
7. 如果要高命中率，`planner.py` / `constants.py` 已补
8. 如果要连续对话，状态记录已补
9. `build_local_capability_answer()` 是否需要同步更新
10. 本地已验证能被发现并执行

### 常见坑

- 只写了 skill 文件，但没写 `build_skill()`，系统不会加载
- `name` 改了，但 `planner.py` 里还是旧名字，永远命不中
- skill 直接返回内部结构或方法名，用户看到 `get_xxx` 这种内部实现细节
- 只补了 skill 文件，没补后端接口封装，结果 `run()` 里逻辑越来越重
- 想支持“刚才那个”，却没有记录上下文状态

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
