---
name: pm-config
description: "查看或修改 .planning/config.json 设置。"
argument-hint: "[key=value]"
---

# /pm-config — 配置管理

触发 `pm-skill`，管理项目配置文件。

## 工作流

1. **无参数** — 展示当前配置：
   - 读取 `.planning/config.json`
   - 格式化展示关键设置：
     ```
     ## 当前 PM 工作流配置
     
     **模式**: interactive / yolo
     **粒度**: coarse / standard / fine
     **Gate 状态**:
       confirm_project: ✅ enabled
       confirm_roadmap: ✅ enabled
       ...
     **研究**: enabled / disabled
     **Wiki 集成**: enabled / disabled
     **自动推进**: enabled / disabled
     ```

2. **有参数** — 修改配置：
   - `/pm-config mode=yolo`
   - `/pm-config wiki_enabled=false`
   - `/pm-config granularity=fine`
   - 验证 key 是否有效
   - 更新 config.json
   - 展示变更

## 可配置项

| Key | 可选值 | 说明 |
|-----|--------|------|
| `mode` | interactive / yolo | 每步确认 / 自动批准 |
| `granularity` | coarse / standard / fine | 阶段粒度 |
| `research` | true / false | 启用研究 |
| `wiki_enabled` | true / false | 启用 wiki 集成 |
| `prd_gates` | true / false | PRD BLOCKING gates |
| `confirm_roadmap` | true / false | 路线图确认 gate |
| `confirm_plan` | true / false | 计划确认 gate |
| 等等 | 见 templates/config.json | |

## 关键规则

- 无效 key → 提示有效选项
- 中文输出
