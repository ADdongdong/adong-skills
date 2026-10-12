# 21 个 HTML 移植件说明

> **本文件由 `scripts/build_ports.py` 自动生成**，内容取自每个片段的头注释与实测结果。
> 改完片段重跑脚本即可刷新，不要手改本文件。

每个移植件都是**零依赖单文件**：内联了设计令牌、该组件所需的工具类 CSS、以及它的 JS 状态机。
动效与上游一致的做法见 `foundation-tokens.md`（时序常量照搬 + 令牌同名引用 + DOM 层级不变）。

## 总览

| slug | 中文名 | 文件大小 | 工具类数 | 未覆盖类 | 片段 |
|---|---|---|---|---|---|
| `agent-screen` | 智能体屏幕 | 47 KB | 153 | 0 | `assets/ports/agent-screen.frag.html` |
| `approval-card` | 审批卡片 | 49 KB | 89 | 0 | `assets/ports/approval-card.frag.html` |
| `chat-composer` | 聊天面板 | 39 KB | 77 | 0 | `assets/ports/chat-composer.frag.html` |
| `code-block` | 代码块 | 39 KB | 64 | 0 | `assets/ports/code-block.frag.html` |
| `context-cards` | 上下文卡片 | 31 KB | 55 | 0 | `assets/ports/context-cards.frag.html` |
| `diff-table` | 差异表格 | 46 KB | 86 | 0 | `assets/ports/diff-table.frag.html` |
| `filter-table` | 筛选表格 | 35 KB | 55 | 0 | `assets/ports/filter-table.frag.html` |
| `fine-tune-card` | 微调卡片 | 44 KB | 99 | 0 | `assets/ports/fine-tune-card.frag.html` |
| `flowchart` | 流程图 | 47 KB | 94 | 0 | `assets/ports/flowchart.frag.html` |
| `insight-cards` | 洞察卡片 | 49 KB | 99 | 0 | `assets/ports/insight-cards.frag.html` |
| `loading-state` | 加载状态 | 31 KB | 38 | 0 | `assets/ports/loading-state.frag.html` |
| `prompt-bar` | 提示栏 | 70 KB | 118 | 0 | `assets/ports/prompt-bar.frag.html` |
| `recommendation-card` | 推荐卡片 | 40 KB | 96 | 0 | `assets/ports/recommendation-card.frag.html` |
| `records-table` | 记录表格 | 101 KB | 129 | 0 | `assets/ports/records-table.frag.html` |
| `search` | 命令搜索 | 33 KB | 57 | 0 | `assets/ports/search.frag.html` |
| `selection-actions` | 选区操作 | 47 KB | 86 | 0 | `assets/ports/selection-actions.frag.html` |
| `sidebar-nav` | 侧边导航 | 55 KB | 111 | 0 | `assets/ports/sidebar-nav.frag.html` |
| `streaming-text` | 流式回答 | 41 KB | 84 | 0 | `assets/ports/streaming-text.frag.html` |
| `task-rows` | 任务进度行 | 41 KB | 70 | 0 | `assets/ports/task-rows.frag.html` |
| `thinking-state` | 思考轨迹 | 44 KB | 73 | 0 | `assets/ports/thinking-state.frag.html` |
| `tool-chips` | 工具调用芯片 | 46 KB | 103 | 0 | `assets/ports/tool-chips.frag.html` |

## 逐个说明

以下「保真说明」摘自各片段头注释。

### `agent-screen` — 智能体屏幕

- 成品：`assets/html/agent-screen.html`（47.0 KB）
- 源片段：`assets/ports/agent-screen.frag.html`
- 编译进 CSS 的工具类：153 个
- 未覆盖类：无

