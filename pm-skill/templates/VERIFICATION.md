# VERIFICATION.md — 阶段验证报告

> 验证阶段交付物是否满足 PLAN.md 中定义的 must_haves。
> 由 `/pm-verify` 命令生成。

---

## 报告摘要

| 属性 | 内容 |
|------|------|
| **阶段** | Phase {N} — {phase-name} |
| **验证日期** | {YYYY-MM-DD} |
| **验证人** | AI (pm-skill) |
| **总体状态** | ✅ PASS / ⚠️ PASS WITH GAPS / ❌ FAIL |
| **Must-Haves 通过率** | {passed}/{total} ({percent}%) |

---

## 自动化检查

### 文件存在性

| 预期文件 | 存在 | 大小 |
|----------|------|------|
| {path-1} | ✅ | {size} |
| {path-2} | ✅ | {size} |
| {path-3} | ❌ | — |

**结果**: {pass}/{total} 通过

### 内容实质性（防桩检测）

| 文件 | 占位符残留 | 最小长度 | 模板符合性 | 状态 |
|------|-----------|----------|-----------|------|
| {file-1} | 无 | ✅ ({lines} 行) | ✅ | ✅ |
| {file-2} | `[待补充]` × 3 | ⚠️ (模板 80% 长度) | ⚠️ | ❌ |
| {file-3} | 无 | ✅ | ✅ | ✅ |

**占位符检测模式**: `[待补充]` `[placeholder]` `TODO` `TBD` `[描述]` `[内容]` `[产品名称]` `[日期]` `[姓名]`

**结果**: {pass}/{total} 通过

---

## Must-Haves 验证

### Truths

| # | Truth | 状态 | 证据 |
|---|-------|------|------|
| 1 | {truth-description} | ✅ | {evidence — grep 结果、文件引用} |
| 2 | {truth-description} | ❌ | {缺失说明} |

**Truths 通过**: {pass}/{total}

### Artifacts

| # | Artifact | 存在 | 实质性 | 状态 |
|---|----------|------|--------|------|
| 1 | {file-path} | ✅ | ✅ | ✅ |
| 2 | {file-path} | ✅ | ❌ | ❌ |

**Artifacts 通过**: {pass}/{total}

### Key Links

| # | Link | 状态 | 证据 |
|---|------|------|------|
| 1 | {link-description} | ✅ | grep `"pattern"` found in {file}:{line} |
| 2 | {link-description} | ❌ | grep no match |

**Key Links 通过**: {pass}/{total}

---

## 缺口分析

### 🚩 关键缺口（阻塞 Transition）

| # | 缺口 | 影响 | 修复建议 |
|---|------|------|----------|
| 1 | {gap-description} | {why critical} | {suggested fix} |

### ⚠️ 非关键缺口（记录即可）

| # | 缺口 | 影响 | 处理方式 |
|---|------|------|----------|
| 1 | {gap-description} | {minor impact} | 记录，下版本修复 |

---

## 建议

- [ ] 🚩 关键缺口 — 必须先修复再 Transition
- [ ] ✅ 全部通过 — 可以执行 `/pm-transition`
- [ ] ⚠️ 非关键缺口可接受 — 建议 Transition（记录缺口）

---

## 更新指南

- 验证完成后立即生成
- 缺口写入 STATE.md 的 Blockers（如是关键缺口）
- 如有关键缺口，修复后重新验证（覆盖此文件或创建 VERIFICATION-v2.md）
