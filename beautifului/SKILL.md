---
name: beautifului
description: >
  把 Beautiful UI（beautifului.dev，MIT，shadcn 注册表）的 21 个 AI 原生 UI 组件引入用户自己的项目，
  并按用户正在构建的 AI 工具/页面推荐该用哪几个组件。
  每个组件都同时提供**上游 React 原码**与**零依赖单文件 HTML 移植版**（动效与官网一致）。
  触发词：beautiful ui、beautifului、AI 组件库、AI 原生 UI、AI 界面组件、agent 界面、
  思考轨迹组件、thinking 组件、流式回答组件、streaming text、工具调用芯片、tool chips、
  审批卡片、approval card、人类确认、human-in-the-loop、任务进度、context cards、RAG 引用卡片、
  chat composer、prompt bar、命令搜索、sidebar nav、洞察卡片、diff 表格、records table、
  把 AI 界面的动效搬过来、AI 工具界面原型、agent 聊天界面长什么样、AI 产品该用什么组件。
  用于：取用组件源码（React 原样或 HTML 移植）、生成组件预览页、给出「场景 → 组件」推荐与搭建顺序。
  Not for：设计全新原创视觉体系或品牌（这套是克制的蓝调中性色 + 单一强调色风格，不做差异化品牌）；
  非 AI/LLM 的普通 CRUD 界面；纯后端或 CLI 工具；
  只想要配色、排版、阴影方案（那类用 better-colors / better-typography / beautiful-shadows / baseline-ui）。
agent_created: true
version: 1.0.0
display_name: "AI 原生 UI 组件库"
display_name_en: "AI-Native UI Component Library"
description_zh: "Beautiful UI（beautifului.dev，MIT）21 个 AI 原生 UI 组件的 React 原码与零依赖单文件 HTML 移植版，附断网可用预览页和场景到组件的推荐引擎。"
description_en: "Beautiful UI (beautifului.dev, MIT): 21 AI-native UI primitives shipped as both React source and zero-dependency single-file HTML, with an offline preview page and scenario-to-component recommendation engine."
author: "哈哈栋"
visibility: "public"
category: "web-ui"
---

# Beautiful UI 组件库

