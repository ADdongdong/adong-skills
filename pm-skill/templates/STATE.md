# STATE.md — 项目状态

> 跨会话短时记忆。保持 **< 100 行**。详细决策记录在 PROJECT.md 中。

---

## 项目参考

- **产品**: {产品名称}
- **PROJECT.md**: `.planning/PROJECT.md`
- **当前焦点**: Phase {N} — {phase-name}

---

## 当前位置

```
Phase: {N} of {total}
Plan:  {MM} of {phase-plans}
状态:  {ready to plan | planning | ready to execute | in progress | phase complete}
```

**最近活动**: Phase {N}, Plan {MM} {执行/规划} — {date}
**进度**: [████████░░] {percent}%

---

## 最近决策（摘要）

- {date}: {decision-summary}（详见 PROJECT.md）
- {date}: {decision-summary}

---

## 待处理

### TODO
- [ ] {task-1}
- [ ] {task-2}

### Blockers
- 🚫 {blocker-1}: {description} — {mitigation plan}

### 关注点
- ⚠️ {concern-1}: {description}

---

## 指标

| 指标 | 值 |
|------|-----|
| 已完成阶段 | {N} |
| 已完成计划 | {M} |
| 总产文件数 | {count} |

---

## 会话连续性

- **上次会话**: {YYYY-MM-DD HH:MM}
- **上次操作**: {action}
- **恢复文件**: `.planning/.continue-here.md`（如存在）

---

## 更新指南

- 每次关键操作后更新（Transition、Execute 完成、Significant Decision）
- 保持 < 100 行 — 如果太长，移入 PROJECT.md
- 不重复 PROJECT.md 中的详细决策 — 只放摘要和指针
