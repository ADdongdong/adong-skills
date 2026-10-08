# 阶段切换工作流

## 概述

完成当前阶段，更新所有项目状态文件，准备进入下一阶段。
改编自 spec-skill 的 `workflows/transition.md`。

## 前置条件

- 当前阶段所有 PLAN.md 都有对应的 SUMMARY.md
- VERIFICATION.md 存在且无关键缺口（或用户明确接受缺口）
- STATE.md 反映了当前阶段的最新状态

## 执行步骤

### 步骤 0：完成性检查

运行快速完成性检查：

1. 列出阶段目录所有 PLAN.md：`ls .planning/phases/{NN-name}/*PLAN.md`
2. 列出阶段目录所有 SUMMARY.md：`ls .planning/phases/{NN-name}/*SUMMARY.md`
3. 确认每个 PLAN 都有对应的 SUMMARY
4. 确认 `NN-VERIFICATION.md` 存在
5. 确认 VERIFICATION.md 中没有 🚩 关键缺口

如有缺失 → 报告用户并建议补救措施

### 步骤 1：更新 PROJECT.md

读取 `.planning/PROJECT.md`，更新：

1. **需求状态更新**：
   - 将本阶段相关的需求从 "Active" 移到 "Validated"
   - 添加通过验证的确认标记（日期 + 验证结果）

2. **决策记录追加**：
   ```markdown
   ## 关键决策
   
   ### Phase {N} ({date})
   - {decision-1}: {context and rationale}
   - {decision-2}: {context and rationale}
   ```

3. **产品上下文更新**：
   - 添加本阶段发现的新知识
   - 更新产品理解的演进

### 步骤 2：更新 ROADMAP.md

读取 `.planning/ROADMAP.md`，更新：

1. **标记阶段完成**：
   ```markdown
   | {N} | {name} | {goal} | {N}/{N} | ✅ Complete | {completion-date} |
   ```

2. **更新进度表**：
   - 完成百分比
   - 实际完成日期 vs. 计划日期

3. **标记下一阶段就绪**：
   ```markdown
   | {N+1} | {next-name} | {next-goal} | 0/{M} | 🔜 Ready | — |
   ```

### 步骤 3：更新 STATE.md

更新 `.planning/STATE.md`（保持 < 100 行）：

1. **位置更新**：
   ```markdown
   ## Current Position
   Phase: {N+1} of {total}
   Status: ready to plan
   Last activity: Phase {N} completed ({date})
   Progress: [████████░░] {percent}%
   ```

2. **Accumulated Context 更新**：
   - 过去 1-2 个阶段的关键决策（摘要）
   - 当前待处理的 TODO
   - 已解决的 blockers

3. **Performance 更新**：
   - 阶段 {N} 完成时间
   - 累计完成阶段数
   - 如有数据，更新 velocity

### 步骤 4：里程碑归档（如适用）

如果当前阶段是一个里程碑节点（如完成 MVP 定义），创建里程碑快照：

```bash
mkdir -p .planning/milestones/v{X}.{Y}
```

复制：
- ROADMAP.md → `v{X}.{Y}-ROADMAP.md`
- REQUIREMENTS.md → `v{X}.{Y}-REQUIREMENTS.md`
- 阶段目录 → `v{X}.{Y}-phases/{NN-name}/`

### 步骤 5：过渡检查点（BLOCKING）

展示过渡摘要：

```
## 阶段 {N} 完成 — 过渡检查点

### 已完成
- ✅ {artifact-1}: {brief}
- ✅ {artifact-2}: {brief}
- 📊 Must-haves 通过率: {X}/{Y}

### 关键决策
- {decision-1}
- {decision-2}

### 下一阶段预览
**阶段 {N+1}**: {name}
**目标**: {goal}
**产出**: {expected deliverables}

---
准备好开始阶段 {N+1} 吗？
- 确认 → 我会建议运行 /pm-plan {N+1}
- 暂停 → 当前状态已保存，随时可恢复
- 回顾 → 需要修改什么？
```

**STOP and WAIT** for user confirmation。

### 步骤 6：最终化

用户确认后：

1. 确认所有文件已写入磁盘
2. 展示下一步操作建议：
   ```
   ✅ 阶段 {N} 已完成！状态已更新。
   🚀 下一步：/pm-plan {N+1}
   ```

## 关键规则

- 完整性检查不通过 → 拒绝过渡
- 关键缺口未修复 → 拒绝过渡
- STATE.md 必须 < 100 行
- 保持中文输出
