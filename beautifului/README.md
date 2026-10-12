# beautifului — Beautiful UI 组件库 skill

把 [Beautiful UI](https://www.beautifului.dev)（作者 Shane Levine / Turbo，**MIT**）的
**21 个 AI 原生 UI 组件**打包成一个 WorkBuddy skill：开发 AI 工具时直接取用，
**动效交互与官网一致**，并能根据你正在做的页面推荐该用哪几个组件。

## 一分钟上手

| 我想… | 怎么做 |
|---|---|
| 先看看这些组件长什么样 | 打开 `assets/preview/index.html`（单文件、断网可开，21 个 demo 真在跑） |
| 在 Flask / 任意 HTML 页面里直接用 | 拿 `assets/html/<slug>.html`，零依赖，整个文件或摘 `<style>`+markup+`<script>` |
| 在 React 19 + Tailwind v4 项目里用 | 从 `assets/upstream/components/` 拷 `.tsx`，引入 `assets/foundation.standalone.css`。见 `references/react-integration.md` |
| 让它帮我选组件 | 告诉它你在做什么页面，它会读 `references/recommendation-engine.md` 先问关键问题再推荐 |

组件中英文名对照见 `references/component-catalog.md`。

## 目录结构

```
beautifului/
├── SKILL.md                        # 入口：先问清楚在建什么 → 选轨道 → 给方案
├── manifest.json
├── README.md                       # 本文件
├── LICENSE.beautiful-ui            # 上游 MIT 原文（Shane Levine）
├── THIRD_PARTY_NOTICES.md          # 上游 + npm 依赖许可；付费图标替换说明
├── v1.0.0-self-test.md             # 自测报告（52/52 项通过）
├── _verify/                        # 21 个移植件的 light/dark 渲染截图（验证证据）
├── references/
│   ├── component-catalog.md        # 21 个组件 × 用途/变体/依赖/降级
│   ├── recommendation-engine.md    # intake 问题集 + 场景路由表 + 强制输出格式
│   ├── react-integration.md        # React 接入（含官网 registry 不可达的绕法）
│   ├── html-ports.md               # 21 个移植件逐个说明与保真差异
│   └── foundation-tokens.md        # 令牌 + 关键帧 + 静态化转换（两个坑）
├── scripts/
│   ├── PORTING_GUIDE.md            # 移植配方（改上游后重新移植的说明书）
│   ├── vendor.py                   # 拉上游源码（git 失败时走 jsdelivr）
│   ├── extract.py                  # registry JSON → 落地源码 + 生成离线 registry
│   ├── twsubset.py                 # Tailwind v4 子集编译器（class → CSS）
│   ├── make_foundation.py          # 生成 foundation.standalone.css
│   ├── build_ports.py              # 片段 → 自包含 HTML（按组件裁剪 CSS）
│   ├── verify_ports.cjs            # Playwright 渲染验证 + 截图
│   └── build_preview.py            # 生成预览页
└── assets/
    ├── upstream/                   # 上游 React 源码 + 令牌 CSS + PROVENANCE.json
    ├── registry/                   # public/r/*.json 原样（27 项）
    ├── registry-offline/           # 依赖已改写为相对路径，可离线安装
    ├── foundation.standalone.css   # 浏览器可直接用的令牌层（含 8 关键帧 + 组件级 CSS）
    ├── ports/*.frag.html           # 移植件源片段（可读可改）
    ├── html/*.html                 # 21 个零依赖成品（self-contained）
    └── preview/index.html          # 离线预览页
```

## 两个值得知道的实现细节

### 1. 动效为什么能一致

上游 21 个组件**没有一个用 framer-motion** —— 动效 = 设计令牌 + 8 个 `@keyframes` + React 定时器。
所以移植的关键只有三条：**时序常量逐字照搬**、**颜色/圆角/阴影/缓动继续引用同名 `var(--token)`**、
**DOM 层级不变**。做到了，手感就一样。

### 2. 为什么不手抄 CSS

21 个组件用了几百个 Tailwind 工具类，手抄必然漂移。所以写了个**子集编译器**
（`scripts/twsubset.py`）：读源码里的类名 → 生成刚好覆盖的 CSS，选择器用
`[class~="…"]` 属性形式（工具类含 `/` `:` `[` `]`，转义极易出错）。
好处是 markup 几乎原样保留，改上游后重跑脚本即可。

代价与取舍都写在 `references/foundation-tokens.md`（尤其是
`@theme inline` 里 `--radius/ease/font` 必须搬进 `:root`、
`shadow-plugin` 的阴影刻度必须内联 —— 这两处做错会静默丢样式）。

## 质量状态（v1.0.0）

| 检查 | 结果 |
|---|---|
| 21 个组件 HTML 移植件 | **21/21 生成**，平均 45 KB，全部零依赖自包含 |
| 每个移植件「生成的 CSS 规则是否真的生效」 | **21/21 满分**（如 `css=32/32`） |
| 每个移植件「页面用到的类是否都有 CSS」 | **21/21 满分**（如 `cls=112/112`） |
| JS 运行期错误 | **0** |
| 官方 registry 完整性 | 27 条，`files[].content` 均非空 |
| 令牌一致性 | 36 个关键令牌 + 8 个关键帧齐全，`--shadow-xs…lg` 已内联，无变量环 |
| 断网可用 | 除 Google Fonts 外无外部加载依赖 |
| `scripts/self_test.py` | **52/52 项通过** |

两道渲染后审计值得说明，因为它们专治「看不出来的错」：

- **`css=NN/NN`** —— 把生成 CSS 里每条 `[class~="…"] { prop: value }` 反解出来，
  找到页面上匹配的元素逐个核对 computed style。值比较做了单位换算（`0.625rem` ≡ `10px`）、
  box-shadow 数字多重集比较、以及**把期望值丢进探针元素让浏览器规范化**（解决
  `transparent` ↔ `rgba(0,0,0,0)`、`color-mix` ↔ `color(srgb …)` 的序列化差异）。
- **`cls=NN/NN`** —— 渲染后用真实 DOM 反查：任何「长得像工具类、但页面里没有对应规则」
  的 class 直接判 FAIL。这条是必须的，因为 JS 里用常量/变量拼出的类名
  无法靠静态提取保证收全（历史版本就因此在 agent-screen 上静默丢了 12 个类）。

## 改上游之后怎么重新生成

```bash
cd <这个 skill 目录>
PY="C:/Users/10355/.workbuddy/binaries/python/versions/3.14.3/python.exe"
NODE="C:/Users/10355/.workbuddy/binaries/node/versions/22.22.2-6/node.exe"

"$PY" scripts/vendor.py            # 重新拉上游（会更新 PROVENANCE.json）
"$PY" scripts/extract.py           # 落地 registry 内嵌的 app/beautifui/*.css
"$PY" scripts/make_foundation.py   # 重新生成 foundation.standalone.css（带令牌断言）
"$PY" scripts/build_ports.py       # 重新组装全部移植件
"$PY" scripts/build_preview.py     # 重新生成预览页
NODE_PATH="C:/Users/10355/.workbuddy/binaries/node/workspace/node_modules" \
  "$NODE" scripts/verify_ports.cjs # 渲染验证 + 截图到 _verify/
```

> ⚠️ 本机 `www.beautifului.dev` 与 `api.github.com` **不可达**，`raw.githubusercontent.com` 时通时断。
> `vendor.py` 走的是 `cdn.jsdelivr.net`（实测稳定）。所有联网命令需绕开沙箱代理。

## 许可证

- **上游**：MIT，Copyright (c) 2026 Shane Levine。原文见 `LICENSE.beautiful-ui`。
- **本 skill 的移植件**：同样以 MIT 分发，并保留上游署名。
- **付费图标**：`sidebar-nav` 上游依赖付费的 `@central-icons-react`，
  移植件已全部替换为 lucide 等价内联 SVG。详见 `THIRD_PARTY_NOTICES.md`。
- **不要** `npm i beautiful-ui` —— npm 上那个同名包是 5 年前另一个人发的，与本项目无关。

以本 skill 为基础交付给第三方的产物，请保留上述署名。
