# Beautiful UI → 单文件 HTML 移植指南

给后续所有移植工作的**唯一配方**。写新移植件前先完整读一遍。

## 0. 背景（30 秒）

`assets/upstream/` 是上游 **Beautiful UI**（beautifului.dev，作者 Shane Levine/Turbo，**MIT**）的原始 React 源码。
我们要把其中的 primitive 逐个移植成 **零依赖单文件 HTML**，放进 `assets/ports/<slug>.frag.html`，
由脚本组装成 `assets/html/<slug>.html`。

**为什么能保真**：上游全部动效都是纯 CSS（设计令牌 + 8 个 `@keyframes`）+ React 里的定时器，
**没有任何组件用 framer-motion**。所以只要①时序常量逐字照搬、②颜色/圆角/阴影/缓动继续引用同名
`var(--token)`、③DOM 层级不变，动效就与官网一致。

## 1. 目录与文件

| 路径 | 作用 |
|---|---|
| `assets/upstream/components/primitives/<Name>.tsx` | 上游源码（**权威**） |
| `assets/upstream/components/atoms/<Name>.tsx` | 共享原子（Button / Chip / EntityChip / ValuePill / Shimmer / StreamText / GlideMenu 等） |
| `assets/upstream/app/beautifui/foundation.css` | 令牌 + 8 keyframes + 组件级 CSS（Partial） |
| `assets/upstream/app/beautifui/records-table.css` | `.records-*` 专用 CSS（≈825 行） |
| `assets/upstream/app/beautifui/sidebar-nav.css` | `.sidebar-*` 专用 CSS |
| `assets/ports/<slug>.frag.html` | **你要写的文件** |
| `assets/html/<slug>.html` | 组装产物（自动生成，不要手改） |
| `scripts/twsubset.py` | Tailwind 子集编译器（`class` → CSS） |
| `scripts/build_ports.py` | 片段 → 成品，并按组件裁剪 CSS |
| `scripts/verify_ports.cjs` | Playwright 渲染 + 截图 + 报错收集 |

## 2. 片段文件格式

```html
<!-- title: Thinking -->
<!--@classes: 这里列 JS 里三元/变量产生的类 -->
<!-- 来源：components/primitives/ThinkingState.tsx（上游 MIT）
     保真说明：照搬了哪些时序常量；哪些地方做了降级，为什么。 -->

<div class="port-frame">
  <p class="port-note"><strong>中文名</strong> — 一句话用途 + 触发场景。</p>
  <div class="port-variants" role="group" aria-label="变体">   <!-- 有变体时才要 -->
    <button type="button" class="port-variant-btn" data-variant="Steps" aria-pressed="true">Steps</button>
  </div>
  <!-- 组件本体。动态部分用 id 挂载点 -->
  <div id="think-host"></div>
</div>

<script>
/* 尽量把上游源码里的常量逐字抄下来，并注明出处 */
(function () {
  // ... 渲染 + 交互
})();
</script>
```

要点：
- **`port-frame` / `port-note` / `port-variants` / `port-variant-btn` 是移植件外壳**，样式已内置，直接用。
- **不要写 `<html>/<head>/<body>/<style>`**，组装脚本会补。
- 脚本用 IIFE `(function(){...})()` 包裹，避免污染。
- 中文说明里的 `<code>` 可直接用。

### `@classes` 什么时候要写（现在已可选）

组装脚本按两处收集类名：① markup 里的 `class="..."`；② `<script>` 里**能被编译器认作工具类**的字符串字面量；③ `@classes` 声明。

**② 是后来加的兜底**：JS 里常把类名放在常量/变量里，例如

```js
var cls = round ? 'rounded-full' : 'rounded-[1px]';   // 不走 class=" 字面量
body += '<tr class="records-row ' + cls + '">';        // 变量插在 class 值中间
```

这类类名过去会被**静默漏掉**（CSS 缺失、元素"没样式"，截图和 JS 报错都看不出来）。
现在的做法是「扫所有字符串字面量，但用 `build_rule()` 做准入」：真工具类收下，
`'1.4s'` / `'(p.round'` / `'...'` 这类噪声编译不过、自动被拒。最坏只是多一条用不到的 CSS。

所以 **`@classes` 现在是可选的**：留着当「本组件用到哪些非静态类」的文档与兜底，删掉也不会漏。
不必再手工维护它。

**真正可靠的验收靠渲染后反查**（见第 5 节的 `cls=NN/NN`）：任何"长得像工具类但页面里没有对应规则"的 class 会被直接判 FAIL。

