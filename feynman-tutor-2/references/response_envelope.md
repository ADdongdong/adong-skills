# 结构化响应协议（Response Envelope）

## 设计目的

为使同一份内核既能在纯聊天环境跑，又能在自研应用里驱动 UI，内核每条回复由两部分组成：

1. **自然语言正文**：给用户看的讲解/提问/反馈（纯聊天环境直接展示）
2. **可选元数据块**：用围栏标记 ` ```feynman ` 包裹的 JSON，供宿主解析渲染；纯聊天环境忽略此块

## Envelope 字段定义

```json
{
  "state": "LECTURE | HOMEWORK | ASSESS | PRACTICE | DIAGNOSE | REMEDIATE | MODULE_DONE | REVIEW",
  "ui": {
    "type": "text | choice_card | level_card | module_list | viz | feedback | practice_card | doc_archive",
    "payload": {}
  },
  "assessment": {
    "result": "pass | fail",
    "root_cause": "concept_confusion | missing_prereq | expression_issue | fatigue | exhausted",
    "concept_id": "concept-id",
    "mastered": true,
    "next_action": "advance | practice | skip_practice | remediate_lecture | remediate_homework | insert_prereq | rest | lower_goal"
  },
  "mastery_updates": [
    { "concept_id": "concept-id", "mastery": "strong" }
  ],
  "archive": {
    "lecture": "<<markdown>>",
    "chatlog": "<<markdown>>",
    "homework": "<<markdown>>"
  }
}
```

## 字段使用约定

- 仅当需要宿主渲染卡片/动画/更新状态/归档文档时，才附带 ` ```feynman ` 块
- 普通讲解、追问只用自然语言正文，不强制带块
- `assessment` 仅在 `ASSESS` / `DIAGNOSE` 状态出现，是决策树机器执行的唯一依据
- 宿主解析失败时，降级为纯文本展示（内核正文始终自包含、可读）

## UI 类型说明

| ui.type | 用途 |
|---|---|
| `text` | 普通文本讲解 |
| `choice_card` | 选择题卡片（目标分级、模块跳过等） |
| `level_card` | 3 级目标选择卡（上下文模式可附 `inferred` 与 `reason`，用于预选并展示推断依据） |
| `module_list` | 模块列表展示 |
| `viz` | 可视化图表（SVG/Mermaid 等） |
| `feedback` | 结构化评估反馈 |
| `practice_card` | PRACTICE 情境题卡片 |
| `doc_archive` | 模块完成归档文档 |
