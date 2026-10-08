---
name: pm-todo
description: "项目 TODO 管理。支持添加、查看、完成待办事项。"
argument-hint: "[add <text> | list | done <id>]"
---

# /pm-todo — TODO 管理

触发 `pm-skill`，管理 `.planning/TODOS.md`。

## 工作流

1. **`/pm-todo list`** — 查看 TODO：
   - 读取 `.planning/TODOS.md`（如不存在，使用 `templates/TODO.md` 创建）
   - 按优先级分组展示

2. **`/pm-todo add <description>`** — 添加 TODO：
   - 分配 ID（TODO-001, TODO-002...）
   - 设置默认优先级 P1
   - 追加到 TODOS.md

3. **`/pm-todo done <id>`** — 标记完成：
   - 将指定 TODO 从 Pending → Done
   - 记录完成日期

## 优先级

| 优先级 | 含义 |
|--------|------|
| P0 | 阻塞当前阶段 |
| P1 | 本阶段内处理 |
| P2 | 可延后 |

## 关键规则

- TODO.md 遵循 `templates/TODO.md` 模板
- ID 格式：TODO-{序号}
- 中文输出
