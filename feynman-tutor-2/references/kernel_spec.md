# 费曼学习 Agent — 内核规范（完整版）

> 版本：V1.0 | 日期：2026-07-24
> 用途：① 作为 Expert 的 system prompt 基础；② 作为未来独立桌面应用的「对话引擎规范」。
> 设计原则：**与 UI / 持久化 / 调度解耦**。内核只负责"怎么教、怎么评估、怎么诊断"，宿主负责渲染与存储。

## 内核状态机

内核维护一个 `session_state`，驱动对话走向。状态迁移由用户动作 + 内核评估结果共同决定。

```
GREETING        → 欢迎 + 介绍方法论
SUBJECT_SELECT  → 节点1：学科/领域/GitHub/上传 选择
GOAL_SELECT     → 节点2：3 级场景化目标选择（无摸底题）
                 （上下文模式可预选推断等级，须用户确认/改选后才继续；见 SKILL.md「节点 1.5」）
MODULE_PLAN     → 节点3：LLM 拆解模块，可「跳过已学」
LECTURE         → 节点4：类比开场 → 「懂了/没太懂」
HOMEWORK        → 节点5：出 1-2 道开放题（核心：用自己的话解释）
ASSESS          → 节点6：评估用户回答 → 输出结构化评估结果
  ├─ PASS  → PRACTICE（节点7，条件触发）
  └─ FAIL  → DIAGNOSE
PRACTICE        → 节点7：做中学（条件触发）
  ├─ 条件1：goal_level >= 🟡能用上？
  │    ├─ 否（🟢能看懂）→ 跳过 → MODULE_DONE
  │    └─ 是 → 检查条件2
  ├─ 条件2：PRACTICE 场景是否需要未学过的前置知识？
  │    ├─ 是 → 跳过或简化场景 → MODULE_DONE
  │    └─ 否 → 进入 PRACTICE
  └─ PRACTICE 完成 → MODULE_DONE
DIAGNOSE        → 节点6：诊断根因
REMEDIATE       → 对症补强（换比喻/插微课/换题型/建议休息）
  → 回到 HOMEWORK 或 LECTURE（视根因）
MODULE_DONE     → 节点8：before/after + 掌握清单 + 归档 3 类文档
REVIEW          → 节点9：输出型复习（做题/复述），由宿主调度触发
```

## 落地说明

### 作为 WorkBuddy Expert / Skill 使用
- 将 system prompt + 行为规则写入 Expert/Skill 配置
- ` ```feynman ` 块在纯聊天环境被忽略（不影响聊天体验），但**建议保留**
- 局限：持久化、富 UI（热力图/动画/文档树）、主动复习推送需宿主另行提供；内核只保证"对话教学法"正确

### 作为独立应用对话引擎使用
- 内核逻辑 = 状态机 + 决策树 + Envelope
- 宿主职责：解析 ` ```feynman ` 块 → 渲染卡片/动画/文档树 → 写 SQLite（掌握度）→ 跑艾宾浩斯调度 → 桌面通知
- 同一份内核 prompt 直接复用，无需重写教学法

### 内核公共性
无论最终路线（Expert 验证 / 独立桌面 / Expert 当 LLM 后端），方法论与决策树是稳定公共资产，不应随技术栈重写。
