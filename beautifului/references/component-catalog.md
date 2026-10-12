# Beautiful UI 组件目录

来源：上游 `lib/meta.ts`（画廊清单）+ `public/r/*.json`（registry 条目）。
21 个组件，全部 **MIT**，作者 Shane Levine（Turbo）。上游栈：Next.js 15 / React 19 / Tailwind CSS v4 / TS。

> 本目录的 `npm` 一列是**上游原始依赖**。本 skill 的 HTML 移植版已经把能内联的都内联、
> 把 `glimm` / `liveline` / `iconoir-react` / `@central-icons-react` 全部降级替换，**移植版零依赖**。

## 速查表

| # | slug | 中文名 | 上游变体 | 上游共享依赖 | 上游 npm 依赖 |
|---|---|---|---|---|---|
| 01 | `loading-state` | 加载状态 | Drive / Dots / Orbit / Surfer | — | — |
| 02 | `thinking-state` | 思考轨迹 | Steps / Reasoning / Search / Coding | — | — |
| 03 | `streaming-text` | 流式回答 | — | — | — |
| 04 | `approval-card` | 审批卡片 | — | Button, GlideMenu | — |
| 05 | `tool-chips` | 工具调用芯片 | — | — | — |
| 06 | `task-rows` | 任务进度行 | Capsules / List | — | — |
| 07 | `chat-composer` | 聊天面板 | — | — | — |
| 08 | `prompt-bar` | 提示栏 | Rounded / Pill | — | **glimm** |
| 09 | `recommendation-card` | 推荐卡片 | — | Button, EntityChip, ValuePill | — |
| 10 | `context-cards` | 上下文卡片 | — | — | — |
| 11 | `diff-table` | 差异表格 | — | Button | — |
| 12 | `records-table` | 记录表格 | — | GlideMenu | — |
| 13 | `filter-table` | 筛选表格 | — | — | — |
| 14 | `sidebar-nav` | 侧边导航 | — | GlideMenu | **@central-icons-react（付费）** |
| 15 | `search` | 命令搜索 | — | GlideMenu | — |
| 16 | `flowchart` | 流程图 | — | — | — |
| 17 | `insight-cards` | 洞察卡片 | — | — | **liveline** |
| 18 | `code-block` | 代码块 | Code / Diff | — | — |
| 19 | `fine-tune-card` | 微调卡片 | — | GlideMenu | — |
| 20 | `selection-actions` | 选区操作 | — | Button, Shimmer, StreamText | **iconoir-react** |
| 21 | `agent-screen` | 智能体屏幕 | Working / Loading | Button | — |

## 逐个说明

### 01 `loading-state` 加载状态
像素网格加载器 + 微光（shimmer）标签 + 实时计时器。
**用于**：不知道要等多久的操作。四种图案：Drive（方形格 + 人字形波前）、Dots（同波前、圆形格）、
Orbit（彗星绕网格一圈）、Surfer（Drive + 一段视频）。
**注意**：`pixel-on` 关键帧是逐格错开延迟形成波浪，周期 650ms（Drive/Dots）与 950ms（Orbit）。
`Surfer` 的上游视频托管在 Vercel Blob，离线时自动回退到占位。

### 02 `thinking-state` 思考轨迹
可展开的推理轨迹：Steps / Reasoning / Search / Coding 四类步骤，
折叠态显示「Thought for 4 seconds」，展开后逐步解析（带模糊消解）。
**用于**：把模型的思考过程摊开给用户看，满足"状态透明"与"可解释"。

### 03 `streaming-text` 流式回答
逐字流式输出 + 尾部模糊消解 + 内联来源芯片 + 操作行（复制/反馈/重试）+ 追问按钮。
**用于**：任何"答案正在生成"的场合。是 AI 产品最核心的一块。
**实现复用**：`atoms/StreamText`（字符揭示 + `.stream-tail` 模糊 + `.stream-caret` 光标）与 `atoms/Shimmer`。

### 04 `approval-card` 审批卡片
Human-in-the-loop：Agent 动手前先问用户。一次一个问题，支持单选/多选/自定义答案，Skip / Continue。
**用于**：不可逆或高影响动作前的确认（删数据、发消息、下单、改配置）。
**共享依赖**：Button、GlideMenu。

### 05 `tool-chips` 工具调用芯片
工具调用与代码编辑压缩成紧凑芯片，可展开看详情；文件 diff 用芯片 hover 预览
（上游用 **Popover API** 实现）。
**用于**：让"Agent 调了什么工具、改了什么文件"一目了然。

### 06 `task-rows` 任务进度行
实时任务状态：running / failed / completed，可展开详情。两种形态：Capsules / List。
**用于**：多步 Agent 流程的进度面板。

### 07 `chat-composer` 聊天面板
带标签页的聊天面板（如 Flavors / Suppliers），含推理回复、固定底部的消息流、输入 composer。
**用于**：完整的对话容器，比裸聊天气泡更接近真实产品。

### 08 `prompt-bar` 提示栏
输入编排器：`@` 引用来源、`/` 命令菜单、模型选择器、语音听写、附件芯片、发送/停止。Rounded / Pill 两种。
**用于**：AI 工具的主输入区。
**降级说明**：上游依赖 npm `glimm`（输入解析）。移植版改用原生 `<textarea>` + 自绘的 `@`/`/` 菜单，
保留键盘上下选择与 Esc 关闭。