来源：components/primitives/AgentScreen.tsx（上游 MIT）
     保真：三态（open / teach a task / record）与 Working·Loading 两个变体；
           折叠卡 2964/1856 的 aspect + fade-up 380ms 入场；hover 才浮出蓝色 Open 胶囊；
           Open 后 portal 到 <body> 的全屏 viewer（fade-in 180ms 背景 + pop-in 240ms 面板）；
           Esc 折叠 / body 滚动锁；自绘 macOS 指针跟随鼠标（[cursor:none] 画布）；
           录制计时 mm:ss + 红色 REC 徽标（records-pulse 1.1s）。
     依赖降级：
       ① 上游占位图 public/agent-desktop.webp **未随仓库同步**。为遵守「不引用不存在的本地
          文件、也不用远端 URL」，这里改用上游**自带的非图片回退** FauxWindow（纯 CSS 自绘的
          仿浏览器窗口骨架）充当屏幕占位——它本就是上游 streamSrc 缺失时的分支，非自创视觉。
       ② 上游 `.agent-cursor` 类定义在 app/globals.css（不在 foundation.standalone.css 里），
          故用等价的工具类+inline（absolute pointer-events-none + drop-shadow filter）复现，
          视觉一致。
     付费依赖：无。


### `approval-card` — 审批卡片

- 成品：`assets/html/approval-card.html`（48.6 KB）
- 源片段：`assets/ports/approval-card.frag.html`
- 编译进 CSS 的工具类：89 个
- 未覆盖类：无

来源：components/primitives/ApprovalCard.tsx（上游 MIT）
     内联了 atoms/Button.tsx（variant ghost / accent + size sm，cva 变体手写为 class 分支）
     与 primitives/GlideMenu.tsx（单条滑动的 hover 高亮 + 键盘导航，见 initGlide）。
     保真：ROLL_MS = 400、两张滑动曲线 SLIDE = "360ms cubic-bezier(0.22, 1, 0.36, 1)"、
           滚动数字逐字符上下翻（transition transform 350ms cubic-bezier(0.4,0,0.2,1)，
           双 rAF 后再落位）、卡片高度随题目高度过渡、单选 480ms 自动前进、
           gap 26px 的问题栈、z-10 选项 / 绝对定位高亮层、aria-pressed / tabIndex 切换。
     降级：useLayoutEffect + useRef 测量 → 直接读 offsetHeight / offsetTop；
           React 的 key 重挂载 → mount() 重建；prefers-reduced-motion 时关闭过渡（同上游）。
     @classes：① footer 的 Skip/Continue 与翻页按钮的类来自 JS 常量（不在 class="..." 里），
               ② 选项勾选态的 class 分支同样由 JS 拼出（含 rounded-[5px]）。


### `chat-composer` — 聊天面板

- 成品：`assets/html/chat-composer.html`（38.9 KB）
- 源片段：`assets/ports/chat-composer.frag.html`
- 编译进 CSS 的工具类：77 个
- 未覆盖类：无

来源：components/primitives/ChatComposer.tsx（上游 MIT）
     保真：phase 状态机 sent →(500ms) reply1 →(1400ms) reply2 →(1200ms) done 逐字照搬；
           气泡 transition-[opacity,transform] duration-300、Section 的
           opacity/filter/transform + duration-400 + cubic-bezier(0.23,1,0.32,1)、
           fade-up 400ms 入场动画、DOM 层级与全部工具类均与上游一致。
     降级：useState/useEffect → 普通变量 + setTimeout；Section 用 display 显隐 +
           重放 fade-up（上游靠 React 复用节点，只在新挂载时播一次动画），
           所以同一次对话里每段回复只会入场一次，视觉与上游等价。
     @classes 里是标签页激活态的分支类，它们是 JS 三元产生的，不在静态 class 属性里。


### `code-block` — 代码块

- 成品：`assets/html/code-block.html`（39.0 KB）
- 源片段：`assets/ports/code-block.frag.html`
- 编译进 CSS 的工具类：64 个
- 未覆盖类：无

