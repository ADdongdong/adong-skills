---
name: daily-ai-feynman
description: >
  每日一篇「费曼学习法 × 知识点」公众号推文的全自动工作流。
  选题覆盖 AI 技术、金融投资、通用商业/产品等领域，每次推荐 3–5 个跨领域选题由用户挑选或自填。
  用 /真懂教练-费曼学习（hahadong）模拟小白对话，梳理成公众号文章，
  配图走三轨制（比喻图→baoyu AI / 知识框架→architecture-diagram 浅色大字 / 分支流程→Mermaid），
  guizang Swiss 风格公众号封面对（21:9+1:1），最终推送至微信草稿箱。
  当用户说"今天写什么知识点"、"生成每日推文"、"写一篇科普发公众号"、
  "用费曼法写一篇 XXX 的推文"、"每日推文"、"帮我推一篇"时触发。
agent_created: true
version: 1.2.0
display_name: "费曼自动生成推文"
display_name_en: "Feynman Auto Post"
description_zh: "费曼自动生成推文：每日一篇费曼学习法 × 跨领域知识点公众号推文。模拟小白对话成稿，配图三轨制（比喻→AI 生图 / 知识框架→architecture-diagram 浅色 / 分支流程→Mermaid），guizang Swiss 风格封面对（21:9+1:1），推送至微信草稿箱。"
description_en: "Feynman Auto Post: a daily Feynman-method WeChat post pipeline. Simulate a novice dialogue into an article, with three-track illustrations (metaphor→AI image, framework→light architecture-diagram, flow→Mermaid) and guizang Swiss-style cover pairs (21:9 + 1:1), pushed to the WeChat draft box."
visibility: "private"
---

# 费曼自动生成推文

把「费曼学习法 + 跨领域科普 + 公众号日更」串成一条可复用的流水线，产出风格统一、
配图清新、可直接进草稿箱的文章。选题不限于 AI——AI、金融、通用商业都行。

## 适用场景
- 想每天稳定产出一篇科普公众号文章（主题自选：AI / 金融 / 商业产品）
- 文章风格：小白提问 + 哈哈栋回答的对话体，通俗易懂、有类比
- 配图（三轨制）：比喻/场景图→baoyu AI 生图；知识框架/架构图→architecture-diagram 浅色大字；分支/流程/关系图→Mermaid
- 封面：guizang Swiss 风格文字排版 + 真实照片（或 baoyu AI 无字背景图）
- 终态：推送到微信公众号草稿箱（手动触发）

## 前置依赖
- 已安装 skill：`hahadong-feiman__skillhub`（费曼学习）、`md-to-wechat__skillhub`（微信推送）
- **三轨制配图工具**（均已装到用户级 `~/.workbuddy/skills/`）：
  - `baoyu-article-illustrator` / `baoyu-cover-image`：AI 生图提示词工厂（比喻图/封面，后端=ImageGen，耗积分 5-10/张，EXTEND.md 已在 `~/.baoyu-skills/` 预配置）
  - `architecture-diagram`：工程级架构图 HTML+SVG（知识框架/架构图，浅色大字规范见 style_guide）
  - 本 skill 自带 `render_mermaid.cjs` + `assets/mermaid/mermaid.min.js`：Mermaid 声明式图表（分支/流程/关系图首选）
- Node 包 `playwright` + Chromium（封面/架构图 HTML→PNG 截图，装在托管 node workspace）
- 本 skill `scripts/` 已自带：`svg_kit.py`（特殊定制兜底）/ `render_svg.cjs` / `render_cover.cjs` / `render_mermaid.cjs` / `publish_draft.cjs`
- 封面模板：`assets/cover_template.html`（Swiss International × 清新蓝，21:9+1:1）
- 微信配置：首次使用把 `md-to-wechat__skillhub/.env` 复制一份到本 skill 目录
  （含 `ACCOUNT` / `THEME_ID` / `WECHAT_APP_ID` / `WECHAT_APP_SECRET` / `API_URL`）

## 工作流程（四阶段）

### ① 选题与生成
1. **推荐选题（跨领域）**：从 `references/knowledge_outline.md` 选题池里挑 **3–5 个未用过**的点，**跨领域混合**（AI / 金融 / 通用商业都带一点），用 `AskUserQuestion` 以选择卡形式呈现。
   - 用户从推荐里选一个；或选「其他」**手动输入**自己的选题（如「讲讲久期」），此时跳过推荐直接使用。
   - 若用户触发时**已直接点名**（如"用费曼法写一篇讲 ETF 的"），则跳过推荐，直接用该选题。
2. 调用费曼 skill（`/真懂教练-费曼学习（hahadong）`），以「模拟小白学 <知识点>」为目标，产出哈哈栋与小白的多轮对话。
3. 对话要求：小白连续追问（用自己的话复述 / 举例子 / 追问为什么），哈哈栋用生活类比开场、逐步纠偏，直到小白能讲清楚。

