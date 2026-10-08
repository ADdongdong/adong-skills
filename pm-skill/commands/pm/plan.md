---
name: pm-plan
description: "为特定阶段创建详细执行计划。进行阶段讨论、研究和任务分解，生成含 must_haves 的可执行 PLAN.md。"
argument-hint: "<phase-number>"
---

# /pm-plan — 阶段规划

触发 `pm-skill`，执行阶段规划工作流。

## 工作流

1. **加载上下文** — 读取 PROJECT.md, ROADMAP.md, STATE.md, 前置阶段 SUMMARY

2. **阶段讨论（BLOCKING）** — 参考 `references/questioning.md`：
   - 确认阶段范围：这个阶段要达成什么？
   - 明确交付物：具体产出什么文档/产物？
   - 识别依赖：依赖哪些前置阶段的结论？
   - 澄清边界：什么是本阶段不做的？
   - STOP → 等待用户确认阶段范围

3. **研究** — 根据阶段类型执行研究：
   - **发现阶段**：竞品分析、市场研究、用户画像 → `references/domain/discovery-methods.md`
   - **策略阶段**：策略画布、价值主张、商业模式 → `references/domain/strategy-frameworks.md`
   - **PRD 阶段**：需求细化、用户故事编写
   - **发布阶段**：GTM 策略、渠道分析 → `references/domain/gtm-patterns.md`
   - 如有 wiki，搜索已有知识库（见 `references/wiki-integration.md`）

4. **创建 PLAN.md** — 遵循 `templates/PLAN.md` 模板：
   - **Must_haves**（truths, artifacts, key_links）用于目标-回推验证
   - **任务分解**：2-3 个任务/计划，~50% 上下文
   - **验收标准**：可 grep 验证的具体条件
   - **产物清单**：每个任务产出的具体文件
   - 如有多计划 → 按依赖关系排列执行顺序

5. **审查（BLOCKING）** — 展示完整计划 → STOP → 等待用户确认

## 产出物

- `.planning/phases/NN-name/NN-CONTEXT.md` — 阶段讨论决策
- `.planning/phases/NN-name/NN-RESEARCH.md` — 阶段研究报告
- `.planning/phases/NN-name/NN-MM-PLAN.md` — 可执行计划

## 关键规则

- 2-3 个任务/计划，~50% 上下文上限
- 优先纵向切片（端到端交付物）而非横向分层
- 每个任务必须有可验证的验收标准
- 阶段类型决定研究深度：发现/策略阶段研究更深
- 中文输出
