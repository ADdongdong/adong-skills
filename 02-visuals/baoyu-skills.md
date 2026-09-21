# baoyu-skills — 本类分片

> **合集总览**：21 个 skill，跨 3 个分类 · 上游 <https://github.com/JimLiu/baoyu-skills> · MIT · 26.0k★
> **本目录收录 8 个**：图表与架构图、生成式图像
> **其他分类**：[03-content-pipeline(12)](../03-content-pipeline/baoyu-skills.md) · [04-presentation(1)](../04-presentation/baoyu-skills.md)
> **上游路径根**：`skills/<name>/`（上游以 Claude 插件形式分发，另见 `.claude-plugin/`）
> **安装**：把上游 `skills/<name>/` 复制到 `~/.codebuddy/skills/<name>/`。
> 本机 `~/.codebuddy/skills/` 下这 21 个**均未安装**。
> ⚠️ 其中带 `danger-` 前缀的两个走**逆向工程 API**，上游明确要求先取得用户同意再用。

## B1 图表与架构图

| Skill | 用途与触发场景 |
|---|---|
| `baoyu-diagram` | 生成专业暗色主题的 **SVG 图**，覆盖架构图、流程图、时序图、结构图、思维导图、时间线、示意/概念图等。触发：任何技术或概念类的图 —— 系统架构、流程、数据流、组件关系、网络拓扑、决策树、组织架构、状态机，乃至任何用图形表达结构 / 逻辑 / 过程的需求。 |
| `baoyu-infographic` | 生成专业信息图：**21 种版式 × 22 种视觉风格**，会先分析内容再推荐「版式×风格」组合，产出可发布级信息图。触发：信息图、可视化摘要、高密度信息大图。 |

## B2 生成式图像

| Skill | 用途与触发场景 |
|---|---|
| `baoyu-image-gen` | 多后端 AI 图像生成：OpenAI GPT Image 2.5、Azure OpenAI、Google、OpenRouter、DashScope、Z.AI GLM-Image、MiniMax、即梦、Seedream、Replicate、Agnes。支持文生图、参考图、宽高比、按已保存 prompt 文件**批量**生成（默认串行；手头已有多个 prompt 或要稳定吞吐时走批量并行）。触发：生成 / 创建 / 绘制图片。 |
| `baoyu-article-illustrator` | 分析文章结构、定位需要配图的位置，按「**类型 × 风格 × 配色**」三维生成插图。触发：为文章配图 / 加图。 |
| `baoyu-cover-image` | 生成文章封面图，5 个维度（类型、配色、渲染、文字、情绪）组合 **11 种配色 × 7 种渲染风格**，支持电影感 2.35:1、宽屏 16:9、方形 1:1。触发：生成封面图 / 做封面。 |
| `baoyu-comic` | 知识漫画创作：多画风多语气，带详细分镜版式，支持批量出图。触发：知识漫画、教育漫画、传记漫画、教程漫画、Logicomix 风格漫画。 |
| `baoyu-xhs-images` | 生成信息图卡片系列：**12 种风格 × 8 种版式 × 3 套配色**，把内容拆成 1~10 张卡通风图片卡片，面向社媒传播优化。触发：小红书图片 / 种草、小绿书、微信图文 / 贴图、图片卡片。 |
| `baoyu-compress-image` | 图片压缩为 WebP（默认）或 PNG，自动选择压缩工具。触发：压缩 / 优化图片、转 WebP、减小图片体积。 |

## 同合集其他分类

| 分类 | 数量 | 内容 |
|---|---|---|
| [03-content-pipeline](../03-content-pipeline/baoyu-skills.md) | 12 | 抓取（X / YouTube / 任意 URL / Electron 解包）、排版（markdown 补齐与转 HTML）、翻译、发布（微信 / 微博 / X）、群聊摘要 |
| [04-presentation](../04-presentation/baoyu-skills.md) | 1 | `baoyu-slide-deck` 幻灯片图片生成 |

## 选择提示

- **要"图"但不生成位图**（架构图、流程图、信息图版式）→ `baoyu-diagram`、`baoyu-infographic`
- **要 AI 画出来的图**（插图、封面、漫画、卡片）→ `baoyu-image-gen` 系（`article-illustrator` / `cover-image` / `comic` / `xhs-images` 都是它的场景化封装）
- **本合集与 02-visuals 内其他项的边界**：`baoyu-diagram` 出 **SVG**、`architecture-diagram-generator` 与 `archify` 出 **HTML+SVG**、`excalidraw-diagram-skill` 出 **Excalidraw JSON** 可继续手改 —— 想接着编辑就选后者。
