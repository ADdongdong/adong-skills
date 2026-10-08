---
name: pm-next
description: "自动检测当前项目状态，建议或执行下一步。适合多会话间快速恢复。"
---

# /pm-next — 自动下一步

触发 `pm-skill`，检测当前 `.planning/` 状态并建议下一步。

## 工作流

1. **检测状态**：
   - 读取 `.planning/STATE.md` 获取当前位置
   - 读取 `.planning/ROADMAP.md` 了解阶段完成情况

2. **确定下一步**：

| 当前状态 | 下一步建议 |
|----------|-----------|
| 无 `.planning/` | `/pm-init` 初始化项目 |
| 阶段 N 无 PLAN.md | `/pm-plan N` 规划阶段 |
| 阶段 N 有 PLAN，无 SUMMARY | `/pm-execute N` 执行阶段 |
| 阶段 N 执行完成，无 VERIFICATION | `/pm-verify N` 验证阶段 |
| 阶段 N 验证通过 | `/pm-transition` 切换阶段 |
| `.continue-here.md` 存在 | 恢复中断的工作 |

3. **展示建议**：
   ```
   📍 当前状态: Phase {N} — {status}
   🚀 建议下一步: /pm-{command} {args}
   
   要执行吗？
   ```

4. **等待用户确认** → 执行建议的命令

## 关键规则

- 只建议，不自动执行
- 优先检测 `.continue-here.md`（中断恢复）
- 中文输出