来源：components/primitives/CodeBlock.tsx（上游 MIT）
     变体：Code（带行号列表）/ Diff（unified diff）
     保真：两条视图共用同一套语法着色 —— 关键字/条件 → var(--accent-ink)，
           字符串/数字 → var(--orange)，函数调用 → var(--ink) 且 font-weight:500；
           TOKEN 正则与 highlight() 的 token 顺序逐字照搬。diff 的 gutter 单列
           （删除行用旧行号，新增/上下文用新行号）、左侧 3px 色条（新增实心绿、
           删除红色斜纹 hatch）、green/red 行底 tint、词级 add/del 高亮
           （color-mix 18% + box-decoration-break:clone）全部照搬。
     Copy：写剪贴板后 1500ms 内显示 "Copied"（绿）；离线/无权限时静默失败，
           与上游 `navigator.clipboard.writeText(...).then(...)` 行为一致，
           仅额外加了 catch 防止控制台出现未捕获的 rejection。


### `context-cards` — 上下文卡片

- 成品：`assets/html/context-cards.html`（30.9 KB）
- 源片段：`assets/ports/context-cards.frag.html`
- 编译进 CSS 的工具类：55 个
- 未覆盖类：无

来源：components/primitives/ContextCards.tsx（上游 MIT）
     保真：检索到的 chunk 一次性入场后常驻。头部 fade-in 400ms ease-out；
           每张卡按索引错开 fade-up 400ms cubic-bezier(0.23,1,0.32,1)（i*100ms）；
           来源 chip 在 700ms 后整体揭示（opacity 0→1、scale 0.95→1，
           transition-[opacity,transform,background-color] 300ms cubic-bezier(0.23,1,0.32,1)，
           并各自延迟 i*80ms）—— 时序常量逐字照搬。
     DOM 层级与上游一致（卡片 / primitive-card-bar / 正文 / chip 行）。
     依赖降级：无（纯 HTML/CSS/JS）。badge 的 bg-red / bg-green 由数据生成，
     故在 @classes 中声明。


### `diff-table` — 差异表格

- 成品：`assets/html/diff-table.html`（45.5 KB）
- 源片段：`assets/ports/diff-table.frag.html`
- 编译进 CSS 的工具类：86 个
- 未覆盖类：无

来源：components/primitives/DiffTable.tsx（上游 MIT）
     保真：getBoundingClientRect 无关；时序照搬 useStage(STAGE_DELAYS=[180,260]) ——
           0 平铺 → 1 删除行着色 → 2 完整 diff（新增行入场 + 页脚）。
           逐格 diff：删除行 hover:brightness-[0.985]、行底 var(--red-tint)、
           flavor 变红、category 芯片 opacity 0.55、supplier 变红 + 删除线
           （text-decoration-color: color-mix(red 50%)）；新增行 var(--green-tint) 与
           对应绿色。行级 include/exclude 用 IncludedMark（scale 0.92↔1 + 勾选 svg），
           键盘 Enter/Space 可切换。表脚 Apply 遵循选择计数；应用后整行替换为
           pop-in 的绿色 "N edits applied" 药丸。
     Button.tsx 内联：variant=accent / size=sm（+ className text-[12px]）。
           cva 里 size sm 的 text-[13px] 会被 className 的 text-[12px] 覆盖
           （上游 cn=twMerge，后者胜出），故这里只保留 text-[12px]，还原真实字号。
     表格 DOM：<table>/<colgroup>/<thead>/<tbody>/<tr>/<td> 与 data-* 保持上游原样。


### `filter-table` — 筛选表格

- 成品：`assets/html/filter-table.html`（35.0 KB）
- 源片段：`assets/ports/filter-table.frag.html`
- 编译进 CSS 的工具类：55 个
- 未覆盖类：无

来源：components/primitives/FilterTable.tsx（上游 MIT）
     保真：状态芯片即时筛选行。每行是 grid-template-rows 1fr↔0fr + opacity 的
           300ms 展开/收起（strong 曲线 cubic-bezier(0.23,1,0.32,1)），不整表重排。
           芯片激活态 bg-surface text-ink shadow-btn，未激活 text-ink-2 hover:bg-hover；
           计数角标激活 bg-field、未激活 text-ink-3。筛选点用上游硬编码 hex
           （#f09a2f / #16a6c7 / #25a878），状态药丸用 foundation 的
           .filter-status-todo/-progress/-done（其色由 --tag-base 经 color-mix 派生，
           明暗两套自动切换）。表格 DOM 与 grid 列宽保持上游原样。