### ② 梳理成文
4. 把对话整理为公众号 Markdown，结构固定：
   - 标题（含知识点名，口语化，如「Agent 到底是什么？用点外卖给你讲明白」）
     ⚠️ MD 第一行仍写 `# 标题` 供脚本提取草稿标题，但**正文不会显示它**
     （`publish_draft.cjs` 渲染前自动摘除），所以**开头别再手写一遍大字标题**，
     也别写「本文目录」之类，直接进引语。
   - 开头引语（1 句话制造阅读期待）
   - 正文：小白问 / 哈哈栋答 交替，用普通段落 + 前缀标签区分（见 `references/style_guide.md`，不用引用块竖条）
   - 结尾小结（3 条要点）
5. 配图占位：在正文关键处插入 `![图N](images/xxx.png)`（文件名按三轨制生成后回填）；封面图路径稍后填。

### ③ 配图（三轨制，先按图类型选轨再生成）
6. **按图类型选轨**（完整决策表见 `references/style_guide.md`「正文插图规范」）：

   | 图类型 | 工具 | 说明 |
   |--------|------|------|
   | 分支/流程/关系/对比 | **Mermaid**（首选） | 声明式，箭头永不指错；`images/*.mmd` → `render_mermaid.cjs` 渲染（清新蓝主题内置） |
   | 知识框架/架构/拓扑 | **architecture-diagram 浅色** | 程序化 HTML+SVG，字大清晰；浅色规范 + 样板见 style_guide；Playwright 3x 截图 |
   | 比喻/场景插画/封面 | **baoyu + ImageGen** | AI 生图有画面感；走 baoyu-article-illustrator 工作流（prompt 文件落盘→ImageGen，耗积分）；中文文字必须人工验字 |
   | 特殊定制/信息图 | svg_kit.py（兜底） | 手写 SVG 坐标，需目视核对箭头 |

7. 封面图：**真实照片 + 文字**的公众号封面对（21:9 + 1:1），配图来源优先级：
   **① baoyu AI 无字背景图**（`baoyu-cover-image` 出无字主视觉 + HTML 叠字，中文标题最稳）→ **② Unsplash 真实照片**（默认，零积分）→ **③ 兜底**（复用正文插图 / guizang 纹理）。

   a) **Unsplash 取图**（默认路径，来自免费图库，零积分）：
      1. 从本篇**核心类比**提炼视觉关键词，用英文（图库英文命中率远高于中文）。
         例：缓存命中→书签 = `bookmark-book`；Agent→点外卖 = `food-delivery-courier`；
         复利→雪球 = `snowball-rolling`；除权→打折 = `discount-price-tag`
      2. 用 **WebFetch** 打开 `https://unsplash.com/s/photos/<关键词>`，
         从结果里挑 **3 张不带 `Unsplash+` 标记的免费图**（带 Unsplash+ 的是付费墙，下不了），
         取其 download 链接里的 ID，形如 `https://unsplash.com/photos/bYy9hndOx0k/download` → `bYy9hndOx0k`
      3. 运行 `node scripts/fetch_photo.cjs <工作目录> <id1> <id2> <id3>`
         → 下载到 `<工作目录>/assets/cand1~3.jpg`，并自动写 `assets/SOURCES.md` 记录来源
      4. 拼一张候选总览图给用户挑（PIL 需 `ImageFile.LOAD_TRUNCATED_IMAGES = True`，
         图库大图常有尾字节截断），用户选定后作为封面配图

      ⚠️ **不要用 curl 直接抓 Unsplash / Pexels 搜索页**——有反爬（401/403/307）。
      只有 `/photos/<id>/download` 端点可达（302 到 `images.unsplash.com` CDN，实测 200）。

      ⚠️ **2026-09-11 实测：Unsplash 搜索页已挂 Anubis 反爬**，WebFetch 只返回
      `Making sure you're not a bot!` 挑战页，取不到任何 id → **改走 Pexels 路线**：
      1. WebFetch `https://www.pexels.com/search/<英文关键词，空格转 %20>/`，让它列出详情页
         URL（`https://www.pexels.com/photo/<slug>-<数字ID>/`），取结尾数字 ID
      2. CDN 直链下载（实测 200，带 `User-Agent` + `Referer: https://www.pexels.com/`）：
         `https://images.pexels.com/photos/<ID>/pexels-photo-<ID>.jpeg?auto=compress&cs=tinysrgb&w=1920`
      3. 来源记 `assets/SOURCES.md`（Pexels License：可商用、可修改、无需署名）

      ⚠️ **`render_cover.cjs` 的 `art.*` 自定义配图分支是死代码**（恒回落到 guizang 默认素材）：
      用真实照片时必须在 `cover.html` 里**直接把 `{{配图绝对路径}}` 替换成写真路径**
      （`file:///E:/.../assets/cand1.jpg`，正斜杠、中文不编码，实测可加载）。

   b) **baoyu AI 无字背景图**（封面要中文标题时的推荐路线）：
      - 用 `baoyu-cover-image` 生成**无字/少字**主视觉（`--text none` 或 title-only），
        **禁止让 AI 直出中文长标题**（错字率高且无法程序修补）
      - AI 图作为封面模板的 `{{配图绝对路径}}` 背景；标题/副标题由 cover.html 的 HTML 叠字保证准确
      - 消耗积分 5-10/张，中文校验由用户人工把关

   c) **兜底方案**（取图失败或主题太抽象时）：
      - 复用正文插图：`--art` 指向 `images/xxx.png`，
        此时把 `background-size` 改成 `88% auto` + `no-repeat` + `background-color:var(--accent-soft)`（居中留白，别拉伸）
      - 用 guizang 纹理素材：见 `references/style_guide.md` 的 9 张素材速查表（纯图案，无内容）

   d) 复制 `assets/cover_template.html` 到 `<工作目录>/cover.html`，替换所有 `{{...}}` 占位符：
      - 栏目标签（如 `FEYNMAN DAILY · NO.03`）
      - 完整标题（可用 `<em>词</em>` 标出主色重点，超 14 字降字号到 84px）
      - 副标题（一句话说清读完能得到什么，20–30 字）
      - 短标题（4–10 字，另起一句，**不要裁 21:9 的标题**）
      - 配图路径 `{{配图绝对路径}}` → 选定照片/AI 图的 `file:///` 绝对路径
        （真实照片用 `background-size:cover` 铺满出血；SVG 插图才用居中缩放）

   e) 运行 `node scripts/render_cover.cjs <工作目录>`
      → 输出 `<工作目录>/cover.png`（2100×900）+ `cover_square.png`（1080×1080）+ `cover_preview.png`

   f) 版式：21:9 = 左侧文字轴 + 右侧配图出血；1:1 = 上方配图 600px + 下方短标题。
      配图版权：Unsplash License 允许商用与修改，来源已记在 `assets/SOURCES.md`；
      AI 图来源记 `assets/SOURCES.md`（注明 AI 生成）。