## 3.5 两个会让人误判「写错了」的现象

- **`border-[1.5px]` 在 Chrome 里算出来是 1px。** 这是设备像素取整（1.5px 边框落在整数像素栅格上），
  不是编译器出错。别为了"看起来对"去改成 1px 或 2px。
- **`w-full max-w-*` 放在 shrink-to-fit 的宿主里不会撑开。** `port-frame` 用的是
  `align-items: flex-start`（收缩适应），所以移植件一般是「宿主级元素显式给 `w-full max-w-*`，
  内部卡片用 `w-full`」。这是移植件的固定约定，照着做即可。

## 4. 依赖降级规则

## 3. 移植五步

1. **读源码**。上游注释里有设计意图与时序表（例如 `const STAGES = [800,600,1800,2600,1600]`）。
   **这些数字要 1:1 抄，不要"差不多"**。
2. **DOM 保层级**。`className=` → `class=`；JSX 内联子组件展开成对应标签。
   改动层级会让上游的 CSS 对不上（尤其是 `.records-*`、`.sidebar-*`、`.stream-tail` 这类选择器依赖结构）。
3. **CSS 不用你写**。markup 里继续用 Tailwind 工具类原名，编译器会生成 CSS。
   只有在用**上游自定义类**（`.stream-tail`、`.stream-caret`、`.source-avatar`、`.records-*`、`.sidebar-*`、
   `.filter-status-*`、`.insight-chart-*`、`.primitive-*`、`.component-nav-scroll`）时，
   它们已在 foundation 里，直接用即可，无需声明。
4. **JS 状态机**。`useState`/`useEffect` → 普通变量 + `setTimeout`/`setInterval`/`requestAnimationFrame`。
   上游组件的 `"use client"` 自跑 demo 循环里都是**硬编码数组**，直接抄。
5. **跑验证**（见下），直到 `OK` 且截图看着对。

## 4. 依赖降级规则

| 上游依赖 | 组件 | 降级做法 |
|---|---|---|
| `glimm` | prompt-bar | 原生 `textarea` + 自绘 `@` / `/` 菜单 |
| `liveline` | insight-cards | 自绘 SVG 折线/面积图，复用上游 `.insight-chart-*` CSS |
| `iconoir-react` | selection-actions | 内联 SVG |
| `@central-icons-react`（**付费**） | sidebar-nav | 换 **lucide** 等价图标（内联 SVG path），并在文件头注明已替换 |
| `class-variance-authority` | button | 变体逻辑手写为 class 分支 |
| `clsx` + `tailwind-merge` | 通用 | 不需要：直接拼 class 字符串 |
| Vercel Blob 视频 | loading-state / agent-screen | 保留远端 URL 并做 `onerror` 回退（离线下显示占位） |

内联 SVG 图标统一用 `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ...>` 风格。

## 5. 命令

```bash
# 组装单个（也会做类名覆盖检查）
python -u scripts/build_ports.py --only <slug>

# 渲染验证 + 截图到 _verify/<slug>.{light,dark}.png
NODE_PATH=$(npm root -g) node scripts/verify_ports.cjs --only <slug>
```

**必须做到**：build 输出「未覆盖类 0」，verify 输出 `OK`。
然后**用 Read 工具看 `_verify/<slug>.light.png`**，确认视觉真的对（空白/错位/字太小都算失败）。

注意：脚本会自动找运行时（`$NODE_BIN` / `$NODE_PATH` → PATH 上的 `node` → `~/.workbuddy/binaries/`）。
Playwright 需要启动浏览器，若当前沙箱拦住了，重试时开启「跳过沙箱」。
Google Fonts 外链在离线时会失败，验证脚本已刻意忽略该噪声。

## 6. 质量红线

- **不要发明视觉**。颜色/圆角/阴影/字号一律来自上游 class；不要自创 hex 色值。
  移植件外壳（`port-*`）除外。
- **不要简化动效**。上游的 `transition` 时长、`cubic-bezier`、`animation-delay` 都是刻意的
  （`--ease-out-strong: cubic-bezier(0.23,1,0.32,1)` 之类"强曲线"）。
- **不要丢交互**。hover / focus-visible / 展开折叠 / 拖拽 / 排序 / 键盘导航，上游有的都要在。
  静态截图看不出交互，所以要照着源码的 handler 逐个实现。
- **不要抄上游的英文演示数据就完事**。演示数据可以保留（能体现布局），但要让中文说明交代清楚
  这个组件解决什么问题。
- 组件内部不要依赖外网（字体除外）。
