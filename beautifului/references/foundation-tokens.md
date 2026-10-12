# 设计令牌与关键帧速查

上游是靠 **66 个 CSS 自定义属性 + 8 个关键帧**驱动的。要改皮肤，改这里就够了；
改别处（组件里的 class）都是错的。

本 skill 的 `assets/foundation.standalone.css` 是**浏览器可直接用的纯 CSS 版**，
已把令牌、关键帧、组件级 CSS 全部打包。**在项目里用这个，不要用上游的 Tailwind 语法原版。**

---

## 一、怎么把上游那份 Tailwind v4 的 CSS 变成本文件能用的

上游 `app/beautifui/foundation.css` 是给 Tailwind v4 编译器吃的，原生浏览器跑不了。
转换规则（由 `scripts/make_foundation.py` 自动完成，**两个坑最容易踩**）：

| 上游语句 | 处理 | 为什么 |
|---|---|---|
| `@import "tailwindcss";` | 删除，换 ~40 行极简 reset | Tailwind 的 preflight 我们只需要最基础那部分 |
| `@import "shadow-plugin/unprefixed";` | 删除，**把 `--shadow-2xs…2xl` 的字面值内联进 `:root`** | `--shadow-btn/card/raised/overlay` 引用它们，不内联则**所有阴影全丢** ⚠️ |
| `@custom-variant dark (&:where(.dark, .dark *));` | 删除 | 它只是 Tailwind 的变体声明；`.dark {}` 本身已是普通 CSS |
| `@theme inline { ... }` | **整块删除，但把 `--radius-*` / `--ease-*` / `--font-*` 搬进 `:root`** | 这三组令牌**只声明在 `@theme` 里、不在 `:root`**；不搬则**圆角与缓动曲线全部丢失** ⚠️ |
| `@theme inline` 里的 `--color-*` 映射 | 丢弃 | 它们只为让 `bg-surface` 这类 Tailwind 工具类能解析；纯 CSS 里直接写 `var(--surface)` |
| `@theme inline` 里的 `--shadow-x: var(--shadow-x)` | **必须丢弃** | 自引用别名，搬进 `:root` 会造成 CSS 变量环（该变量永久失效） |
| `--font-sans: var(--font-inter), …` | 换成字面字体栈 | 上游靠 `next/font` 注入 `--font-inter`，脱离 Next.js 后该变量为空 |

> 结论：**删 `@theme inline` 时一定要搬 `--radius/ease/font`，删 `shadow-plugin` 时一定要内联阴影刻度。**
> 这两件事做错，页面看起来"差不多对"，但动效曲线和阴影会静默降级 —— 最难查的那种 bug。
> `scripts/make_foundation.py` 末尾有断言，缺任何一个都会在终端报警。

---

## 二、令牌清单

### 语义色（明暗两套，各 24 个）

