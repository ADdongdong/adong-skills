# architecture-diagram-generator

> **上游**：<https://github.com/Cocoon-AI/architecture-diagram-generator> · MIT · Copyright (c) 2025 Cocoon AI · 7.3k★
> **本类收录 1 个**：图表与架构图。
> **上游路径根**：`architecture-diagram/`（仓库根还有 `architecture-diagram.zip` 打包件与 `examples/`）
> **安装**：把上游 `architecture-diagram/` 目录复制到 `~/.codebuddy/skills/architecture-diagram/` —— **注意目录名是 `architecture-diagram`，不是仓库名**。
> 本机 `~/.codebuddy/skills/` 下**未安装**。

## B1 图表与架构图

| Skill | 用途与触发场景 |
|---|---|
| `architecture-diagram` | 生成精致、**暗色主题**的架构图，形式是**自包含的 HTML + SVG 单文件**。触发：系统架构图、基础设施图、云架构、安全拓扑、网络拓扑。 |

## 特点与边界

- 产物是**单文件 HTML**（内联 SVG），可直接在浏览器打开或分享，不需要额外依赖。
- 风格是**固定的暗色主题** —— 如果需求明确要浅色，或要可切换明暗主题，改用 [`archify`](archify.md)。
- 与 `baoyu-diagram` 的区别：后者输出**纯 SVG**、图种更宽（时序图、思维导图、时间线等），前者聚焦架构类且输出 HTML 包装。

## 02-visuals 出图项选择速查

| 想接着做什么 | 选它 |
|---|---|
| 浏览器直接打开 / 分享链接 | `architecture-diagram-generator`、`archify` |
| 在 Excalidraw 里继续手改 | [`excalidraw-diagram-skill`](excalidraw-diagram-skill.md) |
| 拿到可嵌入文档的 SVG 源文件 | [`baoyu-diagram`](baoyu-skills.md) |
| 导出动图 / 视频（WebM） | [`archify`](archify.md) |
