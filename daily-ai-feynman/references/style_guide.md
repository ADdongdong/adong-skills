# 排版与配色规范（清新简单 · 清新蓝）

## 主色与底色
- 主色（强调）：`#1c5fd9`（清新蓝）
- 正文文字：`#333333`
- 次级文字：`#666666`
- 分割线 / 边框：`#eaeaea`（浅灰）
- 小标题同主色，正文不加粗大段

### ⚠️ 硬规则：公众号正文**零背景**
- **不要任何背景色**（尤其禁止渲染主题自带的黄底 / 米底 / 色块），一律纯白。
- 区分层次只能用：**字色、字号、分割线**，不能用底色，也**不要用左侧竖线**（微信引用块竖条会挤窄内容区）。
- 实现保障：`publish_draft.cjs` 默认会在渲染后**剥掉 HTML 里所有 background 声明**
  （含 `background` / `background-*` / `bgcolor`）。确需保留时才加 `--keep-bg`。

原则：纯白底，浅灰分割，单一低饱和强调色，杜绝一切色块与高饱和撞色。

### ⚠️ 硬规则：正文开头**不重复大标题**
公众号后台标题栏已有标题，正文顶部不要再来一遍大字标题，直接进内容。
- MD 里第一行仍写 `# 标题`（脚本靠它提取草稿标题），
  但 `publish_draft.cjs` **渲染前会自动摘掉这一行**，正文从引语直接开始。
- 需要保留时才加 `--keep-h1`。

## 对话体区分（小白问 / 哈哈栋答）
正文用**普通段落 + 前缀标签**区分，**不要用 `>` 引用块**（微信会把引用块渲染成左侧灰色竖条，挤窄内容区）。直接用 emoji + 加粗名字前缀，文字拉满全宽：

```markdown
🧑 **小白**：Agent 和聊天机器人到底差在哪？

🧑‍🏫 **哈哈栋**：想象你让助理「帮我订明天去北京的票」……
```

intro / 过渡句也不要用 `>` 引用块，统一为普通段落，全篇无竖条。

**禁止**用底色块 / 引用块区分（蓝底/灰底/左侧竖条一律会被净化或挤窄）。每篇保持「小白问、哈哈栋答」一致即可。

## 公众号封面规范（主题文字 + 配图，21:9 + 1:1 封面对）

封面 = **主题文字 + 配图**，规格参照 guizang-social-card-skill 的公众号封面对标准，
手写 HTML → Playwright 截图产出。**不做纯文字封面。**

### 尺寸与用途
| 文件 | 尺寸 | 用途 |
|------|------|------|
| `cover.png` | 2100×900（21:9） | 草稿箱主封面（`--cover` 参数） |
| `cover_square.png` | 1080×1080（1:1） | 方形封面（公众号新版首图 / 跨平台复用） |
| `cover_preview.png` | 2400×984 | 配对预览（仅供人眼比对，不上传） |

### 版式：文字 + 真实照片
- **21:9**：左侧 1180px 文字轴（kicker → 短横线 → 大标题 → 副标题 → footer）
  ＋ 右侧 920px 照片出血（`background-size: cover`，左缘一条主色竖条分界）
- **1:1**：上方 600px 照片（左下角贴主色栏目标签）＋ 下方 480px 短标题区
- **配色**（与正文 SVG 插图统一）：accent `#1c5fd9`，paper `#ffffff`，ink `#111418`
- **字体栈**：Microsoft YaHei + Segoe UI，mono = Consolas
- 风格不设硬性约束，重点是**文字清晰 + 有真实画面**

## 配图来源（优先级从高到低）

**封面配图优先级 = ① baoyu AI 无字背景图（中文标题最稳）→ ② Unsplash 真实照片（默认，零积分）→ ③ 兜底（正文插图 / guizang 纹理）**

### 〇、baoyu AI 无字背景图（用 baoyu-cover-image，封面要中文标题时的推荐路线）
- 用 `baoyu-cover-image` 生成**无字或极少字**的主视觉（`--text none`），**禁止让 AI 直出中文长标题**（错字率高且无法程序修补）
- AI 图作为 cover.html 的 `{{配图绝对路径}}` 背景，标题/副标题由 HTML 叠字保证准确清晰
- 消耗积分 5-10/张；AI 图中文校验由用户人工把关；来源记 `assets/SOURCES.md`（注明 AI 生成）

### 一、Unsplash 真实照片（默认）
按推文**核心类比**取图——封面画面要能让人一眼联想到本篇讲的东西。

**关键词提炼**：用英文，取核心类比的**具象物**，不要抽象概念词。