| 令牌 | 用途 | 浅色 | 深色 |
|---|---|---|---|
| `--page` | 最底层页面底色 | `oklch(0.985 0.001 286.376)` | `oklch(0.209 0.004 264.477)` |
| `--canvas` | 画布（比 page 略深） | `oklch(0.961 0.002 247.84)` | `oklch(0.231 0.004 264.487)` |
| `--surface` | 卡片/弹层表面（浅色模式下是纯白） | `oklch(1 0 0)` | `oklch(0.26 0.006 271.191)` |
| `--inset` | 内凹区（输入框底、代码块底） | `oklch(0.979 0.002 247.839)` | `oklch(0.243 0.004 264.492)` |
| `--hover` | 悬停底色（浅） | `oklch(0.97 …)` | `oklch(0.289 …)` |
| `--hover-2` | 悬停底色（重） | `oklch(0.933 …)` | `oklch(0.318 …)` |
| `--ink` | 主文字 | `oklch(0.247 …)` | `oklch(0.964 …)` |
| `--ink-2` | 次要文字 | `oklch(0.506 …)` | `oklch(0.731 …)` |
| `--ink-3` | 三级文字/占位 | `oklch(0.695 …)` | `oklch(0.541 …)` |
| `--line` | 主描边（**实色，不是半透明**） | `oklch(0.946 …)` | `oklch(0.308 …)` |
| `--line-strong` | 重描边 | `oklch(0.912 …)` | `oklch(0.356 …)` |
| `--line-soft` | 轻描边 | `oklch(0.966 …)` | `oklch(0.278 …)` |
| `--grid-line` | 网格线（由 `--line` 混出 78%） | `color-mix(…)` | 继承 |
| `--field` | 字段/药丸底色 | `oklch(0.961 …)` | `oklch(0.293 …)` |
| `--stripe` / `--stripe-bg` | `body` 的 45° 斜条纹底纹 | 见文件 | 见文件 |
| `--accent` | **唯一强调色**（蓝） | `oklch(0.626 0.205 254.947)` ≈ `#0285FF` | `oklch(0.68 0.173 253.301)` |
| `--accent-ink` | 强调色文字版（保证对比度） | `oklch(0.556 0.187 255.617)` | `oklch(0.788 0.113 248.33)` |
| `--accent-tint` | 强调色淡底 | `oklch(0.96 0.019 252.878)` | 同色 16% alpha |
| `--green` / `--green-tint` | 成功 | `oklch(0.603 0.155 150.883)` | `oklch(0.705 0.154 153.814)` |
| `--orange` / `--orange-tint` | 警告 | `oklch(0.689 0.179 49.902)` | `oklch(0.746 0.156 55.642)` |
| `--red` / `--red-tint` | 危险 | `oklch(0.621 0.192 23.042)` | `oklch(0.666 0.18 21.433)` |
| `--tooltip-bg/-fg/-muted/-border` | tooltip 四件套 | 深底浅字 | 更深底 |

设计取向（上游注释原文意译）：**冷调、蓝偏中性灰；实色细描边而非半透明；
强调色像调味料一样省着用。**

### 阴影（10 个）

| 令牌 | 说明 |
|---|---|
| `--shadow-hairline` | `0 0 0 1px var(--line)` —— 纯描边，无投影 |
| `--shadow-btn` | 描边 + `--shadow-xs` |
| `--shadow-card` | 描边 + `--shadow-sm` |
| `--shadow-raised` | 描边 + `--shadow-md` |
| `--shadow-overlay` | 描边 + `--shadow-lg`（弹层用） |
| `--shadow-inset-field` | 内阴影，用于输入框凹陷感 |
| `--shadow-2xs` … `--shadow-2xl` | 来自 `shadow-plugin@2.1.0` 的**平滑多层**堆叠 |

> 深色模式下 `--shadow-btn/card/raised/overlay` 换成**低透明白色描边**（`oklch(1 0 0 / 0.1~0.15)`）——
> 因为描边画在元素身后的表面上，浅色细边能融进阴影形成一条连续描边。这个细节别改。

### 字体

| 令牌 | 值（standalone 版） |
|---|---|
| `--font-sans` | `'Inter', ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif` |
| `--font-mono` | `'JetBrains Mono', ui-monospace, 'SF Mono', Menlo, Consolas, monospace` |

`body` 上还设了 `font-size: 14px`、`letter-spacing: -0.01em`、`line-height: 1.5`、
`font-feature-settings: "cv11", "ss01"`（Inter 的紧凑字距 + 等宽数字替代）。
**表格数字（tabular figures）**是这套 UI 的辨识度来源之一，别去掉。

### 圆角（4 个 + pill）

`--radius-chip: 6px`（芯片）· `--radius-control: 8px`（控件）·
`--radius-card: 10px`（卡片）· `--radius-window: 14px`（窗口）· `9999px`（药丸）
上游注释特意标注了这套梯度，**不要随手改成 8/12/16**。

### 缓动（3 个，很关键）

| 令牌 | 值 | 用途 |
|---|---|---|
| `--ease-out-strong` | `cubic-bezier(0.23, 1, 0.32, 1)` | 入场、位移、悬停 |
| `--ease-in-out-strong` | `cubic-bezier(0.77, 0, 0.175, 1)` | 来回切换 |
| `--ease-link` | `cubic-bezier(0.16, 1, 0.3, 1)` | 下划线展开等 |

上游注释原话：**"strong curves; built-ins are too weak"** ——
内置的 `ease`/`ease-in-out` 曲线太平，这套 UI 的"手感"很大程度上来自这三条强曲线。
**换成 `ease` 或 `ease-out` 会明显变廉价。**

