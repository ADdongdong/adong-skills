---
name: pm-quick
description: "轻量临时任务。跳过完整生命周期，快速执行 PM 操作。"
argument-hint: "<task description>"
---

# /pm-quick — 快速任务

触发 `pm-skill`，在不启动完整 PM 生命周期的情况下快速完成一个 PM 任务。

## 适用场景

- 快速竞品查询："帮我查一下 Notion 的竞品有哪些"
- 临时研究："市面上有哪些 AI 客服产品？"
- 快速 PRD 草稿："帮我写一个登录功能的 PRD 草稿"
- 格式转换："把这个功能列表转成用户故事"
- 即兴分析："分析一下这个产品为什么成功"

## 工作流

1. **理解任务** — 快速确认任务范围和期望交付物
2. **执行** — 使用 WebSearch、文件操作等完成任务
3. **输出** — 在工作目录或指定位置生成交付物
4. **（可选）记录** — 如处于 PM 项目中，追加到 STATE.md 的 Recent Activity

## 产物

- 任务特定输出（直接返回或写入文件）
- 可选：`.planning/quick/YYYYMMDD-HHMMSS-task/SUMMARY.md`

## 与完整生命周期对比

| | /pm-quick | 完整生命周期 |
|---|----------|-------------|
| Gate | 无 | 多个 BLOCKING gates |
| 规划 | 跳过 | 详细的 PLAN.md |
| 验证 | 跳过 | Must-haves 验证 |
| 状态追踪 | 可选 | STATE.md 更新 |
| 适用 | 单次查询/草稿 | 系统化产品项目 |

## 关键规则

- 快速执行，不过度规划
- 如果任务实际需要完整流程，建议用户用 `/pm-init` 或 `/pm-prd`
- 中文输出
