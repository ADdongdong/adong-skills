# THIRD_PARTY_NOTICES

## 1. 上游主体：Beautiful UI

- **作品**：Beautiful UI — Crafted primitives for AI-native interfaces（21 个组件）
- **作者**：Shane Levine（Turbo，<https://turbodesign.co>）
- **主页**：<https://www.beautifului.dev>
- **源码**：<https://github.com/slev12397/beautiful-ui>
- **许可证**：MIT，Copyright (c) 2026 Shane Levine
- **许可原文**：见本目录 `LICENSE.beautiful-ui`

本 skill 收录了该项目的组件源码（`assets/upstream/`）、registry 构建产物（`assets/registry/`）、
设计令牌与组件级 CSS，并据此产出单文件 HTML 移植版（`assets/html/`）。
**所有移植件同样以 MIT 分发，并保留上述署名。**

获取时间与 commit 见 `assets/upstream/PROVENANCE.json`。

## 2. 上游的 npm 依赖（仅 React 轨道需要）

| 包 | 版本 | 许可证 | 用在哪 | 本 skill 的处理 |
|---|---|---|---|---|
| `react` / `react-dom` | ^19.1.0 | MIT | 全部组件 | 仅 React 轨道需要 |
| `tailwindcss` | ^4.1.8 | MIT | 全部组件的类名 | React 轨道需要；HTML 移植版已编译为纯 CSS，**不需要 Tailwind** |
| `clsx` | ^2.1.1 | MIT | `lib/utils.ts` 的 `cn` | React 轨道需要 |
| `tailwind-merge` | ^3.6.0 | MIT | `lib/utils.ts` 的 `cn` | React 轨道需要 |
| `class-variance-authority` | ^0.7.1 | Apache-2.0 | `atoms/Button.tsx` | React 轨道需要；HTML 移植版手写变体分支 |
| `motion` | ^13.1.0 | MIT | **仅站点画廊外壳**（`components/site/*`），21 个组件本身均未使用 | 本 skill 未收录站点外壳，**因此不需要** |
| `shadow-plugin` | ^2.1.0 | MIT（作者 Florian Kiem / flornkm） | 提供 `--shadow-xs…2xl` 平滑多层阴影 | **已将字面值内联**进 `foundation.standalone.css` 的 `:root`，运行期不需要该包 |
| `glimm` | ^0.3.0 | MIT | `prompt-bar` 的输入解析 | **HTML 移植版已降级**为原生 `<textarea>` + 自绘 `@`/`/` 菜单；React 原码仍需装 |
| `liveline` | ^0.0.7 | MIT | `insight-cards` 的图表 | **HTML 移植版已降级**为自绘 SVG 折线/面积图；React 原码仍需装 |
| `iconoir-react` | ^7.11.1 | MIT | `selection-actions` 的图标 | **HTML 移植版已降级**为内联 SVG；React 原码仍需装 |
| `@central-icons-react/round-outlined-radius-2-stroke-2` | ^1.1.315 | **商业许可（付费，需 license key）** | `sidebar-nav` 的 12 个图标 | **⚠️ 已在本 skill 中全部替换为 lucide 等价图标**，详见下节 |
| `@web-kits/audio` | ^0.1.0 | MIT | 站点交互音效 | 未收录站点外壳 |
| `next` | ^15.3.3 | MIT | 上游演示站框架 | 未使用 |
| `agentation` | ^3.0.2 | MIT | 上游开发期工具 | 未收录 |

### 2.1 付费图标替换说明（`sidebar-nav`）

上游 `components/primitives/SidebarNav.tsx` 从 **付费**图标包
`@central-icons-react/round-outlined-radius-2-stroke-2` 引入 12 个图标，
该包安装时会执行许可证校验（需要 `CENTRAL_LICENSE_KEY`）。

本 skill 的 HTML 移植版 `assets/html/sidebar-nav.html` **已把这 12 个图标全部替换为
lucide 风格的自绘内联 SVG**，只依赖几何路径形状，不再需要任何图标包。

替换对照（上游 → lucide 等价语义）：

| 上游图标 | 替换为 |
|---|---|
| `IconArrowBoxLeft` | `arrow-left-from-line` |
| `IconCheckmark1Small` | `check` |
| `IconChevronDownSmall` | `chevron-down` |
| `IconCrossSmall` | `x` |
| `IconEditBig` | `pencil` |
| `IconHome` | `house` |
| `IconMagnifyingGlass` | `search` |
| `IconPlusMedium` | `plus` |
| `IconPopsicle2` | `ice-cream-cone` |
| `IconSettingsGear1` | `settings` |
| `IconSidebarLeftArrow` | `panel-left` |
| `IconUserAdd` | `user-plus` |

**⚠️ 注意**：`assets/upstream/components/primitives/SidebarNav.tsx` 是**上游原码，仍带着付费依赖**。
如果你走 React 轨道并直接拷这个文件，**必须自己完成上述替换**，
否则会触发付费包的许可证校验。替换后的完整实现可以直接参考 `assets/html/sidebar-nav.html`。

### 2.2 图标形状来源

移植件中使用的内联 SVG 路径形状，语义与几何参考自 **Lucide**（ISC 许可证）。
Lucide 许可证：<https://github.com/lucide-icons/lucide/blob/main/LICENSE>

## 3. 字体

上游假定使用 **Inter** 与 **JetBrains Mono**。

| 字体 | 许可证 | 说明 |
|---|---|---|
| Inter | SIL Open Font License 1.1 | 由上游通过 `next/font/google` 注入 `--font-inter` |
| JetBrains Mono | SIL Open Font License 1.1 | 由上游通过 `next/font/google` 注入 `--font-mono-face` |

**本 skill 未内嵌字体文件**，移植件通过 Google Fonts CDN 链接引用；
离线时会回退到系统字体栈（`ui-sans-serif` / `ui-monospace`），排版度量会有轻微差异。
如需完全保真，请自行下载这两个字体的 woff2 并在项目中本地托管（均允许再分发）。

## 4. 演示数据

上游画廊使用一套虚构的**冰淇淋 / 雪葩电商**演示数据（风味、供应商、销售趋势等），
其中出现的 `scoopdata.io`、`marketbasket.io`、`*.example.com` 等域名均为示意。
本 skill 的移植件保留了这套演示数据以便还原布局，**它与任何真实企业无关**。

## 5. 名称冲突提醒

npm 上存在一个 **5 年前发布的同名包 `beautiful-ui@1.0.31`**（作者 `chenqw`，与该项目**无关**）。
请勿执行 `npm i beautiful-ui`。
本 skill 对应的上游**没有发布 npm 包**，只通过 shadcn registry 源码分发。
