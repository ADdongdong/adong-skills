# effective-html — HTML 产物与原型

> **上游**：<https://github.com/plannotator/effective-html> · MIT · 3.2k★
> **本类收录 6 个**：全部属于本分类，不跨分类 —— 本文件即该合集的完整索引。
> **上游路径根**：`skills/<name>/`
> **安装**：`npx skills add plannotator/effective-html`；或把上游 `skills/<name>/` 目录复制到 `~/.codebuddy/skills/<name>/`。
> 本机 `~/.codebuddy/skills/` 下这 6 个**都已安装**。

## A1 设计语言与规范

| Skill | 用途与触发场景 |
|---|---|
| `design-artifact` | HTML 制品的设计原则与创意方向 —— 页面、报告、计划、落地页、演示、小工具的配色、字体搭配、布局、主题与整体气质。触发：产出或改版任何视觉类 HTML 交付物，或要求"不要长得像 AI 生成的"。 |

## A3 HTML 产物与原型

| Skill | 用途与触发场景 |
|---|---|
| `html` | 产出或改版**自包含单文件 HTML 制品**，视觉方向由需求、项目与题材共同决定。触发：HTML 本身就是交付物 —— 报告、解说、落地页、演示、工具、混合型产物，或需求较宽泛时。**本合集的唯一隐式路由**。 |
| `html-wireframe` | 低保真 HTML 线框，**在视觉设计之前**验证信息层级、内容、导航、任务流与响应式结构。触发：显式点名 `html-wireframe`，或由 `html` 路由过来。 |
| `html-prototype` | 精细、响应式的 HTML 原型/交互稿，基于对话上下文、产品语境与设计语言。触发：显式点名 `html-prototype`，或由 `html` 路由过来。 |
| `html-plan` | 自包含 HTML 计划：保留原始材料，同时改进行层级、顺序、归属、依赖与可评审性。触发：显式点名 `html-plan`，或由 `html` 路由过来。 |
| `html-diagram` | 自包含 HTML 图表：用布局、符号与交互澄清关系、时序、拓扑、状态、层级或数量结构。触发：显式点名 `html-diagram`，或由 `html` 路由过来。 |

## 关键调用纪律（上游明确要求，务必遵守）

- `html` 是**唯一允许隐式激活**的项，它负责把线框 / 原型 / 计划 / 图表类请求**路由**给对应专项。
- `design-artifact` 之外的四个专项（`html-wireframe`、`html-prototype`、`html-plan`、`html-diagram`）是**显式调用专项**：只在你点名叫它，或 `html` 把请求路由过来时才启用，**不得因一个泛泛的请求自行激活**。
- `html` 不用于普通应用实现 —— 那是写代码，不是产出 HTML 制品。
