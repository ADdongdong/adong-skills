# archify

> **上游**：<https://github.com/tt-a1i/archify> · MIT · 68.6k★ · 站点 <https://tt-a1i.github.io/archify/>
> **本类收录 1 个**：图表与架构图。另有 `DESIGN.md` / `PRODUCT.md` / `ROADMAP.md` 等仓库级文档，与 skill 本身无关。
> **上游路径根**：`archify/`（另有 `archify.zip` 打包件与 `viewer/`、`examples/`、`benchmarks/` 等）
> **安装**：把上游 `archify/` 目录复制到 `~/.codebuddy/skills/archify/`。
> **本机已安装**：`~/.codebuddy/skills/archify/`。本账号也已将该仓库 fork 到 `ADdongdong/archify`。

## B1 图表与架构图

| Skill | 用途与触发场景 |
|---|---|
| `archify` | 产出**精致且经过校验**的架构图、工作流图、时序图、数据流图、生命周期 / 状态图 —— 形式是可探索的**独立 HTML（内联 SVG）**，支持明暗主题、可选的轨迹动效，以及 PNG / JPEG / WebP / SVG / WebM 导出。输入可以是自然语言需求，也可以直接粘贴 Mermaid（`flowchart` / `sequenceDiagram` / `stateDiagram`）；当图需要反映真实代码时，会去仓库里找证据。触发：可视化系统架构、基础设施、云 / 安全 / 网络拓扑。 |

## 在 02-visuals 里怎么选

本项目 02-visuals 的 B1 组有 4 个"出图"skill，分工如下：

| 想要 | 用 |
|---|---|
| **可探索的独立 HTML**、能导出 PNG/JPEG/WebP/SVG/**WebM**、支持粘贴 Mermaid 或读仓库证据 | `archify`（本项） |
| 暗色主题、自包含 HTML+SVG 的架构图（系统 / 基础设施 / 云 / 安全 / 网络拓扑） | [`architecture-diagram-generator`](architecture-diagram-generator.md) |
| **SVG 源文件**，覆盖架构/流程/时序/结构/思维导图/时间线等更宽的图种 | [`baoyu-diagram`](baoyu-skills.md) |
| 生成 **Excalidraw JSON**，之后还要在 Excalidraw 里继续手改 | [`excalidraw-diagram-skill`](excalidraw-diagram-skill.md) |
