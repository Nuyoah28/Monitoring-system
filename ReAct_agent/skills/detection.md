# 侦测类技能 (Detection Skills)

## 概述
侦测类技能用于管理 Mamba-YOLO 开放世界检测目标配置。

## 技能列表

### 1. update_detection_prompts - 更新侦测目标
- **功能**: 更新开放世界检测目标列表
- **参数**:
  - `prompts`: 必填，字符串数组，例如 ['红色电动车', '戴帽子的人']

## 后端接口
- `POST /monitor/update_prompt` - 下发侦测目标到算法服务

## 说明
该技能用于动态更新 Mamba-YOLO 模型的开放世界检测目标，支持自然语言输入（逗号、顿号分隔）。