### `fine-tune-card` — 微调卡片

- 成品：`assets/html/fine-tune-card.html`（44.0 KB）
- 源片段：`assets/ports/fine-tune-card.frag.html`
- 编译进 CSS 的工具类：99 个
- 未覆盖类：无

来源：components/primitives/FineTuneCard.tsx（上游 MIT）
     依赖 primitives/GlideMenu.tsx，已内联为 Type 下拉里的 hover 高亮层。
     保真：ScrubField 拖动 (clientX 位移 / 2) * step、↑↓←→(Shift ×10)、直接输入数字、
           min/max 先 clamp 再 Math.round；分段滑块 width:calc((100% - 4px)/3)、left:2、
           transition-transform 300ms cubic-bezier(0.23,1,0.32,1)；
           头部 Adjust 微光(shimmer-text 1.4s) ↔ Edited 徽标(pop-in 250ms)；
           Type 菜单 pop-in 200ms、transform-origin:bottom-right —— 常量逐字照搬。
     增强：上游卡片只通过 onChange 抛出状态、自身没有预览元素。为兑现
           「控件要真的改到预览元素上」，移植件在卡片旁加了一块「Flavor card」
           样本，W/H/Radius/Opacity 直接写入它的 inline style。


### `flowchart` — 流程图

- 成品：`assets/html/flowchart.html`（47.3 KB）
- 源片段：`assets/ports/flowchart.frag.html`
- 编译进 CSS 的工具类：94 个
- 未覆盖类：无

来源：components/primitives/Flowchart.tsx（上游 MIT）
     保真：布局常量 PAD_Y=24 / ROW_GAP=64 / PILL_OFFSET=30 逐字照搬；
           节点拖拽（pointer capture + 3px 阈值 + 画布内夹取）、连接线贝塞尔
           （k = clamp(|dy|*0.55, 24, 84)）、chip 下拉菜单（pop-in 180ms 入场 +
           高亮层 top/height 220ms cubic-bezier(0.23,1,0.32,1) 滑动）全部保留；
           菜单 hover 高亮与「选中节点点亮连线」逻辑一致。
     降级：无 —— 组件纯自绘，无外部依赖。
     @classes 里声明的是 JS 模板拼接产生的分支/动态类：
       Menu 的左右对齐(right-0/left-0)、选中勾(invisible)、
       chip 开合态(bg-hover-2 / bg-field / hover:bg-hover-2)、
       节点选中阴影(shadow-[...]) 与默认阴影(shadow-card/hover:shadow-raised)、
       以及 chip 宽度(w-36/w-44/w-64)。


### `insight-cards` — 洞察卡片

- 成品：`assets/html/insight-cards.html`（49.2 KB）
- 源片段：`assets/ports/insight-cards.frag.html`
- 编译进 CSS 的工具类：99 个
- 未覆盖类：无

来源：components/primitives/InsightCards.tsx（上游 MIT）
     降级：npm 包 liveline 全部替换为自绘 SVG 折线/面积图（无依赖）。曲线用上游同款
           Catmull-Rom 重采样（smooth：3 点以上，每段 9 采样，末点原样）保证与官网同样平滑；
           图表窗口/内边距/线宽照搬 props（CompareCard padding {40,0,22,0}、lineWidth 2.25；
           AnomalyCard padding {34,0,22,0}、grid）；hover 游标与 tooltip 复用上游自定义类
           .insight-chart-stage / -cursor / -tooltip-anchor / -tooltip / -tooltip-item / -tooltip-dot
           与 --tooltip-* 令牌、--shadow-overlay，未新增任何图表样式。
     保真：分页 carousel（‹ › + 页码）、blur crossfade（transition-[opacity,filter] duration-250）、
           文字 — 页码 — 卡片 — pill 的结构；CompareCard 双序列/大百分比/legend；
           AnomalyCard Spend/Usage 切换、阈值文案、底部金额；AllocationCard 分段条 + legend。
     verify workaround：已全部撤回，本文件回到上游 class（包括 text-white / bg-white/20 /
           inline-block 等），不再为规避审计引入 inline style。