| 推文主题 | 核心类比 | 搜索关键词 |
|----------|----------|-----------|
| 大模型缓存命中 | 看小说夹书签 | `bookmark-book` |
| AI Agent | 点外卖找跑腿 | `food-delivery-courier` |
| 复利 | 雪球越滚越大 | `snowball-rolling` |
| 除权除息 | 打折卖 | `discount-price-tag` |
| 上下文窗口 | 桌面放得下多少纸 | `cluttered-desk-papers` |

❌ 别搜 `artificial-intelligence` / `finance` 这类抽象词，出来全是俗套的电路板和K线图。

**执行步骤**：
1. WebFetch `https://unsplash.com/s/photos/<关键词>`
2. 挑 3 张**不带 `Unsplash+` 标记**的免费图（带 Unsplash+ 的是付费墙），取 download 链接里的 ID
3. `node scripts/fetch_photo.cjs <工作目录> <id1> <id2> <id3>`
4. 拼候选总览给用户挑

> ⚠️ **2026-09-11 实测：Unsplash 搜索页已挂 Anubis Proof-of-Work 反爬**
> （WebFetch 返回标题为 `Making sure you're not a bot!` 的挑战页，拿不到任何 photo id）。
> 遇到这种情况**直接切下面的「Pexels 路线」**，不要在 Unsplash 上继续试。

### 一·B、Pexels 真实照片（Unsplash 被反爬时的默认替代）

**搜索页 WebFetch 可用**（实测 2026-09-11），能直接拿到 photo id：
1. WebFetch `https://www.pexels.com/search/<英文关键词，空格用 %20>/`
   → 让它列出详情页 URL（形如 `https://www.pexels.com/photo/<slug>-<数字ID>/`），取结尾数字 ID
2. **CDN 直链下载**（无需走详情页，实测 200）：
   `https://images.pexels.com/photos/<ID>/pexels-photo-<ID>.jpeg?auto=compress&cs=tinysrgb&w=1920`
   带头 `User-Agent` + `Referer: https://www.pexels.com/` 更稳
3. 用 PIL 拼 2×2 候选总览给用户挑（`ImageFile.LOAD_TRUNCATED_IMAGES = True`）
4. 来源写进 `assets/SOURCES.md`（Pexels License：可商用、可修改、无需署名）

**必须注意的坑**：
- 🚫 **不要 curl 抓搜索页**：`unsplash.com` / `pexels.com` 搜索页有反爬（401/403/307）。
  Unsplash 能走通的只有 `/photos/<id>/download` 端点 → 302 到 `images.unsplash.com` CDN；
  Pexels 走 `images.pexels.com/photos/<id>/pexels-photo-<id>.jpeg` CDN 直链（实测 200）。
- 🚫 **PIL 读图库大图要开截断容错**：`ImageFile.LOAD_TRUNCATED_IMAGES = True`，
  否则报 `image file is truncated`。
- ⚠️ **`render_cover.cjs` 的自定义配图分支是死代码**（实测 2026-09-11）：脚本里
  `customExts` 与 `autoNames` 同为 `art.png/jpg/jpeg/webp`，`!autoNames.has(...)` 恒为 false，
  所以**放 `art.jpg` 不会被采纳，永远回落到 guizang 默认素材**。
  → 用真实照片时，**直接把 `cover.html` 里 `{{配图绝对路径}}` 换成写真路径**
  （`file:///E:/.../assets/cand1.jpg`，正斜杠、不编码中文，实测可加载），
  占位符一被替换，脚本整段解析逻辑跳过，CSS 变量就指向你的照片。

**版权**：Unsplash License 允许商用与修改，来源自动记入 `assets/SOURCES.md`。
可选在文末标 `Photo · Unsplash · @作者`。

### 二、复用正文 SVG 插图（兜底 A）
配图路径指向 `images/svg_1.png`。此时**不要用 `cover` 拉伸**，改成居中留白：
```css
background-color:var(--accent-soft);
background-image:var(--art);
background-size:88% auto;      /* 1:1 用 auto 82% */
background-repeat:no-repeat;
background-position:center;
```

### 三、guizang 纹理素材（兜底 B，纯图案无内容）
只在主题过于抽象、找不到合适照片时用。9 张 1920×1080 WebP：

| 分类 | 素材名 | 视觉特征 |
|------|--------|----------|
| style-B | `ikb-dot-gradient` | IKB 克莱因蓝点渐变（与 accent 最搭） |
| style-B | `lemon-green-dot-shadow` / `lemon-grid` / `safety-orange-halftone` | 绿点影 / 黄网格 / 橙半调 |
| style-A | `indigo-porcelain` / `dune` / `forest-ink` / `kraft-paper` / `monocle-classic` | 冷瓷蓝 / 暖沙 / 墨绿 / 牛皮纸 / 奶油白 |

路径前缀：`C:/Users/10355/.workbuddy/skills/guizang-social-card-skill/assets/screenshot-backgrounds/<style>/`

