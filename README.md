# adong-skills

我的 skill 总目录 —— 按**功能**分 6 类，共 50 个条目。

- **自建 skill 放文件本体**：克隆下来就能装，各自 `SKILL.md` / `scripts` / `references` 完整随行。
- **收藏 skill 只做索引**：登记用途、触发场景、上游地址与安装方式，**不搬运他人代码**（唯一例外见 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)）。

## 统计

| 分类 | 中文 | 条目 | 自建 | 收藏 |
|---|---|---|---|---|
| [`01-web-ui`](01-web-ui) | 网页与界面 | 15 | 1 | 14 |
| [`02-visuals`](02-visuals) | 图表与图像 | 14 | 1 | 13 |
| [`03-content-pipeline`](03-content-pipeline) | 内容流水线 | 13 | 0 | 13 |
| [`04-presentation`](04-presentation) | 演示与幻灯片 | 2 | 0 | 2 |
| [`05-dev-tooling`](05-dev-tooling) | 工程与系统工具 | 3 | 3 | 0 |
| [`06-learning`](06-learning) | 学习与表达 | 3 | 1 | 2 |
| **合计** | | **50** | **6** | **44** |

## 怎么用这个仓库

**先认形态**，两种形态一眼可辨：

| 形态 | 长什么样 | 含义 |
|---|---|---|
| **自建** | 一个**目录**，里面必有 `SKILL.md` | 本体在这，直接装 |
| **收藏** | 一个**单文件 `.md`**，文件名 = 上游仓库名（如 `ui-skills.md`） | 只是索引，按里面的指引回上游装 |

**装自建 skill**：把整个目录复制到 `~/.codebuddy/skills/<name>/`，重启宿主即生效。

**选收藏 skill**：打开同目录下的索引 `.md`，里面逐条写了用途、触发场景与安装方式。

**同一个上游可能出现在多个分类**（`baoyu-skills` 在 3 个、`garden-skills` 在 5 个）：那是**有意分片**，每个分片只列属于本类的 skill，文件头会给出合集总览与跨类跳转。

## 01-web-ui — 网页与界面（15）

### A1 设计语言与规范

| Skill | 用途 | 来源 | 索引 |
|---|---|---|---|
| `awesome-design-md` | 74 个品牌的 `DESIGN.md` 设计语言库 —— 要"照着 X 的样子做"时取它的令牌、字体与组件规则 | 自建 | [目录](01-web-ui/awesome-design-md/) |
| `create-design-md` | 从既有仓库或线上站点产出一份 `DESIGN.md`，给编码 agent 一份长期界面上下文 | 收藏 | [ui-skills](01-web-ui/ui-skills.md) |
| `design-artifact` | HTML 制品的设计原则与创意方向：配色、字体搭配、布局、主题、整体气质 | 收藏 | [effective-html](01-web-ui/effective-html.md) |
| `web-design-engineer` | 用 HTML / CSS / JS / React 构建或重设计浏览器渲染的视觉制品 | 收藏 | [garden-skills](01-web-ui/garden-skills.md) |
| `ui-skills-root` | UI 任务动工前，用 CLI 选出**最小够用**的 UI skill 上下文 | 收藏 | [ui-skills](01-web-ui/ui-skills.md) |

### A2 界面质量修复

| Skill | 用途 | 来源 | 索引 |
|---|---|---|---|
| `baseline-ui` | 快速清理 UI 代码的间距、层级、排版与小布局问题 | 收藏 | [ui-skills](01-web-ui/ui-skills.md) |
| `improve-ui` | 对现有界面做**只读**审计，写出可交给另一个 agent 实施的改进计划 | 收藏 | [ui-skills](01-web-ui/ui-skills.md) |
| `fixing-accessibility` | 审计并修复无障碍问题：ARIA、键盘导航、焦点管理、对比度、表单报错 | 收藏 | [ui-skills](01-web-ui/ui-skills.md) |
| `fixing-metadata` | 审计并修复 HTML 元数据：SEO、OG、Twitter card、favicon、JSON-LD、robots | 收藏 | [ui-skills](01-web-ui/ui-skills.md) |
| `fixing-motion-performance` | 审计并修复动画性能：布局抖动、合成属性、滚动联动、模糊效果 | 收藏 | [ui-skills](01-web-ui/ui-skills.md) |

### A3 HTML 产物与原型

| Skill | 用途 | 来源 | 索引 |
|---|---|---|---|
| `html` | 产出/改版**自包含单文件 HTML 制品**（报告、解说、落地页、演示、工具）—— 本合集的**唯一隐式路由** | 收藏 | [effective-html](01-web-ui/effective-html.md) |
| `html-wireframe` | 低保真 HTML 线框，在设计之前验证信息层级、内容、导航与任务流 | 收藏 | [effective-html](01-web-ui/effective-html.md) |
| `html-prototype` | 精细、响应式的 HTML 原型与交互稿 | 收藏 | [effective-html](01-web-ui/effective-html.md) |
| `html-plan` | 自包含 HTML 计划：保留原始材料，改进层级、顺序、归属、依赖与可评审性 | 收藏 | [effective-html](01-web-ui/effective-html.md) |
| `html-diagram` | 自包含 HTML 图表：用布局、符号与交互澄清关系、时序、拓扑、状态、层级 | 收藏 | [effective-html](01-web-ui/effective-html.md) |

