# 阶段规划工作流

## 概述

为特定阶段创建可执行计划。加载上下文、进行阶段讨论、执行研究、分解任务，
生成含 must_haves 的 PLAN.md。

本工作流专为 PM 场景设计，覆盖发现、策略、PRD、执行规划、发布 GTM 等 PM 阶段类型。

## 前置条件

- `.planning/` 目录存在且完整
- 阶段 N 在 ROADMAP.md 中已定义
- 如果 N > 1，前置阶段已完成（或明确允许跳过）

## 执行步骤

### 步骤 0：加载上下文

读取以下文件到上下文：
1. `.planning/PROJECT.md` — 产品愿景、需求、约束、决策
2. `.planning/ROADMAP.md` — 当前阶段的目标和成功标准
3. `.planning/STATE.md` — 当前状态、最近决策、待处理事项
4. 前置阶段的 `NN-SUMMARY.md`（如果存在）— 关键发现和结论
5. 前置阶段的 `NN-VERIFICATION.md`（如果存在）— 已验证的状态

创建阶段目录：
```bash
mkdir -p .planning/phases/{NN-name}/
```

### 步骤 1：阶段讨论（BLOCKING）

**目标**：确认阶段范围，识别需要研究的主题。

基于 ROADMAP.md 中该阶段的定义，执行聚焦的讨论：

1. **确认阶段目标**：
   ```
   根据路线图，阶段 {N} ({name}) 的目标是：
   {goal from ROADMAP}
   
   让我们细化这个阶段的具体范围。
   ```

2. **提出阶段特定的澄清问题**（使用 `references/questioning.md` 的提问模式）：
   - 范围确认："这个阶段你最想得到的产出是什么？"
   - 约束识别："有什么时间、资源或信息的限制？"
   - 接口明确："这个阶段依赖哪些前置阶段的结论？"
   - 验收标准："做完后，你怎么判断这个阶段成功了？"

3. **总结阶段范围**：
   ```
   ## 阶段 {N} 范围确认
   
   **阶段类型**: {discovery/strategy/PRD/execution/release}
   **目标**: {refined goal}
   **产出物**: {deliverables}
   **不包括**: {out of scope}
   **成功标准**: {criteria}
   ```

4. **STOP and WAIT** for user confirmation

### 步骤 2：研究

根据阶段类型，执行不同类型的研究。参考对应领域文档：

**发现阶段** — 参考 `references/domain/discovery-methods.md`：
- 竞品分析：识别 3-5 个直接/间接竞品
- 市场研究：TAM/SAM/SOM 估算
- 用户研究：用户画像、痛点分析
- 机会评估：机会解决方案树（如适用）
- Wiki 搜索：搜索已有知识库

**策略阶段** — 参考 `references/domain/strategy-frameworks.md`：
- 产品愿景定义
- 价值主张设计（JTBD 格式）
- 策略画布（9 区块）
- 商业模式分析
- 关键指标定义（北极星 + 输入指标）
- Wiki 搜索：搜索竞品和策略相关文档

**PRD 阶段**：
- 用户故事编写（INVEST 标准）
- 功能优先级排序（P0/P1/P2）
- 验收标准定义
- 边界情况分析
- Wiki 搜索：验证需求、检测冲突

**执行规划阶段**：
- 将 PRD 需求转化为可执行的功能规格
- 里程碑 & 发布节奏规划
- 关键路径识别 & 风险分析
- 跨团队协作接口定义（设计、开发、测试的交付节奏）
- PM 产出：功能规格文档、里程碑路线图、风险清单

**发布阶段** — 参考 `references/domain/gtm-patterns.md`：
- 滩头阵地细分分析
- ICP 定义
- 消息 & 价值主张设计
- GTM 渠道分析
- 发布倒计时规划
- 成功指标定义

**研究产物**：创建 `NN-RESEARCH.md`（遵循 `templates/RESEARCH.md`）：
- 研究问题
- 方法论
- 主要发现
- 数据来源
- 结论和建议

**Wiki 集成**（如果有 llm-wiki-skill）：
- 研究开始前：wiki-query 搜索已有知识
- 研究完成后：将新发现结晶回 wiki
- 详见 `references/wiki-integration.md`

### 步骤 3：创建 PLAN.md

遵循 `templates/PLAN.md` 模板创建 `NN-MM-PLAN.md`：

**Frontmatter（YAML）**：
```yaml
---
phase: {N}
plan: {MM}
phase_name: "{name}"
phase_type: "{discovery|strategy|prd|execution|release}"
depends_on: []
must_haves:
  truths:
    - "{可验证的产品事实}"
  artifacts:
    - "{必须存在的文件}"
  key_links:
    - "{产物间的关键关联}"
user_setup: []
---
```

**任务分解**（XML 结构）：
```xml
<plan>
<objective>{阶段目标}</objective>

<tasks>
<task id="{N}.{MM}.1" type="auto">
<description>{具体可执行的任务描述}</description>
<read_first>{开始前必须阅读的文件，逗号分隔}</read_first>
<acceptance_criteria>
- {可检查的完成条件 1}
- {可检查的完成条件 2}
</acceptance_criteria>
<produces>{产出的文件列表}</produces>
</task>

<task id="{N}.{MM}.2" type="auto">
...
</task>
</tasks>

<dependencies>
- {MM}-PLAN.md: depends_on [{dep}], produces [{files}]
</dependencies>
</plan>
```

**任务设计原则**：
- 2-3 个任务/计划，~50% 上下文上限
- 优先纵向完整（端到端交付物，如「完整的竞品分析报告」）
- 每个任务有明确的验收标准（可快速判断通过/不通过）
- 区分 `type="auto"`（Agent 自动执行）和 `checkpoint:human-verify`（需要用户确认）
- `produces` 列出具体文件路径
- PM 任务按逻辑顺序排列（先采集 → 再分析 → 再撰写）

**Must_haves 设计**：
- **truths**：可验证的产品事实或结论（如"竞品分析涵盖 Top 5 竞品，每家含定价和功能对比"）
- **artifacts**：必须存在且实质化的文件（如"RESEARCH.md 存在，≥ 50 行，含数据来源引用"）
- **key_links**：产物间的关键关联（如"PRD 的用户故事引用 RESEARCH.md 中的用户画像数据"）

### 步骤 4：审查（BLOCKING）

展示完整计划：

```
## 阶段 {N} 计划审查

**阶段**: {N} - {name}
**目标**: {objective}
**计划数**: {count}
**估计工作量**: {粗略估计}

### Must-Haves 验证标准
- Truths: {count} 项
- Artifacts: {count} 项
- Key Links: {count} 项

### 任务分解
{N}.{MM}.1: {task-1-description} → 产出 {files}
{N}.{MM}.2: {task-2-description} → 产出 {files}

### 计划文件
.planning/phases/{NN-name}/{NN-MM-PLAN.md}
```

### 步骤 5：创建 CONTEXT.md

将步骤 1 的讨论决策记录到 `NN-CONTEXT.md`：
- 阶段范围确认
- 关键假设
- 讨论中做出的决策
- 用户的具体要求

### 步骤 6：等待确认

**STOP and WAIT** — 用户说"继续"或"执行"后才结束规划阶段。

## 关键规则

- 步骤 1 是 BLOCKING：必须等用户确认阶段范围
- 步骤 4 是 BLOCKING：必须等用户批准计划
- 研究深度由阶段类型决定
- 每个 PLAN.md ≤ 3 个任务
- 中文输出