### 短标题提取法（1:1 用）
参考 guizang 的 `references/title-shortener.md` 五步提取：
1. 找核心动词（接管 / 减重 / 搬到 / 写完）
2. 找核心对象（便签纸 / 装备 / 家 / 书）
3. 压缩到 4–10 字
4. 去掉英文（除非是品牌名如 AI）
5. 必要时加小副标题

⚠️ 短标题是**另写一句**，不是把 21:9 的长标题裁短塞进方块。

### 工作流
1. 复制 `assets/cover_template.html` 到 `<工作目录>/cover.html`
2. 替换所有 `{{...}}` 占位符为当篇内容（配图路径默认不改 = ikb-dot-gradient）
3. 运行 `node scripts/render_cover.cjs <工作目录>` → 自动输出三张 PNG（配图自动从 guizang 素材解析）
4. 推送草稿时用 `--cover cover.png`

### 模板文件位置
`assets/cover_template.html`（含完整 CSS + 三帧结构 + 占位符说明 + JS 预览自动拼接）

## 正文插图规范（三轨制 · 先按图类型选轨）

| 图类型 | 工具 | 为什么 | 产物 |
|--------|------|--------|------|
| **分支 / 流程 / 关系 / 对比 / 脑图** | **Mermaid**（首选） | 声明式，箭头永不指错；渲染管线现成 | `images/*.mmd` → `*.png` |
| **知识框架 / 架构 / 拓扑** | **architecture-diagram 浅色大字** | 程序化生成，结构严谨、字大清晰、可控 | `diagram/*.html` → Playwright 3x 截图 |
| **比喻 / 场景插画 / 封面背景** | **baoyu + ImageGen** | AI 生图有画面感、讲故事 | prompt 文件 → ImageGen → PNG（耗积分） |
| 特殊定制 / 信息图 | svg_kit.py（兜底） | 手写 SVG 坐标，需目视核对箭头 | `images/svg_N.svg` → `*.png` |

**用户定案的三条铁律**：
1. **一律浅色背景**（白/浅灰底 + 语义色描边），不要暗色图——暗色块在白底文章中跳眼（2026-08-07 第 12 篇 RAG 实测）。
2. **知识框架总结图放文章开头**——先给读者一张全文路线图，再进正文。
3. **字号要大、图要高清**：公众号正文图显示宽约 375–677px，画布内字号 <15px 会被压缩成糊点。规范：画布宜窄（620–800 宽），主标签 ≥20px、说明 ≥14px；Playwright 截图 deviceScaleFactor 3，svg 类渲染 2x。

### 零、知识框架 / 架构图 → architecture-diagram 浅色大字版

**样板**：`E:\16_workBuddy_workspace\myskill\posts\12_RAG技术\diagram\rag-framework.html`（三层 region 分组）+ `render_framework.cjs`（Playwright 3x 截 `#framework-svg`）。

规范要点：
- 浅色：底 `#f8fafc` + 网格 `#e8ecf2`，文字深墨 `#0f172a` / 副文字 `#475569`
- 组件：白底卡片 + 语义色描边（rose `#f87171` / emerald `#34d399` / cyan `#22d3ee` / violet `#a78bfa` / amber `#fbbf24` / slate `#94a3b8`），序号圆 + 主标题 + 说明两行
- 结构清晰：用虚线 region 边界按"认知层次"分组（如 问题层 rose → 机制层 violet → 产品边界层 amber），每组 2 个模块
- 字号：标题 28–30px、主标签 22–24px、说明 15–16px、序号 24–26px；底部深蓝总结条 `#1c5fd9`
- 渲染：Playwright `element.screenshot()` 截 SVG，deviceScaleFactor 3（640 画布 → 1920px 高清）

#### 连线规范（手写坐标必守，2026-08-08 第 13 篇踩坑后定）
- **模块间隙 ≥ 44px**：任何两个相邻模块之间的空隙至少 44px，箭头才放得下、看得清指向。布局先算好缝隙再画线。
- **箭头 marker 8px、线宽 2–2.5**：不要用 12px+ 大箭头和 3px 粗线（挤、糊、看不出指向）。
- **路径禁止穿过任何模块**：连线（尤其折线回路）的每一段都要用目标/起点模块的 bbox 检查——`x` 落在某模块的 `[x, x+w]` 且 `y` 落在 `[y, y+h]` 即算穿框，必须绕行。
- **箭头必须贴目标框边缘**：终点坐标 = 目标框边缘内侧 2–4px，marker 方向指向框内；不允许悬空停在半路。
- **每条箭头都要"有语义"**：画完自检"箭头从哪到哪、表达什么关系"，缺少的关键连接（如 tool_calls→执行）必须补上。
- **画完必渲染必目视**：渲染后逐条核对箭头起点/终点/路径，不许只看坐标。