### `loading-state` — 加载状态

- 成品：`assets/html/loading-state.html`（31.4 KB）
- 源片段：`assets/ports/loading-state.frag.html`
- 编译进 CSS 的工具类：38 个
- 未覆盖类：无

来源：components/primitives/LoadingState.tsx（上游 MIT）
     变体：Drive / Dots / Orbit / Surfer
     保真：pixel-on 波浪、shimmer 标签（1.4s）、100ms 计时器、pop-in 上下文卡与上游一致；
           所有时序常量逐字照搬。Surfer 变体的视频走上游 Vercel Blob，离线时自动回退。
     @classes 里声明的是 JS 三元产生的分支类（rounded-full / rounded-[1px]），
     它们不出现在静态 markup 的 class 属性里，必须显式声明。


### `prompt-bar` — 提示栏

- 成品：`assets/html/prompt-bar.html`（69.7 KB）
- 源片段：`assets/ports/prompt-bar.frag.html`
- 编译进 CSS 的工具类：118 个
- 未覆盖类：无

来源：components/primitives/PromptBar.tsx（上游 MIT）
     变体：Rounded（圆角卡片）· Pill（全圆角药丸）
     ── glimm 降级（本件最关键的替换）────────────────────────────
     上游 import { createShader, playSweep, accentChain, ACCENTS } from "glimm"，
     用 WebGL 着色器在 composer 内部画一道彩虹扫光（选中旗舰模型时触发）。
     本移植件删掉该依赖，改为**原生 <canvas> 2D + requestAnimationFrame 自绘**：
       · 保真：触发时机（selectModel 里 key === "sprinkles-5" 才触发）、
               sweepMs 570 / outroMs 80 / peakAlpha 1.3 / easing easeOutExpo /
               bandTight 10（彩虹带密度）/ direction "ltr" / brightness 1.4（用 CSS filter 施加）/
               swellAmount 的纵向柔化 / 每次触发重建（uTime 归零）都照搬；
       · 降级：glimm 的 ACCENTS 调色板在离线环境不可得，按上游注释的意图
               （"Build a true full-spectrum rainbow instead"）内联 7 段全光谱彩虹；
               水平位移 + 纵向柔化的实现方式是自绘的，视觉近似着色器而非逐像素一致；
               waveSpeed 1.8 的波峰摆动简化掉（只保留纵向渐隐）。
     ── 其余保真 ─────────────────────────────────────────────────
     时序/尺寸逐字照搬：pop-in 180ms cubic-bezier(0.23,1,0.32,1)、
     glide 高亮 top/height 220ms + opacity 150ms、dictation 2200ms 后落字、
     附件 chip pop-in 200ms、eq-bounce 900ms 逐条 +150ms、textarea 28~100px 自动增高、
     parseToken 正则 /(^|\s)([@/])([\w-]*)$/、AUTO_STEPS 自跑演示的 hold 值。
     降级：React 状态 → 普通变量；useLayoutEffect 测量 → 直接读 offsetTop / getBoundingClientRect；
           行内 style 承载 grid 摆放（上游的 col-span-full 在本仓库的 Tailwind 子集编译器里
           会生成非法的 `span full`，故改用等价的 inline grid-column/row）。
     @classes：① 上述 grid/半径/勾选态的分支类，② JSON 里内联的 Product/ValuePill 类串。


### `recommendation-card` — 推荐卡片

- 成品：`assets/html/recommendation-card.html`（39.8 KB）
- 源片段：`assets/ports/recommendation-card.frag.html`
- 编译进 CSS 的工具类：96 个
- 未覆盖类：无

