# React 轨道：把组件接进你的 React 项目

上游是 **React 19 + Tailwind CSS v4 + TypeScript** 的 shadcn registry。

## ⚠️ 先看这一条：官网 registry 在本机不可达

上游每个 registry 条目的 `registryDependencies` 都指向
`https://www.beautifului.dev/r/foundation.json`，而**这个域名在本机解析/连接失败**。
所以直接跑官方 README 里的命令会卡住：

```bash
# ✗ 会失败（依赖 www.beautifului.dev）
npx shadcn@latest add https://www.beautifului.dev/r/approval-card.json
```

本 skill 提供了两条**离线可用**的路径。

---

## 路径 1（推荐）：手拷源码，零工具零联网

最稳，不依赖任何 CLI。

### 步骤

1. **建一个 Tailwind v4 项目**（已有时跳过）：
   ```bash
   npx shadcn@latest init            # 生成 components.json，Tailwind v4 项目必需
   ```

2. **拷组件源码**。每个组件是一个自包含 `.tsx`：
   ```
   assets/upstream/components/primitives/<Name>.tsx  →  你的 components/primitives/
   ```
   `<Name>` 与 slug 的对应见 `component-catalog.md`（如 `approval-card` → `ApprovalCard.tsx`）。

3. **拷它依赖的共享原子**（漏了会编译报错）。对照目录表里的「上游共享依赖」列：
   ```
   assets/upstream/components/atoms/Button.tsx        →  components/atoms/
   assets/upstream/components/primitives/GlideMenu.tsx→  components/primitives/
   assets/upstream/components/atoms/EntityChip.tsx    →  components/atoms/
   assets/upstream/components/atoms/ValuePill.tsx     →  components/atoms/
   assets/upstream/components/atoms/Shimmer.tsx       →  components/atoms/
   assets/upstream/components/atoms/StreamText.tsx    →  components/atoms/
   ```
   项目里没有 `lib/utils.ts`（`cn` 工具）时，一并从
   `assets/upstream/lib/utils.ts` 拷过去。

4. **接设计令牌**。这是最关键的一步，决定视觉与动效对不对：
   ```
   assets/foundation.standalone.css  →  你的 app/foundation.css（或直接 import）
   ```
   `foundation.standalone.css` 是把你需要的令牌、8 个 `@keyframes`、
   `.records-*` / `.sidebar-*` 等组件级 CSS 全部打包好的**纯 CSS**（不是 Tailwind 语法），
   在 `globals.css` 里 `@import "./foundation.css";` 即可。

   > 上游原版 `app/globals.css` 是 Tailwind v4 语法（含 `@theme inline`、`@import "tailwindcss"`），
   > 只适合他自家的 Next.js 工程。我们要的是**令牌层**，所以用 standalone 版更省事。
   > 如果你坚持用上游原版，记得 `@import "tailwindcss";` 必须在最前，且装 `shadow-plugin`
   > （`--shadow-btn/card/raised/overlay` 引用它的 `--shadow-xs…lg`）。

5. **装 npm 依赖**：
   ```bash
   npm i clsx tailwind-merge class-variance-authority
   ```
   只有 `Button.tsx` 用到 `class-variance-authority`；`clsx` + `tailwind-merge` 是 `cn` 的实现。
   用哪个组件就装哪个的额外依赖：

   | 组件 | 额外 npm 包 | 是否已在本 skill 里降级 |
   |---|---|---|
   | `prompt-bar` | `glimm` | ✅ HTML 移植版已用原生 textarea 替代；**React 版仍需装** |
   | `insight-cards` | `liveline` | ✅ HTML 移植版自绘 SVG；**React 版仍需装** |
   | `selection-actions` | `iconoir-react` | ✅ HTML 移植版内联 SVG；**React 版仍需装** |
   | `sidebar-nav` | `@central-icons-react/round-outlined-radius-2-stroke-2`（**付费**） | ✅ HTML 移植版已换 lucide；**React 版需自己换掉**，见下 |

6. **字体**：上游假定 `Inter` + `JetBrains Mono`。Next.js 里用 `next/font/google` 注入
   `--font-inter` / `--font-mono-face`；非 Next 项目把 `--font-sans` / `--font-mono`
   改成你自己的字面栈即可（standalone CSS 里已经是字面栈）。

### 关于付费图标（必看）

`sidebar-nav.tsx` 顶部 import 了 12 个付费图标：

```
IconArrowBoxLeft, IconCheckmark1Small, IconChevronDownSmall, IconCrossSmall,
IconEditBig, IconHome, IconMagnifyingGlass, IconPlusMedium, IconPopsicle2,
IconSettingsGear1, IconSidebarLeftArrow, IconUserAdd
```
来自 `@central-icons-react/round-outlined-radius-2-stroke-2`，安装时会跑许可证检查
（需要 `CENTRAL_LICENSE_KEY`）。**免费替代方案**：换成 `lucide-react` 的同义图标
（ArrowLeftFromLine / Check / ChevronDown / X / Pencil / House / Search / Plus / IceCream / Settings / PanelLeft / UserPlus）。
更省事的做法：直接用本 skill 的 `assets/html/sidebar-nav.html`，
里面已经替换好了。

---

## 路径 2（备选）：用本地 registry 安装

`assets/registry-offline/` 里的条目已经把 `registryDependencies` 从
`https://www.beautifului.dev/r/xxx.json` 改写成相对文件名 `./xxx.json`，因此可以离线解析：

```bash
# 把整个 registry-offline 目录放到项目里，然后：
npx shadcn@latest add ./assets/registry-offline/approval-card.json
```

> **注意**：`shadcn` CLI 对「本地文件路径作为 registry 源」的支持随版本变化，
> 且它仍需要联网解析 npm 依赖。**这条路径请以实际试跑结果为准**；
> 跑不通就用路径 1 手拷 —— 组件本身不锁定任何 CLI。

---

## 上游组件的性质（重要预期管理）

上游 README 说得很直白，这里照抄并翻译：

> 每个组件都是 `"use client"` 且**自带动画** —— 它们跑自己的演示循环（流式、思考、稳定），
> 而**不是接收数据 props**。请把它们当作**视觉参考**，用来接入你自己的真实状态，
> 而不是当成成品 API。

所以接入真实后端时，你要做的是：

1. 把组件内部的 `useEffect` 演示循环**换成由真实事件驱动**。
   例如 `ThinkingState` 的 `STAGES` 数组，换成你的 SSE/WebSocket 事件流。
2. 上游 `lib/meta.ts` 里每个组件的 `variants` / `deps` 是接线的路标。
3. 上游仓库 README 有一节 "Wiring the harness to a real agent"，给出 demo 接缝与替换对照表；
   对应源码在仓库的 `app/harness/page.tsx`（本 skill 未收录，需要时从上游取）。

## 反查上游文件路径

| 需要什么 | 去哪找 |
|---|---|
| 组件源码 | `assets/upstream/components/primitives/`、`assets/upstream/components/atoms/` |
| 令牌 + keyframes + 组件级 CSS | `assets/upstream/app/beautifui/foundation.css` |
| `.records-*` 专用 CSS | `assets/upstream/app/beautifui/records-table.css` |
| `.sidebar-*` 专用 CSS | `assets/upstream/app/beautifui/sidebar-nav.css` |
| 上游原始 `globals.css`（Tailwind v4 语法，37KB） | `assets/upstream/app/globals.css` |
| 画廊清单（caption/variants/deps/npm） | `assets/upstream/lib/meta.ts` |
| registry 条目原文 | `assets/registry/*.json` |
| 版本与出处 | `assets/upstream/PROVENANCE.json` |
