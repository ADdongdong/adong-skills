# 验证工作流

## 概述

验证阶段交付物是否满足计划中定义的 must_haves。
改编自 spec-skill 的 `workflows/verify-work.md`，适配 PM 产物验证。

## 前置条件

- 阶段的所有 PLAN.md 都有对应的 SUMMARY.md
- 所有计划任务已完成

## 执行步骤

### 步骤 0：收集验证上下文

1. 读取阶段所有的 `NN-MM-PLAN.md` 文件
2. 提取所有 `must_haves`（truths, artifacts, key_links）
3. 读取阶段所有的 `NN-MM-SUMMARY.md` 文件
4. 列出阶段目录下的所有产物文件

### 步骤 1：自动化检查

#### 1.1 文件存在性
对每个 `must_haves.artifacts`：
- `ls {file_path}` 确认文件存在
- 记录：✅ 存在 / ❌ 缺失

#### 1.2 内容实质性（防桩检测）
使用 `references/verification-patterns.md` 的模式：

对于 PM 文档，检查：
- **占位符检测**：grep `[待补充]` `[placeholder]` `TODO` `TBD` `[描述]` `[内容]`
- **空白段落**：grep 连续两个空行后无实质内容的模式
- **模板原文**：grep 模板中的占位文本（如 `[产品名称]` `[日期]` `[姓名]`）
- **最小长度**：文档 < 模板长度的 80% 视为不完整

#### 1.3 内容质量
- PRD 文档：检查是否包含所有必需的章节
- 研究报告：检查是否有数据来源引用
- 策略文档：检查是否包含 9 个区块的实质内容
- 发布计划：检查是否包含时间线和成功指标

### 步骤 2：Must-haves 验证

#### 2.1 Truths 验证
对每个 `must_haves.truths`：
- 阅读对应产物文件
- 判断文件中是否确认了该事实
- 记录：✅ 确认 / ⚠️ 部分 / ❌ 未确认

示例：
```
Truth: "竞品分析涵盖 Top 5 竞品"
验证: grep 竞品名称 → 找到 5 个 → ✅
```

#### 2.2 Artifacts 验证
对每个 `must_haves.artifacts`：
- 文件存在？
- 文件实质性（通过步骤 1.2 检测）？
- 记录：✅ 通过 / ❌ 失败

#### 2.3 Key Links 验证
对每个 `must_haves.key_links`：
- grep 相关的交叉引用模式
- 确认产物间关联已建立
- 记录：✅ 已关联 / ❌ 缺失

示例：
```
Key Link: "PRD 的用户故事引用 RESEARCH.md 中的用户画像"
验证: grep "用户画像\|persona\|user profile" prd.md → 找到引用 → ✅
```

### 步骤 3：缺口分析

汇总验证结果，分类：

- **🚩 关键缺口**：阻塞 transition，必须修复
  - 缺失关键产物文件
  - must_haves truths 未满足
  - 关键产物仅含占位符

- **⚠️ 非关键缺口**：可记录，不阻塞
  - 非核心章节有待补充的内容
  - 数据可进一步完善
  - 辅助文档缺失

### 步骤 4：生成验证报告

创建 `NN-VERIFICATION.md`（遵循 `templates/VERIFICATION.md`）：

```markdown
# Phase {N} Verification Report

## Summary
- 阶段: {N} - {name}
- 验证日期: {date}
- 总体状态: ✅ PASS / ⚠️ PASS WITH GAPS / ❌ FAIL
- Must-Haves 通过率: {X}/{Y}

## Automated Checks
| Check | Result |
|-------|--------|
| 文件存在性 | {pass}/{total} |
| 内容实质性 | {pass}/{total} |
| 模板符合性 | {pass}/{total} |

## Must-Haves Verification

### Truths
| Truth | Status | Evidence |
|-------|--------|----------|
| {truth-1} | ✅/❌ | {evidence} |

### Artifacts
| Artifact | Exists | Substantive | Status |
|----------|--------|-------------|--------|
| {file-1} | ✅ | ✅ | ✅ |
| {file-2} | ✅ | ❌ (占位符残留) | ❌ |

### Key Links
| Link | Status | Evidence |
|------|--------|----------|
| {link-1} | ✅ | grep found in {file} |

## Gap Analysis

### Critical Gaps
- 🚩 {gap-1}: {description} → 建议: {fix}

### Non-Critical Gaps
- ⚠️ {gap-2}: {description}

## Recommendation
- [ ] 关键缺口修复后重新验证
- [ ] 或：非关键缺口可接受 → 允许 transition
```

### 步骤 5：展示结果

展示验证报告摘要 → **STOP and WAIT** for user confirmation

如果有关键缺口：
```
⚠️ 发现 {N} 个关键缺口，必须先修复才能过渡到下一阶段。
建议: /pm-execute {N} --fix 重新执行相关计划
```

如果通过：
```
✅ 阶段 {N} 验证通过！准备过渡到下一阶段。
下一步: /pm-transition
```

## 关键规则

- 存在 ≠ 实质化 — 必须 grep 检测
- 关键缺口 = 阻塞 transition
- 用户确认后才能标记验证完成
- 中文输出