来源：components/primitives/RecommendationCard.tsx（上游 MIT）
     内联了 3 个原子：atoms/Button.tsx（cva 变体手写为 class 分支，含 tailwind-merge 的去重结果：
     Alternatives 调用方传 px-2.5 / text-[12.5px]，覆盖 size sm 的 px-3 / text-[13px]；
     主按钮调用方只传 text-[12.5px]，所以仍保留 size sm 的 px-3。两处都按合并后的最终类写死）、
     atoms/EntityChip.tsx（含 Monogram，默认色 #e08a3c 为上游默认值）、atoms/ValuePill.tsx（5 种 tone 的 tint + ring）。
     保真：备选抽屉用 grid-template-rows 0fr→1fr + opacity，300ms + cubic-bezier(0.16,1,0.3,1)；
           正文切换重放 fade-in 180ms ease-out；置信度仪表 3 格、transition-colors duration-300；
           抽屉行 hover:bg-hover、transition-colors duration-100 全部照搬。
     降级：无 npm 依赖。cn/tailwind-merge 的类合并提前算好写死。


### `records-table` — 记录表格

- 成品：`assets/html/records-table.html`（100.7 KB）
- 源片段：`assets/ports/records-table.frag.html`
- 编译进 CSS 的工具类：129 个
- 未覆盖类：无

状态钩子类（is-colsel / is-resizing / is-visible / is-selected / is-active）与
     records-* 一样由 records-table.css 定义，不在此声明，避免被工具类编译器重复处理。


### `search` — 命令搜索

- 成品：`assets/html/search.html`（33.1 KB）
- 源片段：`assets/ports/search.frag.html`
- 编译进 CSS 的工具类：57 个
- 未覆盖类：无

来源：components/primitives/SearchList.tsx（上游 MIT）
     依赖 primitives/GlideMenu.tsx，已内联为 #search-glide 内的一条 hover 高亮层
     （top/height 220ms cubic-bezier(0.23,1,0.32,1)、opacity 150ms ease —— 逐字照搬）。
     保真：实时过滤（toLowerCase().includes）、空状态阈值 query.length > 2、
           未输入时只取前 5 条、点击结果回填输入框、清空按钮 fade-in 150ms、
           结果行 fade-in 200ms，全部照搬上游；仅 DOM 由字符串拼装，无框架。
     降级：无依赖（纯 HTML/CSS/JS）。


### `selection-actions` — 选区操作

- 成品：`assets/html/selection-actions.html`（46.7 KB）
- 源片段：`assets/ports/selection-actions.frag.html`
- 编译进 CSS 的工具类：86 个
- 未覆盖类：无

来源：components/primitives/SelectionActions.tsx（上游 MIT）
     降级：① iconoir-react → 内联 SVG（14×14 stroke-width 1.8，send 16×16/2.4）；
           ② atoms/Button.tsx（class-variance-authority）→ 手写的 quiet/xs class 常量；
           ③ atoms/Shimmer.tsx → 内联 shimmer span（1.8s linear infinite）；
           ④ atoms/StreamText.tsx → 内联流式揭示（charsPerTick 2 / tickMs 9 / blurTail 6，
              leading edge 用 .stream-tail 虚化，caret 流式中 .is-streaming 常亮、结束后闪烁）。
     验证workaround：已全部撤回（verify 审计已能正确处理 inline-flex 块级化与 color-mix 归一化），
           本文件不再为规避审计引入 inline style。
     保真：280ms 后出场；thinking 700ms 后转 streaming；浮条锚定在选中文本最后一行下方
           （requestAnimationFrame + getClientRects().at(-1)），水平对齐整段选区中心；
           位移 transition transform 320ms cubic-bezier(0.77,0,0.175,1) / opacity 180ms；
           模式切换时按内容固有宽度做 320ms cubic-bezier(0.23,1,0.32,1) 宽度动画；
           prompt 输入时锁定 typingWidth；动作组展开 max-width 224↔462 等常量逐字照搬。


### `sidebar-nav` — 侧边导航

- 成品：`assets/html/sidebar-nav.html`（54.5 KB）
- 源片段：`assets/ports/sidebar-nav.frag.html`
- 编译进 CSS 的工具类：111 个
- 未覆盖类：无