### ④ 排版推送
8. 把封面图填入 MD（顶部 `![cover](cover.png)` 或用 `--cover` 指定）。
9. 运行 `node scripts/publish_draft.cjs --file <md路径> --confirmed`
   （首次不加 `--confirmed`，脚本会打印本机 IP 供加入微信白名单）。
   该脚本基于 md-to-wechat 增强：**正文本地 PNG 自动上传微信 CDN**，无需手动处理。
10. 推送成功，告知用户去公众号后台 → 草稿箱查看。

## 关键约定
- **配色**：清新蓝 `#1c5fd9` 主色 + 纯白底 + 浅灰分割线（详见 `references/style_guide.md`）
- **零背景（硬规则）**：公众号正文不要任何背景色，禁用主题黄底/色块。
  `publish_draft.cjs` 默认自动剥离 HTML 中全部 `background*` / `bgcolor`；
  确需保留才加 `--keep-bg`。
- **不重复标题（硬规则）**：正文顶部不出现大字标题，脚本渲染前自动删掉首个 H1；
  确需保留才加 `--keep-h1`。
- **封面配图**：优先级 = **baoyu AI 无字背景图（中文标题稳）→ Unsplash 真实照片（零积分默认）→ 兜底**（正文插图 / guizang 纹理）。
  Unsplash 路径：按核心类比提炼英文关键词 → WebFetch 搜索 → `fetch_photo.cjs` 下载候选 → 用户挑选，来源记 `assets/SOURCES.md`。
- **插图三轨制（硬规则）**：分支/流程/关系/对比图 → Mermaid 首选；知识框架/架构图 → architecture-diagram 浅色大字；比喻/场景插画 → baoyu + ImageGen。决策表见 style_guide。
- **插图规范（用户偏好）**：一律浅色背景（白/浅灰底，不要暗色块）；"知识框架总结图"放文章开头；字号要大、图要高清——画布 620–800 宽、主标签 ≥20px、说明 ≥14px，Playwright 截图用 3x（svg 类 2x 已够）
- **AI 生图红线**：中文文字渲染不可靠（错字只能重生成，禁止程序修补）；封面中文标题 = AI 出无字背景 + HTML 叠字；每张 AI 图消耗积分 5-10，需先告知用户
- **选题池**：跨领域（AI / 金融 / 通用商业）混合推荐，跑完在 `references/knowledge_outline.md` 打勾记录，避免重复
- **本地图**：必须放 `<工作目录>/images/` 下，MD 用相对路径引用，由 `publish_draft.cjs` 自动上传
- **中文渲染**：`render_svg.cjs` 已加载系统微软雅黑 / 楷体，不会乱码

## 排错
| 现象 | 处理 |
|------|------|
| 微信 40164 IP 不在白名单 | 把脚本打印的 IP 加入公众号后台 → 基础信息 → API IP 白名单 |
| SVG 中文乱码 | `render_svg.cjs` 已绑定系统字体；确认 `C:/Windows/Fonts/msyh.ttc` 存在 |
| 封面不符预期 | 调整 cover.html 里的文案/排版/素材路径，重新运行 render_cover.cjs；标题过长时降字号或拆行 |
| 推送报 missing_env | 检查本 skill 目录的 `.env` 是否从 md-to-wechat 复制齐全 |
