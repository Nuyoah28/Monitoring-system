# 监控类技能 (Monitor Skills)

## 概述
监控类技能用于查询和管理系统中的监控点信息。

## 技能列表

### 1. get_monitor_list - 监控点列表查询
- **功能**: 查询当前用户可访问的监控点列表
- **参数**: 无

### 2. get_monitor_detail - 监控点详情查询
- **功能**: 按监控点 ID 或名称查询监控点详情
- **参数**:
  - `monitor_id`: 可选，监控点 ID
  - `monitor_name`: 可选，监控点名称

## 后端接口
- `GET /monitor` - 查询监控点列表
- `GET /monitor/{id}` - 查询监控点详情