来源：components/primitives/SidebarNav.tsx（上游 MIT）
     保真：几何 224px 展开 / 52px 收起、内层固定 224px 树被外壳裁剪、
           「两种状态下每个 rail 图标都居中在 x=26」——逐字保留；
           SIDEBAR_MOTION(duration 280 / copyDuration 180 / copyOffset 8 /
           easing cubic-bezier(0.16,1,0.3,1)) 与 CHAT_SEARCH_MOTION(180/28) 照搬；
           折叠、工作区菜单、聊天搜索、聊天历史过滤、GlideMenu 滑动高亮全部保留。
     依赖降级：上游 import 的付费图标库 @central-icons-react（12 个图标）已替换为
           **lucide（ISC）等价图标的内联 SVG**，视觉略有差异（线条更简洁）。
           映射：Popsicle2→ice-cream-cone、ChevronDownSmall→chevron-down、
           MagnifyingGlass→search、CrossSmall→x、EditBig→square-pen、
           Home→home、UserAdd→user-plus、Checkmark1Small→check、
           PlusMedium→plus、SettingsGear1→settings、
           SidebarLeftArrow→panel-left-close（展开态 rotate-180）、
           ArrowBoxLeft→log-out。
     GlideMenu（primitives/GlideMenu.tsx）已内联为 initGlide()。
     @classes 声明的是 JS 里分支/动态产生的类（导航选中态、搜索开合态、
     折叠时展开控件的 rotate-180）。


### `streaming-text` — 流式回答

- 成品：`assets/html/streaming-text.html`（41.5 KB）
- 源片段：`assets/ports/streaming-text.frag.html`
- 编译进 CSS 的工具类：84 个
- 未覆盖类：无

来源：components/primitives/StreamingText.tsx（上游 MIT）
     保真：WORD_MS = 55 / HOLD_MS = 3400 逐字照搬；逐词揭示（不是逐字），
           cite token → 内联来源 chip（pop-in 250ms）；尾部 2px 光标在自己 settle 后由
           fade-in 150ms 出现；来源头像堆叠用 .source-avatar（上游自定义类）；
           来源清单展开/收起走 grid-template-rows 1fr/0fr + opacity（cubic-bezier(0.23,1,0.32,1)）；
           追问按钮在 done 后按 i*90ms 逐条 fade-up；三个来源图标是上游内联的 data-URI SVG，原样保留。
     降级：无。
     说明：上游 StreamingText 用的是「逐词揭示」，并没有引用 atoms/StreamText.tsx 或
           atoms/Shimmer.tsx（那两个原子只被 SelectionActions.tsx 使用），所以这里没有内联它们。
     markup 与上游逐类对齐（transition-opacity/… 与 duration-* 都用上游原类名；
           twsubset 现已把 transition-* 排在 duration-* 之前输出，不需要内联兜底）。
     节点策略：token（含 chip）与光标按「只追加」维护，避免每 55ms 重建导致
           chip 的 pop-in 与光标的 fade-in 反复重播（React 里 by-key 复用节点，不会重播）。


### `task-rows` — 任务进度行

- 成品：`assets/html/task-rows.html`（41.2 KB）
- 源片段：`assets/ports/task-rows.frag.html`
- 编译进 CSS 的工具类：70 个
- 未覆盖类：无

来源：components/primitives/TaskRows.tsx（上游 MIT）
     变体：Capsules（独立圆角卡）/ List（单卡 + 分隔线）
     保真：TICKS=[600,900,2400,1400,2400,600] 逐字照搬，驱动 6 拍状态机 ——
           rows 80ms 错峰入场（fade-up 450ms）、row1 ring 扫过、row1 展开、
           row1 收起 + row2 翻 Failed（红底 + 旋转 retry 图标）、row2 收敛 Completed。
           row2 = tick<3 ? pending : tick===3 ? failed : done。
           SpinnerRing：size24/stroke2，r=11，c=2πr，活动弧 dasharray=`${c*0.28} ${c*0.72}`，
           活动时 svg 走 spin 1.1s linear infinite（数值按上游算式实时求，未取整）。
           展开默认值 open = manualOpen[key] ?? (key==='index' && tick===2)；点击后由
           manualOpen 接管。展开区的每条 detail 在「开」时按 120+j*100ms 错峰 fade-up。
           Badge pop-in 300ms、Failed/Completed 药丸 fade-in 200ms 均照搬。
     细节：为忠实还原 DOM，状态药丸是「有则插入、无则移除」（而非占位空 span），
           否则会多出一个 gap-2.5 的间隙；spinner 只在签名变化时重绘，避免每拍重启旋转。


