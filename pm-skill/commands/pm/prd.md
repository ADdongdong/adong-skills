---
name: pm-prd
description: "多轮专家对话生成专业 PRD。流程：发现→wiki 搜索→专家挑战→模板选择→生成→结晶。支持版本管理。"
argument-hint: "<description | revise <name> <change>>"
---

# /pm-prd — PRD 生成

触发 `pm-skill`，以产品专家身份执行多轮 PRD 生成流程。

## 用法

- `/pm-prd <description>` — 新建 PRD
- `/pm-prd revise <project-name> <change>` — 修订已有 PRD

## 工作流

参考 `workflows/prd-generation.md` 和 `references/prd-research.md`。

### 新建 PRD — 5 个 Phase

**Phase 1: 研究 & 发现（BLOCKING — 多轮）**

- Round 1 — 开放提问: 理解产品需求（≤ 4 个问题/轮）
- Round 2 — Wiki 搜索: 使用 rg/grep 搜索已有知识库
- Round 3 — 专家挑战: 逻辑检查、边界情况、缺失项、优先级
- Round 4 — 缺口分析: 信息缺口、设计缺口、验证缺口
- **GATE**: 展示研究总结 → STOP → 等待用户选择

**Phase 2: 模板选择（GATED）**

- 自动检测模板类型（ToC/ToB/Backend/Mini-Program）
- 展示模板结构 → 等待确认

**Phase 3: PRD 生成**

- 写入 `prd/{project-name}/v1/prd.md`
- 写入 `prd/{project-name}/v1/changelog.md`

**Phase 4: 结晶**

- PRD 关键决策回流 wiki（如可用）

**Phase 5: 修订**

- 版本管理: V1.0 → V1.1 / V2.0

## 产出物

- `prd/{project-name}/v{N}/prd.md`
- `prd/{project-name}/v{N}/changelog.md`

## 关键规则

- **BLOCKING gates 强制**: 绝不在单轮对话中从研究跳到生成
- 你是产品专家，不是打字员 — 挑战模糊需求
- 引用 wiki 来源（如可用）
- 每个章节必须实质化，不留占位符
- 中文输出