**Beautiful UI**（[beautifului.dev](https://www.beautifului.dev)，作者 Shane Levine / Turbo，**MIT**）
是一套面向 AI 原生界面的组件原语：加载状态、思考轨迹、流式回答、工具调用、任务进度、
人类审批、引用卡片、表格增删、命令搜索、洞察图表…… 共 **21 个**。

它和普通组件库的区别：普通设计系统解决「网站需要哪些基础组件」，
Beautiful UI 关注的是**当 AI 开始思考、用工具、改数据、提建议、准备动手时，界面该怎么向人交代**。

## 这个 skill 提供什么

| 轨道 | 产物 | 适合 |
|---|---|---|
| **A. React 原码** | `assets/upstream/**`（上游 .tsx 源码 + 令牌 CSS）+ `assets/registry-offline/*.json` | React 19 + Tailwind v4 项目 |
| **B. 单文件 HTML** | `assets/html/<slug>.html`（21 个，零依赖、动效一致） | Flask/任意 HTML/Vue/小程序/纯静态页 |
| **C. 只看与选型** | `assets/preview/index.html`（21 个真动效 demo 的离线预览页） | 想先看看再决定用哪些 |

**动效为什么能一致**：上游所有动效都是纯 CSS（设计令牌 + 8 个关键帧）+ React 定时器，
**没有任何组件用 framer-motion**。所以移植版只要时序常量照搬、颜色继续引用同名 `var(--token)`，手感就一样。

---

## 第一步（强制）：先搞清楚用户在建什么

**不要**一上来就甩组件清单。AI 产品的界面需求差异极大，「做个聊天界面」和「做个 Agent 控制台」
需要的组件几乎不重叠。

- 用户只说了「我要做一个 XX 的 AI 界面」→ 读 `references/recommendation-engine.md`，
  用其中的 **7 问 intake** 一次问完，再推荐。
- 用户贴了代码 / PRD / 截图 → 走**被动模式**：先列出你识别到的「AI 交互表面」并说明依据，
  再套路由表。
- 用户已经很明确要某个组件（例如「把 thinking 那个组件给我」）→ 跳过 intake，直接给。

推荐时**必须**按 `references/recommendation-engine.md` 里的强制格式输出，
且必须包含「不推荐」那一节 —— 明确排除能防止硬塞不合适的组件。

## 第二步：按技术栈选轨道

### 轨道 A：React 项目（React 19 + Tailwind v4）

读 `references/react-integration.md`。**关键前提：官网 registry 域名不保证可达**，
所以不要跑 `npx shadcn add https://www.beautifului.dev/r/...`，用离线路径：

1. **推荐**：从 `assets/upstream/components/{primitives,atoms}/` 手拷 `.tsx`，
   把 `assets/foundation.standalone.css` 作为令牌层引入，装 `clsx tailwind-merge class-variance-authority`。
2. 备选：`npx shadcn@latest add ./assets/registry-offline/<slug>.json`（依赖已改写成相对路径）。

**注意付费图标**：`sidebar-nav` 上游用付费的 `@central-icons-react`（12 个图标），
必须换成 `lucide-react`；`assets/html/sidebar-nav.html` 里已经换好了，可以参考其映射。

### 轨道 B：单文件 HTML（零依赖，直接可用）

直接把 `assets/html/<slug>.html` 整个文件给用户，或按需摘取它的 `<style>` + markup + `<script>`。

- 每个文件都**自包含**：内联了令牌层、该组件需要的工具类 CSS、以及它的 JS 状态机。
- 已经过离线渲染验证（无外部请求、无 JS 报错）。
- 每个文件右上角有个明暗主题切换按钮，便于直接检验两套令牌。
- **离线唯一损失**：Google Fonts（Inter / JetBrains Mono）加载不到时会回退到系统字体栈。
  要完全保真就把这两个字体本地化。

### 轨道 C：只要选型 / 想看效果

让用户打开 `assets/preview/index.html`（单文件、零构建、断网可开）。
里面内嵌了全部 21 个组件的**真实可交互 demo**，并附令牌色板、关键帧演示与场景路由表速查。

## 第三步：给方案，而不只是给组件

- 说明**为什么**选它（对应页面里哪个可见的元素/动作）。
- 说明**怎么串起来**（外壳 → 输入 → 过程 → 输出 → 确认 → 数据）。
- 如果用户要做真集成，指出**把哪个流式事件接到哪个组件**。
- 如果是 React 轨道，指出该组件还需要哪些**共享原子**（见 `references/component-catalog.md` 的依赖列）。

---

## 组件目录（21 个，速览）

完整说明、变体、依赖见 **`references/component-catalog.md`**。

- **状态与过程**：`loading-state` 加载状态 · `thinking-state` 思考轨迹 · `tool-chips` 工具调用芯片 · `task-rows` 任务进度行
- **对话与输出**：`streaming-text` 流式回答 · `chat-composer` 聊天面板 · `prompt-bar` 提示栏 · `code-block` 代码块 · `selection-actions` 选区操作
- **人机协同**：`approval-card` 审批卡片 · `recommendation-card` 推荐卡片
- **知识与数据**：`context-cards` 上下文卡片 · `records-table` 记录表格 · `diff-table` 差异表格 · `filter-table` 筛选表格 · `insight-cards` 洞察卡片
- **导航与检索**：`sidebar-nav` 侧边导航 · `search` 命令搜索
- **开发与流程**：`flowchart` 流程图 · `fine-tune-card` 微调卡片 · `agent-screen` 智能体屏幕

## 已知坑（都在文档里展开了）

- **`www.beautifului.dev` 与 `api.github.com` 不保证可达** → 别依赖官网 registry 命令，用离线路径。
- **`@theme inline` 里的 `--radius-*` / `--ease-*` / `--font-*` 必须搬进 `:root`**，
  否则圆角与缓动曲线静默丢失。详见 `references/foundation-tokens.md`。
- **`--shadow-btn/card/raised/overlay` 依赖 `shadow-plugin` 的 `--shadow-xs…lg`**，必须内联字面值。
- **上游组件是"自带动画的演示件"，不是数据接口**：它们跑自己的演示循环。
  接真实后端时要把内部 `useEffect` 换成你的事件流。
- **`sidebar-nav` 付费图标**：别直接拷上游 .tsx，先换掉 `@central-icons-react`。
- **npm 上有一个 5 年前的同名包 `beautiful-ui@1.0.31`**，与本项目无关，**不要 `npm i beautiful-ui`**。

## 自测与出处

- 移植件的渲染验证脚本：`scripts/verify_ports.cjs`（Playwright，逐张截图 + 收集报错 + 离线校验）。
- 令牌一致性自测：`scripts/make_foundation.py`（缺任一关键令牌会报警）。
- 完整自测报告：`v1.0.0-self-test.md`。

**许可证**：上游 MIT，Copyright (c) 2026 Shane Levine，原文见 `LICENSE.beautiful-ui`。
第三方依赖许可见 `THIRD_PARTY_NOTICES.md`。
版本与来源 commit 见 `assets/upstream/PROVENANCE.json`。

> 版权要求：以本 skill 为基础交付给第三方的产物，请保留上述署名。