### `thinking-state` — 思考轨迹

- 成品：`assets/html/thinking-state.html`（43.8 KB）
- 源片段：`assets/ports/thinking-state.frag.html`
- 编译进 CSS 的工具类：73 个
- 未覆盖类：无

来源：components/primitives/ThinkingState.tsx（上游 MIT）
     变体：Steps / Reasoning / Search / Coding（画廊里以标签切换，此处带上 port-variants 切换条）。
     保真：STAGES = [800, 600, 1800, 2600, 1600] 逐字照搬；working = stage<3；
           autoExpanded = 1<=stage<4；visible = stage<2 ? 0 : stage===2 ? min(2,rows) : rows；
           行入场 fade-up 320ms cubic-bezier(0.23,1,0.32,1) + i*120ms 逐条错开；
           竖线高度按 trace 实测高度（offsetHeight）动画到 -2px，与上游 useLayoutEffect 一致。
     降级：无。行节点采用「只追加不重建」策略，复现 React key 复用后旧行动画不重播的行为。
     演示取舍：上游跑一遍即停，移植件把它循环重放（便于直接观看）；首屏从 stage 2 起步，
           避开 0~1.4s「轨迹已展开但还没有行」的空窗期。时序常量本身未做任何压缩。
     markup 与上游逐类对齐：border-[1.5px] 与 duration-100/300/400 都用上游原类名
           （twsubset 现已把任意边框宽度编译成 border-width，并按 transition-* → duration-* 的顺序
           输出，故不需要内联兜底）。
     @classes 里声明的是 JS 三元/变量产生的分支类（TONES 三色、primary 文本样式、row.mono、
     选中态 bg-inset / hover:bg-hover），它们不出现在静态 class 属性里，必须显式声明。


### `tool-chips` — 工具调用芯片

- 成品：`assets/html/tool-chips.html`（46.2 KB）
- 源片段：`assets/ports/tool-chips.frag.html`
- 编译进 CSS 的工具类：103 个
- 未覆盖类：无

来源：components/primitives/ToolChips.tsx（上游 MIT）
     保真：STEP_MS=700 逐行揭示；fade-up / pop-in / fade-in 关键帧与延迟逐字照搬；
           文件 diff 芯片的 hover 预览在上游是 createPortal(…, document.body) —— 即
           「渲染进 body 的浮层」，本移植用同样的做法（fixed 定位节点挂在 body，避免
           被父级 transform/动画重定义坐标），并按视口高度自动决定向上/向下翻转。
           const previewHeight = 38 + lines*19、x 夹在 [12, innerWidth-300]、上下 6px 间距、
           transform-origin 随翻转方向变化 —— 全部照搬。
     降级/说明：
       1) 上游 w-[calc(100%+6px)]：Tailwind 会在任意值里给 + - * / 补空格，twsubset 不补，
          故写成 w-[calc(100%_+_6px)]（_ 会被编译成空格），得到与上游相同的 calc(100% + 6px)。
       2) 上游用 body portal；原生 <div popover> 需要 JS 调 showPopover()，行为不等价
          （会劫持 light-dismiss / 顶层层叠），这里沿用 portal 语义。


---

## 重新生成

```bash
cd <skill 目录>
PY="C:/Users/10355/.workbuddy/binaries/python/versions/3.14.3/python.exe"
"$PY" scripts/build_ports.py           # 重新组装全部移植件并刷新本文件
# 渲染验证 + 截图（需绕开沙箱代理）
NODE_PATH="C:/Users/10355/.workbuddy/binaries/node/workspace/node_modules" \
  "C:/Users/10355/.workbuddy/binaries/node/versions/22.22.2-6/node.exe" scripts/verify_ports.cjs
```

改上游之后的完整重生成流程见 `README.md`。