### 09 `recommendation-card` 推荐卡片
Agent 建议 + 置信度仪表 + 备选抽屉 + Accept 操作。
**用于**：Agent 主动给建议、需要用户拍板的场景。

### 10 `context-cards` 上下文卡片
检索到的知识片段 + 来源（favicon 圆形头像，用 `.source-avatar`）。
**用于**：RAG 的"我参考了哪些资料"，提升可信度。

### 11 `diff-table` 差异表格
AI 提议的表格数据增删，逐格 diff 扫过（removals / additions）。
**用于**：Agent 改表格、批量改数据前的预览与确认。

### 12 `records-table` 记录表格
CRM 风格网格：标签、排序、关系状态、列选择，以及 Agent 提议的「Add calculation」计算列。
**用于**：结构化业务数据（客户、供应商、单据）的主视图。
**体量提示**：上游约 59KB 源码 + 825 行专用 CSS，是最大的一个。

### 13 `filter-table` 筛选表格
状态芯片（To do / In Progress / Completed）实时重组数据。
**用于**：任务看板式的状态过滤视图。

### 14 `sidebar-nav` 侧边导航
可折叠的工作区 + 聊天导航，带滑动（gliding）hover 高亮。
**用于**：AI 产品的应用外壳。
**降级说明**：上游 import **付费**图标库 `@central-icons-react`（12 个图标）。
移植版已全部替换为 lucide 等价图标（ISC），视觉略有差异。

### 15 `search` 命令搜索
命令面板式搜索：实时过滤 + 空状态 + 键盘导航。
**用于**：命令面板 / 快速跳转（⌘K 那类）。

### 16 `flowchart` 流程图
点阵画布上的工作流：触发器 + 条件步骤（If/Else）+ and/or 分支。
**用于**：让用户看懂 Agent 的编排逻辑，或可视化一条自动化流程。

### 17 `insight-cards` 洞察卡片
分页的 Agent 洞察，带可拖动 scrub 的实时图表与跟随游标的 tooltip。
**用于**：数据类 AI 产品的"洞察"模块。
**降级说明**：上游依赖 npm `liveline`（图表库）。移植版用自绘 SVG 折线/面积图，
并继续复用上游的 `.insight-chart-*` 类与 `--tooltip-*` 令牌。

### 18 `code-block` 代码块
带行号的代码列表 + 统一 diff（词级变更高亮）。Code / Diff 两种。
**用于**：回答里嵌代码、展示 Agent 的代码改动。

### 19 `fine-tune-card` 微调卡片
Agent 在设计检查器里调属性：W / H / Radius / Opacity%，可拖动、可滚轮。
**用于**："让用户直接调"的轻量参数面板——也是很好的交互范式参考。

### 20 `selection-actions` 选区操作
高亮一段文字后浮出操作行：Explain / Improve / Shorten / Tone / Grammar，
选择后原地流式重写。
**用于**：写作类 AI 工具的"选中即改"。
**降级说明**：上游依赖 `iconoir-react`；移植版改为内联 SVG。

### 21 `agent-screen` 智能体屏幕
观看 Agent 的屏幕：open / teach a task / record 三态，含自绘光标 `.agent-cursor`。Working / Loading 两种。
**用于**：让用户"看着 Agent 干活"，尤其适合计算机操作类 Agent。

## 共享原子（不单独出卡，但被多个组件引用）

| 原子 | 路径 | 被谁用 |
|---|---|---|
| `Button` | `components/atoms/Button.tsx` | approval-card、recommendation-card、diff-table、selection-actions、agent-screen |
| `GlideMenu` | `components/primitives/GlideMenu.tsx` | approval-card、records-table、sidebar-nav、search、fine-tune-card |
| `EntityChip` | `components/atoms/EntityChip.tsx` | recommendation-card |
| `ValuePill` | `components/atoms/ValuePill.tsx` | recommendation-card |
| `Shimmer` | `components/atoms/Shimmer.tsx` | **仅 selection-actions** |
| `StreamText` | `components/atoms/StreamText.tsx` | **仅 selection-actions** |

> ⚠️ **别把 `StreamText` 当 `streaming-text` 的依赖。** 这是最容易搞错的一处：
> 上游 `lib/meta.ts` 的 `INTERNAL` 表是「selection-actions 需要这些原子」，
> 不是「这些原子被哪些组件用」。`StreamingText.tsx` **不用** `StreamText` 也不用 `Shimmer` ——
> 它自己实现逐词揭示（注意是**逐词**，不是逐字，也没有 `.stream-tail` 尾部模糊），
> 而 `.stream-caret` 光标是它自己在组件样式里画的。
> 真正用 `StreamText`（逐字 + 尾部模糊 + 光标）的是 `SelectionActions.tsx`。

上游仓库另有 `Chip`、`StatusPill`、`SegmentedControl`、`ProgressRing`、`Switch`、`TextRow` 等原子，
同样在 `assets/upstream/components/atoms/` 中。

## registry 索引（26 项 + 1 个 style）

`assets/registry/registry.json` 是上游 registry 索引，共 27 条：
`foundation`（`registry:style`）+ 6 个 `registry:ui` 原子 + 20 个 `registry:component`。
`agent-screen` **不在 registry 里**（它依赖视频素材），只在仓库树与画廊里。

`assets/registry-offline/` 是同一批条目的改写版：`registryDependencies` 里的
`https://www.beautifului.dev/...` 绝对 URL 已被改写为相对文件名，供离线安装使用。
