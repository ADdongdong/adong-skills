---
name: pm-transition
description: "完成当前阶段，更新 PROJECT/ROADMAP/STATE，准备下一阶段。"
---

# /pm-transition — 阶段切换

触发 `pm-skill`，完成当前阶段并过渡到下一阶段。

## 工作流

1. **验证当前阶段** — 参考 `workflows/transition.md`：
   - 所有 PLAN.md 都有对应的 SUMMARY.md
   - VERIFICATION.md 存在且无关键缺口
   - STATE.md 反映了最新状态

2. **更新 PROJECT.md**：
   - 将已完成的需求从 Active 移到 Validated
   - 添加本阶段的关键决策
   - 更新产品上下文（新发现的知识）

3. **更新 ROADMAP.md**：
   - 标记当前阶段为完成（✅ + 完成日期）
   - 更新进度表
   - 标记下一阶段为「就绪」

4. **更新 STATE.md**：
   - 更新当前阶段位置
   - 更新进度条
   - 记录本阶段的 velocity 数据
   - 保留关键决策和待处理 TODO

5. **过渡检查点** — 参考 `workflows/transition.md`：
   - 展示：完成总结 + 下一阶段预览
   - STOP → 等待用户确认切换

## 产出物

- 更新的 `PROJECT.md`
- 更新的 `ROADMAP.md`
- 更新的 `STATE.md`

## 关键规则

- 必须验证当前阶段完整（所有 SUMMARY + VERIFICATION 存在）
- 不要跳过阶段 — 按 ROADMAP.md 顺序执行
- STATE.md 保持 < 100 行
- 中文输出

## 阶段类型过渡建议

完成后，Agent 会建议下一阶段类型：

```
当前阶段: 01-发现     → 建议下一阶段: 02-策略
当前阶段: 02-策略     → 建议下一阶段: 03-PRD
当前阶段: 03-PRD      → 建议下一阶段: 04-执行
当前阶段: 04-执行     → 建议下一阶段: 05-发布
当前阶段: 05-发布     → 🎉 项目完整！建议 /pm-health 最终检查
```