---

## 三、8 个关键帧（+1）

| 关键帧 | 用途 | 定义要点 |
|---|---|---|
| `pixel-on` | 像素网格加载器 | `0%,100% {opacity:.15}` → `18%,42% {opacity:1}` → `62% {opacity:.15}`；**逐格错开 delay 形成波浪** |
| `shimmer-text` | 微光文字 | `background-position` 从 `150%` 移到 `-50%`；配合 `background-clip: text` + 渐变 |
| `fade-up` | 上浮入场 | `opacity 0→1`, `translateY(8px)→0` |
| `fade-in` | 淡入 | 仅 `opacity 0→1` |
| `pop-in` | 弹出 | `opacity 0→1`, `scale(.95)→1` |
| `spin` | 旋转 | `rotate(360deg)` |
| `eq-bounce` | 均衡器跳动 | `scaleY(.35)→1→.35` |
| `caret-blink` | 光标闪烁 | `step-end`，`opacity 1→0→1`，1s |
| `records-pulse` | 记录表格的行脉冲 | 仅在 `records-table.css` 中 |

## 四、组件级自定义类（不是工具类，别当 Tailwind 使）

这些类在上游是"随组件一起拷"的 CSS 块，已被打进 `foundation.standalone.css`：

| 类 | 归属组件 | 作用 |
|---|---|---|
| `.stream-tail` | StreamText | 尾部 1.6px 模糊 + 遮罩渐变，制造"正在解析"的边缘 |
| `.stream-caret` / `.is-streaming` | StreamText | 光标；流式时**实心不闪**，停了才闪 |
| `.source-avatar` | StreamingText / ContextCards | favicon 圆形头像的细描边 |
| `.records-*`（~40 个） | RecordsTable | 约 825 行的网格、标签、列选择、拖拽手柄样式 |
| `.sidebar-*` | SidebarNav | 224px 树 / 52px 壳的折叠几何 |
| `.filter-status-todo/-progress/-done` | FilterTable | 用 `--tag-base` + `color-mix` 派生状态色 |
| `.insight-chart-*` | InsightCards | 图表游标线与 tooltip 定位 |
| `.primitive-card-pad/-bar/-footer`、`.primitive-table-cell`、`.primitive-icon-button` | 通用 | 小卡片的统一光学间距（12px / 10px 12px / 10px / 28px 图标按钮） |
| `.component-nav-scroll` | 画廊导航 | 隐藏滚动条 + 底部渐隐遮罩 |
| `.animated-underline` | 通用 | hover 时从左展开下划线（280ms `--ease-link`） |
| `.agent-cursor` | AgentScreen | Agent 的自绘鼠标光标 |

## 五、改皮肤的正确姿势

`foundation.standalone.css` 里组件只通过**令牌**取色（`bg-surface` → `var(--surface)`、
`text-ink-2` → `var(--ink-2)`、`shadow-card` → `var(--shadow-card)`），
所以**换肤 = 只改 `:root`（和 `.dark`）两个块**。不用去动任何组件 class。

```css
:root {
  --accent: #6d28d9;         /* 换个强调色 */
  --accent-ink: #5b21b6;
  --accent-tint: #ede9fe;
}
```

明暗切换：把 `dark` 类挂到 `<html>` 或任意祖先元素上即可，整组令牌一起换。
上游还给 `.theme-switching *` 加了 `transition: none !important` ——
**切换主题时冻结过渡**，避免上百个颜色同时渐变换来换去的闪噪。这个技巧值得照抄。

## 六、响应式与无障碍

- `.records-*` 在 `@media (hover: none)` 下**主动关掉 hover 底色** ——
  因为触屏上 `:hover` 会在点击后粘住。移植时别丢这段。
- `@media (prefers-reduced-motion: reduce)` 存在两处：一处单独处理 `.stream-caret` /
  `.stream-tail`，一处把所有动画压到 `0.01ms`。**两层都要保留**，
  否则开了系统级减弱动效设置的用户仍会看到流式模糊。
- `:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }` 是全局焦点样式；
  但输入类元素（`input/textarea/select/[contenteditable]`）的 outline 被显式关掉，
  它们靠自身的 `shadow` 令牌表达焦点。