> A3 中除 `html` 外都是**显式调用专项**，只在点名或由 `html` 路由时才启用。

## 02-visuals — 图表与图像（14）

### B1 图表与架构图

| Skill | 用途 | 来源 | 索引 |
|---|---|---|---|
| `mermaid-doc-renderer` | 把 Mermaid 渲染成高清 PNG / SVG / PDF，并把含 Mermaid 的 Markdown 转成无 Markdown 痕迹的 Word | 自建 | [目录](02-visuals/mermaid-doc-renderer/) |
| `archify` | 可探索的独立 HTML + 内联 SVG 架构图 / 工作流 / 时序 / 数据流 / 生命周期图，支持明暗主题、轨迹动效与 PNG/JPEG/WebP/SVG/**WebM** 导出 | 收藏 | [archify](02-visuals/archify.md) |
| `architecture-diagram-generator` | 暗色主题、自包含 HTML + SVG 的架构图（系统 / 基础设施 / 云 / 安全 / 网络拓扑） | 收藏 | [repo](02-visuals/architecture-diagram-generator.md) |
| `excalidraw-diagram-skill` | 生成 **Excalidraw JSON** 图表（可继续手改）；⚠️ 上游**未声明许可证** | 收藏 | [repo](02-visuals/excalidraw-diagram-skill.md) |
| `baoyu-diagram` | 专业暗色主题 **SVG** 图：架构 / 流程 / 时序 / 结构 / 思维导图 / 时间线 / 概念图 | 收藏 | [baoyu-skills](02-visuals/baoyu-skills.md) |
| `baoyu-infographic` | 21 种版式 × 22 种视觉风格的可发布级信息图 | 收藏 | [baoyu-skills](02-visuals/baoyu-skills.md) |

### B2 生成式图像

| Skill | 用途 | 来源 | 索引 |
|---|---|---|---|
| `gpt-image-2` | 面向 GPT Image 2 的生成/编辑：18 大类、80+ 结构化模板，含 Advisor 降级模式 | 收藏 | [garden-skills](02-visuals/garden-skills.md) |
| `ian-xiaohei-illustrations` | Ian 风格**中文正文配图**：小黑 IP、纯白手绘、少量红橙蓝批注 | 收藏 | [repo](02-visuals/ian-xiaohei-illustrations.md) |
| `baoyu-image-gen` | 多后端 AI 出图（OpenAI / Azure / Google / OpenRouter / DashScope / GLM / MiniMax / 即梦 / Seedream / Replicate …），可按 prompt 文件批量 | 收藏 | [baoyu-skills](02-visuals/baoyu-skills.md) |
| `baoyu-article-illustrator` | 分析文章结构、定位配图位置，按「类型 × 风格 × 配色」生成插图 | 收藏 | [baoyu-skills](02-visuals/baoyu-skills.md) |
| `baoyu-cover-image` | 文章封面图：11 种配色 × 7 种渲染风格，2.35:1 / 16:9 / 1:1 | 收藏 | [baoyu-skills](02-visuals/baoyu-skills.md) |
| `baoyu-comic` | 知识漫画：多画风多语气、详细分镜版式、批量出图 | 收藏 | [baoyu-skills](02-visuals/baoyu-skills.md) |
| `baoyu-xhs-images` | 信息图卡片系列：12 风格 × 8 版式 × 3 配色，拆成 1~10 张卡片 | 收藏 | [baoyu-skills](02-visuals/baoyu-skills.md) |
| `baoyu-compress-image` | 图片压缩为 WebP（默认）或 PNG，自动选工具 | 收藏 | [baoyu-skills](02-visuals/baoyu-skills.md) |

## 03-content-pipeline — 内容流水线（13）

按数据流向排列：抓取 → 整形 → 分发。

| Skill | 用途 | 来源 | 索引 |
|---|---|---|---|
| `beautiful-article` | 素材（URL / PDF / DOCX / MD / 纯文本 / 截图）编辑设计成**可离线分享的单文件 HTML 网页文章** | 收藏 | [garden-skills](03-content-pipeline/garden-skills.md) |
| `baoyu-url-to-markdown` | 抓任意 URL 转 markdown（内置 X / YouTube / Hacker News 适配器，走 Chrome CDP） | 收藏 | [baoyu-skills](03-content-pipeline/baoyu-skills.md) |
| `baoyu-youtube-transcript` | 下载 YouTube 字幕 / 转录与封面图，支持多语言、翻译、章节、说话人识别 | 收藏 | [baoyu-skills](03-content-pipeline/baoyu-skills.md) |
| `baoyu-danger-x-to-markdown` | X（Twitter）推文与文章转带 frontmatter 的 markdown（⚠️ 逆向 API，需先同意） | 收藏 | [baoyu-skills](03-content-pipeline/baoyu-skills.md) |
| `baoyu-danger-gemini-web` | 逆向 Gemini Web API 出图 / 出文，支持参考图与多轮（⚠️ 需先同意） | 收藏 | [baoyu-skills](03-content-pipeline/baoyu-skills.md) |
| `baoyu-electron-extract` | 从已安装 Electron 应用的 `.asar` 提取资源与 JS，尽量还原源码 | 收藏 | [baoyu-skills](03-content-pipeline/baoyu-skills.md) |
| `baoyu-format-markdown` | 给纯文本或 markdown 补 frontmatter、标题、摘要、分级标题、加粗、列表、代码块 | 收藏 | [baoyu-skills](03-content-pipeline/baoyu-skills.md) |
| `baoyu-markdown-to-html` | markdown 转带样式 HTML（微信兼容主题），支持代码高亮、数学、Mermaid 转 PNG、PlantUML、脚注 | 收藏 | [baoyu-skills](03-content-pipeline/baoyu-skills.md) |
| `baoyu-translate` | 翻译三模式（快翻 / 常规 / 精翻）+ 自定义术语表 | 收藏 | [baoyu-skills](03-content-pipeline/baoyu-skills.md) |
| `baoyu-post-to-wechat` | 发布到**微信公众号**：文章（HTML / markdown / 纯文本）与贴图 | 收藏 | [baoyu-skills](03-content-pipeline/baoyu-skills.md) |
| `baoyu-post-to-weibo` | 发布到**微博**：普通微博与 markdown 头条文章 | 收藏 | [baoyu-skills](03-content-pipeline/baoyu-skills.md) |
| `baoyu-post-to-x` | 发布到 **X**：普通推文与 X Articles 长文 | 收藏 | [baoyu-skills](03-content-pipeline/baoyu-skills.md) |
| `baoyu-wechat-summary` | 用本地 `wx-cli` 把微信**群聊精华**总结成结构化摘要（含历史、画像与隐私护栏） | 收藏 | [baoyu-skills](03-content-pipeline/baoyu-skills.md) |

## 04-presentation — 演示与幻灯片（2）

| Skill | 用途 | 来源 | 索引 |
|---|---|---|---|
| `baoyu-slide-deck` | 从内容生成**幻灯片图片**：先出带风格指令的大纲，再逐页出图 | 收藏 | [baoyu-skills](04-presentation/baoyu-skills.md) |
| `web-video-presentation` | 文章 / 口播稿转**点击驱动的 16:9 网页演示**，可合成口播音频（内置 MiniMax 与 OpenAI TTS） | 收藏 | [garden-skills](04-presentation/garden-skills.md) |

## 05-dev-tooling — 工程与系统工具（3）

| Skill | 用途 | 来源 | 索引 |
|---|---|---|---|
| `xd-dev-handbook` | Spring Boot + UmiJS 全栈编码规范 | 自建 | [目录](05-dev-tooling/xd-dev-handbook/) |
| `hahadong-push-github` | 把任意本地目录一键推送到 GitHub：自动取本机凭据、不使用代理、密钥不入库 | 自建 | [目录](05-dev-tooling/hahadong-push-github/) |
| `c-drive-cleanup` | Windows C 盘清理与 Junction 迁移全流程：五分类、命令安全分级、可续跑状态机、四道备份门（含真实事故复盘） | 自建 | [目录](05-dev-tooling/c-drive-cleanup/) |

## 06-learning — 学习与表达（3）

| Skill | 用途 | 来源 | 索引 |
|---|---|---|---|
| `feynman-tutor-skill` | 费曼学习法 · 真懂教练：用生活类比开场、追问复述、诊断卡点，确保真学懂而非假装学懂 | 自建 | [目录](06-learning/feynman-tutor-skill/) |
| `vibe-hub-skill` | 在 Vibe Coding 全程持续识别准确术语，给通俗解释与 VibeHub 内链（含术语解析脚本） | 收藏 | [vibe-hub-skill](06-learning/vibe-hub-skill.md) |
| `kb-retriever` | 本地知识库目录的分层检索与问答（按文件类型组合 grep / pdfplumber / pandas 渐进检索） | 收藏 | [garden-skills](06-learning/garden-skills.md) |

## 来源与许可

- 自建内容适用根目录 [`LICENSE`](LICENSE)（MIT）。
- 44 个收藏条目**只登记出处、不再分发代码**；9 个上游仓库的来源、许可与权利人逐条登记在 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)。
- ⚠️ 其中 `coleam00/excalidraw-diagram-skill` **未声明许可证**（默认「保留所有权利」），复用前请先向上游确认。
- **唯一完整再分发**的是 `01-web-ui/awesome-design-md/design-md/` 内的 74 份 `DESIGN.md`（上游 MIT）；该 skill 的 `SKILL.md` 为本仓库作者自写。

## 对上游做过的改动

全部改动（只有 1 处，外加 1 项元数据剔除）逐条记在 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md#本仓库对自建内容做过的改动仅-1-处)。除此之外，所有自建 skill 的 `SKILL.md` **保持原样未改** —— 它们同时是 skillhub 等平台按 frontmatter 解析的输入。