### 一、Mermaid 声明式图表（**首选，推荐用于所有流程/结构/关系类插图**）

> **为什么选 Mermaid？** 手写 SVG 坐标（svg_kit.py）容易出箭头指向错误、元素溢出等 bug。
> Mermaid 是声明式的——你只写「节点 + 连线」，布局引擎自动算坐标，**箭头永远不会指错**。

#### 适用场景
| 图类型 | Mermaid 关键字 | 适合 |
|--------|---------------|------|
| 流程 / 演化 / 分工 | `flowchart TD/LR` | 三道工序、演化时间线、钱去哪了瀑布 |
| 风险 / 分类 / 对比 | `flowchart TD` | 风险地图、两分法对比 |
| 脑图 / 知识树 | `mindmap` | 概念体系、知识框架 |
| 时序 / 交互 | `sequenceDiagram` | API 调用流程 |

#### 工作流
1. 在 `<工作目录>/images/` 下创建 `.mmd` 文件（如 `svg_1.mmd`, `svg_2.mmd`, `svg_3.mmd`）
2. 用 Mermaid 语法写图表代码（中文标签用引号包裹）
3. 运行 `node scripts/render_mermaid.cjs <工作目录>` → 自动输出同名 `.png`（2x 高清）
4. **渲染后必须逐张目视核对**：Read PNG 确认箭头指向正确、文字不截断、布局合理
5. `post.md` 中插图引用**必须用相对路径** `![图N：描述](images/svg_N.png)`——**严禁**写成 `local-file:///E:/.../images/svg_N.png` 或任何带协议前缀/盘符的绝对路径。publish 脚本按 HTML 的 `src` 提取图片，`local-file://` 前缀在 markdown→HTML 转换时会被整段丢弃，导致插图全部漏传（06、08 均踩过此坑）。

#### 主题配置（已内置在 `render_mermaid.cjs`）
- 配色对齐清新蓝：主色 `#1c5fd9`，节点底色 `#eaf1ff`，文字 `#1a2b4a`
- 字体：Microsoft YaHei
- 渲染倍率：默认 4x（`render_mermaid.cjs <目录> [deviceScaleFactor，默认4]`），高清够用

#### ⚠️ 强制检查清单（每次渲染后逐项打勾）
- [ ] 所有实线箭头从源节点出发 → 到达目标节点（无交叉/错位）
- [ ] 所有虚线箭头（-.->）标注清晰、指向正确
- [ ] 中文文字完整显示（无截断/重叠）
- [ ] 整体布局紧凑但不拥挤（无大片空白或过度压缩）

### 二、手写 SVG（仅用于特殊定制 / 信息图风格）
- 圆角卡片 `rx=16`，描边 `stroke-width=2.5`，柔和投影（feDropShadow）
- 主色 `#1c5fd9`，辅以紫 `#845ef7`、绿 `#40c057`、暖黄 `#f2c200` 区分模块
- 箭头 `stroke-width=1.8`，marker 小巧（7×7），不穿过框体
- 标签用楷体（KaiTi）增强「手写笔记」感
- **⚠️ 手写坐标必须目视核对箭头位置后再推送**
- 每张图宽度建议 600–780，高度自适应
- 画布宽度必须设为 **680**（viewBox `0 0 680 H`）
- 用 `scripts/svg_kit.py` 的函数生成，`render_svg.cjs` 渲染

### 三、比喻 / 场景插画 → baoyu-article-illustrator + ImageGen（AI 生图）

**触发条件**：图的"灵魂"是画面感/讲故事（闭卷 vs 开卷、语义星图、雪球滚大）时，AI 生图比几何框图生动得多；但**文字多、结构严谨的图禁用 AI**（框架图/流程图 AI 必翻车）。

工作流（按 baoyu-article-illustrator 规范）：
1. 分析该图要表达的比喻/场景，选 type（scene / comparison / metaphor 等），风格统一用 `sketch-notes`（EXTEND.md 已配）或用户指定
2. **先写 prompt 文件**到 `<工作目录>/prompts/NN-{type}-{slug}.md`（硬性要求，含 ZONES / LABELS / COLORS / STYLE / ASPECT 结构化）
3. 调用 ImageGen（本环境后端）：`size 1536x1024`（16:9），`quality high`，`output_dir` 指向 `<工作目录>/baoyu_test/`
4. **中文标签必须用户人工验字**（模型不能读图；AI 中文易错字，错字只能重生成、禁止程序修补）
5. 选定后复制进 `<工作目录>/images/`，post.md 用相对路径引用

⚠️ 每张 AI 图消耗积分 5-10，生成前先告知用户。
