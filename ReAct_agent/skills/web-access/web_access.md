# Web Access Skill

## 概述
web_access 是联网插件工具，用于搜索互联网信息和抓取网页内容。

## 技能列表

### 1. web_access - 联网搜索与抓取
- **功能**: 执行联网搜索，或抓取指定 URL 的网页内容
- **参数**:
  - `action`: 可选，search 或 fetch，默认 search
  - `query`: 可选，搜索关键词
  - `url`: 可选，fetch 时的目标网页地址

## 说明
- 当用户提到网站、网址、联网、搜索、web、http/https 时，优先考虑调用此工具。
- `action=search` 返回搜索入口建议，`action=fetch` 返回网页内容摘要。
