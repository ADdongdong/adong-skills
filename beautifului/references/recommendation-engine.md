# 推荐引擎：根据「你在做什么」选出该用的组件

这个文件是这个 skill 的核心价值所在 —— 组件本身只是素材，**选对**才有用。

## 两种触发模式

### 模式 A：交互式 intake（用户还没给代码）

用户说「我要做一个 XX 的 AI 界面/工具」时，**先问，再推**。不要跳过提问直接甩组件清单——
AI 产品的界面需求差异极大，「做个聊天界面」和「做个 Agent 控制台」需要的组件几乎不重叠。

用 `AskUserQuestion` 一次问完（7 问，别拆成七轮）：

| # | 问题 | 选项（≤4 个） |
|---|---|---|
| 1 | 这个页面/工具的核心动作是？ | 对话问答 / 生成与改写 / 编辑结构化数据 / 检索与引用 |
| 2 | AI 的输是流式的吗？ | 逐字流式 / 分步展示 / 一次性给完 |
| 3 | 要展示「思考过程 / 工具调用」吗？ | 都要 / 只要思考 / 只要工具 / 都不用 |
| 4 | 有人类审批/确认环节吗？ | 有，且动作不可逆 / 有，但可撤销 / 没有 |
| 5 | 会处理表格或结构化数据吗？ | 会改数据 / 只读展示 / 不涉及 |
| 6 | 目标技术栈？ | React 项目 / Flask+HTML 原型 / 纯静态页 |
| 7 | 需要给出引用来源（citations）吗？ | 需要 / 不需要 |

**问完再进路由表。** 第 6 问决定交付形态（见下文「按技术栈分流」）。

### 模式 B：被动推断（用户给了代码或需求文档）

用户直接贴代码、贴 PRD、或说「看看我这个页面该加什么」时：

1. 先读代码/需求，**逐条列出你识别到的「AI 交互表面」**（例如：有 `streaming` 状态、有 `tool_calls`、
   有 `<table>` 承载模型输出、有 confirm 弹窗、有 citation 字段……），并把识别依据指出来（文件+行号或需求原文）。
2. 再套路由表给推荐。
3. 如果凭据不足（比如代码里只有 UI 没有 AI 逻辑），**说明你推断了什么、依据是什么**，别装作很确定。

## 场景 → 组件路由表

| AI 产品表面 | 主推 | 备选 |
|---|---|---|
| 对话/问答容器 | `chat-composer`、`streaming-text` | `prompt-bar` |
| 主输入区（@ 来源 / 命令 / 模型选择） | `prompt-bar` | `chat-composer` |
| 流式答案 | `streaming-text` | `code-block`（答案含代码时） |
| 思考/推理轨迹 | `thinking-state`（Steps/Reasoning） | `tool-chips` |
| 工具调用 / 代码改动 | `tool-chips` | `diff-table`、`code-block` |
| 人类审批（不可逆动作） | `approval-card` | `selection-actions` |
| 多步任务进度 | `task-rows` | `loading-state` |
| 不确定时长的等待 | `loading-state` | `task-rows` |
| RAG 引用 / 知识片段 | `context-cards` | `streaming-text`（内联来源） |
| 表格数据改动 | `diff-table` | `records-table` |
| 结构化业务数据主视图 | `records-table` | `filter-table` |
| 状态过滤/看板 | `filter-table` | `search` |
| Agent 给建议、要用户拍板 | `recommendation-card` | `insight-cards` |
| 数据洞察 / 图表 | `insight-cards` | `recommendation-card` |
| 命令面板 / 快速跳转 | `search` | `sidebar-nav` |
| 应用外壳导航 | `sidebar-nav` | `search` |
| 流程编排可视化 | `flowchart` | `task-rows` |
| 回答里嵌代码 | `code-block` | `streaming-text` |
| 选中即改（写作类） | `selection-actions` | `approval-card` |
| 轻量参数面板 / 让用户直接调 | `fine-tune-card` | — |
| 让用户看 Agent 操作屏幕 | `agent-screen` | `task-rows` |

## 按技术栈分流（关键）

| 技术栈 | 交付方式 |
|---|---|
| **React 19 + Tailwind v4** | 走 React 轨道：`assets/registry-offline/<slug>.json` 本地安装，或从 `assets/upstream/` 手拷 `.tsx` + `foundation.standalone.css`。见 `react-integration.md` |
| **Flask + HTML / 任意静态页 / Vue / Angular / 小程序** | 走 HTML 轨道：直接把 `assets/html/<slug>.html` 整个文件（或它的 `<style>` + markup + `<script>`）搬过去。**零依赖** |
| **只是想要设计方案参考** | 给 `assets/preview/index.html`，让用户自己浏览 21 个真动效 demo |

## 组合顺序：不是给一堆组件，而是给一条搭建顺序

推荐时**必须**给出「页面里按什么顺序拼起来」，因为组件之间的 nesting 是有讲究的：

1. **外壳**：`sidebar-nav` → `search`（挂在导航里）
2. **输入**：`prompt-bar` 固定在底部
3. **过程**：`thinking-state` → `tool-chips` → `task-rows`（自上而下对应"想 → 做 → 汇报"）
4. **输出**：`streaming-text`（内含 `context-cards` 的来源、`code-block` 的代码）
5. **确认**：需要用户拍板时插入 `approval-card` / `recommendation-card`
6. **数据**：数据类产品再叠 `records-table` / `diff-table` / `filter-table` / `insight-cards`

## 强制输出格式

```
## 推荐清单
1. `<slug>` — 一句话用途
   - 为什么：<这个页面里的哪个元素/动作会触发它，要具体到用户看得见的东西>
   - 引入：React → assets/registry-offline/<slug>.json ／ HTML → assets/html/<slug>.html
   - 依赖：<无 / 需要哪个原子 / 上游 npm 包（移植版已降级）>
   - 保真：原样 ／ 简化（<具体差异>）
2. ...

## 不推荐（以及为什么）
- `<slug>` — 原因（例如"你这个流程不需要人工确认，审批卡是多余的"）

## 页面里的组合顺序
1. ...
2. ...

## 落地要点
- 需要把哪个流式事件接到哪个组件（如果用户在做真集成）
- 明暗主题怎么切（`.dark` 类挂在 <html> 或任意祖先元素上）
```

「不推荐」这一节不是凑数：**明确排除**能防止用户把不合适的组件硬塞进去，
也让推荐看起来是判断而不是罗列。

## 反向判断：什么时候不推荐

- 用户只是要配色/排版/字体 → 交给 `better-colors` / `better-typography` / `beautiful-shadows` / `baseline-ui`。
- 用户要做的是普通 CRUD 界面、不是 AI 交互 → 这套组件几乎都用不上，别硬推。
- 用户已经有了自己的设计系统 → 只推荐「结构/行为」参考，明确提醒不要连配色一起搬。
- 用户要品牌级原创视觉 → 这套是"克制的蓝调中性色 + 单一强调色"风格，不适合做差异化品牌。
