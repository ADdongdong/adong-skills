# PLAN.md — 可执行阶段计划

> 本文档是阶段的执行蓝图。**BLOCKING gate**: 必须经用户确认后才能执行。

---

```yaml
---
phase: {N}
plan: {MM}
phase_name: "{phase-name}"
phase_type: "{discovery|strategy|prd|execution|release}"
depends_on: [{dependency-plan-ids}]
must_haves:
  truths:
    - "{可验证的产品事实 — 验证方式}"
  artifacts:
    - "{文件路径 — 必须存在且实质化}"
  key_links:
    - "{交叉引用模式 — grep 可验证}"
user_setup: []
---
```

---

```xml
<plan>
<objective>{该计划要达成的单一目标}</objective>

<context>
{从 PROJECT.md、前置 SUMMARY.md 和讨论中提取的关键上下文}
</context>

<tasks>

<task id="{N}.{MM}.1" type="auto">
<description>{具体、可执行的任务描述}</description>
<read_first>{开始前必须读取的文件，逗号分隔}</read_first>
<acceptance_criteria>
- {可检查的完成条件 1}
- {可检查的完成条件 2}
</acceptance_criteria>
<produces>{产出的文件路径，逗号分隔}</produces>
</task>

<task id="{N}.{MM}.2" type="auto">
<description>{具体、可执行的任务描述}</description>
<read_first>{文件列表}</read_first>
<acceptance_criteria>
- {条件 1}
- {条件 2}
</acceptance_criteria>
<produces>{文件路径}</produces>
</task>

</tasks>

<dependencies>
- {MM}-PLAN.md: depends_on [{deps}], produces [{files}]
</dependencies>

<verification>
{执行后如何验证计划成功的说明}
</verification>
</plan>
```

---

## Must_Haves 设计指南

### truths（可验证的事实/结论）
定义该计划完成后，从产品视角可确认的事实或结论。
- ✅ 好: "竞品分析涵盖 5 家直接竞品，每家包含定价、功能、GTM 策略"
- ✅ 好: "PRD 包含完整的功能优先级排序（P0/P1/P2），每个 P0 功能有验收标准"
- ❌ 差: "竞品分析完成"

### artifacts（产物 — 必须存在的文件）
定义必须存在的具体文件及其质量要求。
- ✅ 好: "prd/auth-system/v1/prd.md — 存在且 ≥ 100 行，无占位符"
- ✅ 好: "RESEARCH.md — 包含执行摘要、方法论、主要发现、数据来源四个章节"
- ❌ 差: "PRD 文档完成"

### key_links（关键关联 — 产物间的交叉引用）
定义产物间可验证的关联模式。
- ✅ 好: "PRD.md 引用 RESEARCH.md 中的用户画像数据"
- ✅ 好: "STRATEGY.md 的价值主张与 PROJECT.md 的产品愿景一致"
- ❌ 差: "文档之间有关联"

---

## 任务设计原则

1. **纵向完整**: 每个任务产出完整的端到端交付物（如「完成竞品分析报告」而非「写竞品分析的第 3 节」）
2. **可验证**: 每个验收标准能在 5 秒内判断通过/不通过
3. **上下文友好**: `<read_first>` 只列真正需要读取的文件，不堆砌无关资料
4. **大小适中**: 2-3 个任务/计划，约 50% 上下文上限
5. **顺序合理**: PM 任务通常有逻辑先后（先研究 → 再分析 → 再撰写），按依赖关系排序

---

## 任务类型

- `type="auto"` — Agent 自动执行，无需中途确认（如「搜索 Top 5 竞品信息」）
- `type="checkpoint:human-verify"` — 需要用户审查确认后才能继续（如「确认竞品分析维度覆盖完整」）

---

## PM 阶段典型任务示例

### 发现（Discovery）阶段
- 任务 1: 竞品信息采集（Web 搜索 + 信息整理）
- 任务 2: 竞品深度分析（功能对比、定价、GTM 策略）
- 任务 3: 用户画像 & 市场机会总结（checkpoint: human-verify）

### 策略（Strategy）阶段
- 任务 1: 9 区块策略画布填写（愿景、细分、痛点、价值主张）
- 任务 2: 战略权衡 & 护城河分析（checkpoint: human-verify）

### PRD 阶段
- 任务 1: 用户故事 & 功能需求编写
- 任务 2: 边界情况 & 非功能需求定义
- 任务 3: 完整 PRD 整合 & 优先级排序（checkpoint: human-verify）

---

## 更新指南

- 计划获批后修改 → 标记变更 → 重新确认
- 执行中发现问题 → 记录到 SUMMARY.md 的 deviations
- 验证失败 → 更新 PLAN.md 并重新执行
