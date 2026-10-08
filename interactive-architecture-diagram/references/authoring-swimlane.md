# 顺序泳道

适用于多角色按一条确定顺序交接任务，可跨多个阶段。优先 JSON，不用模型计算时间槽、连线路径或空白占位。

```json
{
  "kind":"swimlane",
  "title":"订单交接",
  "lanes":[{"id":"wms","label":"WMS","kind":"system"},{"id":"operator","label":"操作员","kind":"person"}],
  "phases":[{"label":"下发与确认","steps":[{"lane":"wms","text":"下发任务","next_label":"任务单"},{"lane":"operator","text":"确认接收","next_kind":"reply"},{"lane":"wms","text":"记录确认结果"}]}]
}
```

- `lanes` 按画面中的泳道顺序排列，2–10 个；`id` 唯一，须匹配 `[A-Za-z][A-Za-z0-9_]{0,31}`，动作的 `lane` 引用它。
- `phases` 按阶段顺序排列，1–12 个；每阶段的 `steps` 按执行顺序排列，全图 2–120 步。
- `next_label` 和 `next_kind` 描述该动作到下一个动作的交接；`next_kind` 为 `flow`（默认）或 `reply`。最后一步不写后继字段。
- `orientation` 可选 `vertical`（默认）或 `horizontal`；其余宽高、换行和路由都由模板决定。
- 分支、并行、循环和多条独立路径不适配本版。保留完整业务要求，走 general，不要强行压成单一路径。
- 规范模型会包装为 `kind: "swimlane"`、`template`、`template_version`、`spec` 等字段，并补齐 ID；后续直接修改规范模型的 `spec`，保留已有 ID。
