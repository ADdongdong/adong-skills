---
name: cozyledger-design-tokens
description: 校验/修改「沙拉记账 CozyLedger」（E:\14_myProject\shalajizhang，Android + Jetpack Compose）的设计令牌与图标。当任务涉及改配色、加/改语义色角色、拆分图表色组、重建图标 sprite、排查「深色模式取错色」或「图标显示成文字」、或改动 design/ 目录下的令牌与原型时使用。也覆盖「UI 还是丑 / 参考某个 App 的风格」这类需要做视觉方向改版的请求。
agent_created: true
---

# CozyLedger 设计令牌与图标

## 当用户说「还是丑，参考某个 App」时的工作流

用户三次推翻配色方向（v2 冷蓝 → v3 暖色 → v4 中性），每次都不是审美口味问题，
而是**结构问题**。踩出来的流程：

1. **去读参照对象的源码，不要只看截图。** 截图能看出"好看"，看不出"为什么好看"。
   本次抓 komi-store：`curl` 它的 GitHub tree API 找主题文件 →
   `personality/classic/ClassicColors.kt` + `StatusPalette.kt` + `AccentId.kt`
   + `ColorContrast.kt`，**它为什么成立就全在源码里**（中性灰阶 + 强调色变量化 +
   装饰层归零 + 状态色独立）。
2. **量化对照，不要说"更简洁"。** 「整体有个颜色」= 底色 Lab 色度 3.53 vs 1.02；
   「太花」= 带强调色的元素 12+ 处 vs 3 处。给出数字，用户才能确认你听懂了他。
3. **照抄前算「色相预算」。** 参照对象的设计前提可能和我们的语义约束冲突
   （komi 的红/琥珀撞我们的收入红/超支红/提醒琥珀）。**先列色相占用表，再决定能抄哪几个。**
4. **把可选项做进原型让用户当场选，而不是问。** 用户说不清"要多暖"，
   但能在原型里点着比。v4 把强调色做成 4 个预设的切换器（照 komi 的设置页），
   把「暖/冷/无色」这个说不清的问题变成了一个点击动作。

**判断改版是否真的解决了问题的自检法**：
把截图饱和度拉到 0 —— **如果信息层级和审美都没塌，说明颜色用对了地方。**

**照抄参照对象时，一定要验它的对比度。** 已经抓到它两处缺陷：
`outline #C4C6CF` 对白底只有 1.65（不达 1.4.11 的 3:1）；
下载态「半透明底 + 原字色」8/8 组合只有 1.61–1.94:1。
**"看起来高级"和"算下来达标"是两件事，前者不保证后者。**

## 长流程与操作反馈：借鉴 komi 安装模块的三条结构纪律

完整拆解见 `design/BORROW-KOMI-INSTALL.md`。核心源码
`feature/details/presentation/.../components/SmartInstallButton.kt`（整个安装流程就一个按钮）。

| # | 纪律 | 为什么 |
|---|---|---|
| 1 | **一个控件承担完整生命周期**，禁止「disabled + 转圈 + toast」三跳 | 用户视线不离开手指按下的位置。原地换文案/副标题/配色，**控件不换、位置不动** |
| 2 | **状态之间换视觉语言，不调透明度** | 「主色 @40%」出来是发灰的脏主色（像坏了）；「中性面 + 中性字」是干净的安静态 |
| 3 | **重要的东西不许藏起来** | 危险操作常驻可见不得进 `⋯`；默认选项排第一并写明理由 |

### ⚠️ 抄参照对象前，先确认「约束对得上」

**已经抄错过一次，代价是重做一遍。** 把「安装 → 下载 → 校验 → 安装」硬映射成
「记一笔 → 保存中 → 同步中 → 已同步/待同步」，两处都不成立：

| 抄错的 | 为什么不成立 |
|---|---|
| 同步态 / 待同步态 | **概念错**：本项目的 `PendingScreen`（待确认）指的是**自动识别到的流水待用户确认**（支付宝/微信通知解析），不是"待同步到云端" |
| 「保存中」+ 进度填充 | **多此一举**：本地写入毫秒级，而规则本身就写着"不足 400ms 不显示进度" |

> **借鉴的是"为什么这么做"，不是"做了哪些状态"。**
> 每个机制背后都有一个约束（komi 的约束是"下载要几十秒、中途要能取消"）。
> **约束对不上，机制就不该搬 —— 否则就是凭空长出一个不存在的问题。**

**记一笔的正确形态（已落地）**：

```
记一笔 ──点保存──▶ 已记下（约 0.7s）──▶ 抽屉下滑关闭
                       └──本地写入失败──▶ 重试
```

三态 `idle / done / failed`，无进度、无同步文案。
**抽屉关闭这个动作本身就是"记好了"的反馈**，不需要 toast。
云端同步依然存在，但只在「我的 / 设置」页的运行状态里展示。

### 剩下的借鉴点（仍然有效）

- **主操作 + 尾部 pill 组合**：咬合圆角（主按钮右下收小、尾部左下收小）+ 中间留 6dp
  而非贴合。**尾部随状态换动作需要"有第二个动作可换"** —— komi 有（下载中途可取消），
  我们没有，所以尾部只在空闲可用，其余状态退成惰性。
- **主操作带上下文副标题**：主标题是动作，副标题是"这次动作作用于什么"
  （`餐饮 · 我 · 今天`）。对记账尤其有用 —— 提交前最后确认"记给谁、记哪个分类"。
- **禁用态用中性面 + 45% 文字**，不是整体 alpha。
- **分隔线只占 66% 高度**（`DividerHeightFraction = 0.66f`），与图标光学对齐而非与容器对齐。
- **默认选项排第一**（`VariantPickerDialog` 第一行永远是「自动」+ 一行解释）；
  失效降级时说清"之前是哪个"。

### 我们补的一条（komi 那边也没有）

**控件退成不可用时，外观也要跟着退。**
只拦 `onClick` 不够 —— **「长得像能点却不能点」是假承诺**。
原型里 `.btn-tail.is-inert`（中性底 + `fg2` 图标）与主按钮的 done/failed 底同色，
两块读作一组静止控件。

**不跟的一条**：M3 Expressive 的波浪进度（`CircularWavyProgressIndicator`，Classic 人格在用）。
调性活泼，与 v4 的中性克制冲突；本项目也没有毫秒级以上的等待。

### 进度填充的硬约束（模式对，但本项目暂无落点）

| 项 | 要求 |
|---|---|
| 填充 vs 轨道 RGB 距离 | **≥45**（否则"推了看不出来"） |
| 文字对比度 | 对**轨道**和**填充**都要 **≥4.5** |
| 推荐组合 | 轨道 `surfaceInset` · 填充 `color-mix(in srgb, accent 35%, surfaceInset)` · 文字 `accentStrong` |

反例：`accentSoft` 当填充对它自己的轨道只有 **25.9** —— 看着像没动。
**落点留给**：账单导入 / 数据备份恢复 / 月报导出 PDF / 批量确认 >20 笔。

### 原型里的实现要点

- 状态存在 `state.save`（不是 DOM 里）—— `renderStage()` 每次重建 DOM，状态必须可重建。
- 动画用 `paintSaveBtn()` **只更新按钮自身**，不整屏重渲染，否则过渡被打断。
- 事件用**委托**绑在 `#stage` 上（`e.target.closest('#saveBtn')`），因为 DOM 每次重建。
- 深链接参数：`save = idle|done|failed`，`offline = 0|1`（工具栏「模拟保存失败」）。

## 当前配色版本：v4 中性底 + 强调色可变

**底色与面色不带颜色。** 浅 `bg #FBFBFD` / `surface #FFFFFF` / `fg #1A1C1E` / `fg2 #44474E` / `muted #71747E` / `border #8A8D96`
深 `bg #111316` / `surface #1A1C1E` / `surfaceWarm #202226` / `surfaceRaised #282A2E`

**强调色是变量，不是品牌身份** —— 4 组预设，由 `[data-theme]` × `[data-accent]` 决定：

| 预设 | 浅色 primary | 深色 primary |
|---|---|---|
| `cobalt` 钴蓝（默认） | `#3B5BDB` | `#B6C4FF` |
| `copper` 铜棕 | `#8A6455` | `#DCAE96` |
| `frost` 青霜 | `#00696E` | `#4DD9E3` |
| `mono` 墨灰 | `#4A4A4A` | `#C7C7C7` |

语义色（固定，不随强调色变）：income `#D14132` / expense `#1F7C5C` / danger `#AF352A` / success `#2E6B45` / warn `#BD890B`

历史：v1 暖珊瑚（未落地）→ v2 天空蓝青 → v3 暖陶土（因「整体有个颜色不好看」被推翻）→ **v4 中性底（现行）**

### 迭代轨迹的教训：v3 错在哪

v3 把底色、阴影、图标圆底、头像、chip 全部做成暖色，**屏幕上带强调色的元素有 12+ 处**。
换成蓝色也一样错 —— **错的是「面积」，不是「色相」。**

量化对照：浅色底 Lab 色度 3.53 → **1.02**；首页强调元素 12+ → **3 处**。

v4 参照 **komi-store 的 Classic 人格**（`core/presentation/.../personality/classic/ClassicColors.kt`）。
它好看的原因不是配色，是结构：

1. 底色与面色是**纯中性灰阶**（Lab 色度 1.0–2.2）
2. **强调色不碰底与面**，只出现在：主操作填充 / 选中态 / 小徽章 / 焦点环
3. 强调色是**变量**（同 `AccentId.kt`），不是品牌身份
4. 状态色独立成组（`StatusPalette.kt`，GitHub Primer 色）
5. **Classic 把装饰层显式关到 0**：`screentoneOpacity = 0`、`gridOpacity = 0`

### 色相预算（改任何颜色前先算这笔账）

**语义色用掉一个色相，强调色与分类色就不能再用它。**

| 占位 | 色相 |
|---|---|
| 语义色 | 红 6°（收入/超支）· 绿 143°（支出/达成）· 青绿 159° · 琥珀 42°（提醒） |
| 强调色 | 蓝 228° · 棕 20° · 青 183° · 灰 |
| **剩下的给分类色** | **22° / 52° / 88° / 118° / 206°** —— 只有五段 |

由此推出两条硬约束：

- **分类色板是 6 色（5 有色 + 1 消色「其他」）**，不是 7 色。第 6 槽给消色灰表示「其他/未分类」，它不与任何语义色争色相。
- **照抄外部色板时，红与琥珀一律不能用**。实例：komi-store 的 `crimson #B3261E` 与我们的 `danger #AF352A` 距离仅 **19.6**；`sun #F4BE48` 与 `warn #E5B65C` 深色下仅 **26.2**。两者分别被换成 `copper` 与删除。

### 深色只有四级表面（是算术，不是偷懒）

`bg` L\*5.81 → `surface` L\*10.14，**跨度只有 4.33**。要在中间插一级且两侧 ΔL\* ≥ 2.5 需要 ≥5.0。
→ `surfaceInset` **不作为阶梯级**，降为「功能填充」（轨道/输入框底），只对 `surface` 校验 ΔL\* 2.49。
浅色则相反：`surfaceInset` 94.75 < `surfaceWarm` 96.22 < `bg` 98.67 < `surface` 100.00，跨度 5.25，靠「白卡 + 极淡投影 + 描边」补层级。

### 不跟 Komi 的一条

它的 `outline #C4C6CF` 对白底只有 **1.65:1**，不达 WCAG 1.4.11 对控件边界的 3:1。
我们不跟，控件描边 `border` 取 `#8A8D96`（3.32）。**装饰性分隔线才用低对比的 `borderSoft`。**

## 强调色的覆盖纪律

**强调色不碰底与面。** 只允许出现在四类地方：主操作填充 / 选中态 / 小徽章 / 焦点环。
首页上限 **3 处**。

分类图标圆底改为中性（`--cl-surfaceWarm`），**分类色只由图标自身的颜色承担** ——
那是内容，不是装饰。

## 金额排版：并排双容器 + 固定字号（2026-09-22 起，账本首页 Hero）

**当前实现**：支出与收入**并排两个容器**，**共用同一个固定字号**（`HeroMetrics.size` = `FSize.xl` 24sp）。
不再用字号表达主次。

### ★ 这是被用户否掉两轮后定下来的 —— 过程比结论更值得记

1. 第一轮："收入和支出的数字没按数字大小调整" —— 当时默认轨道是「总量守恒」，
   而它**只看收支比例、与金额绝对大小无关** → 我改了参数（换成「各自量程」）
2. 第二轮："还是太潦草，横向排列在两个容器里，字体大小也不变" → **整条字号轴被否掉**

> **同一个机制被连续两次要求调整时，该怀疑机制本身，而不是继续调它的参数。**
> 用户第一次说"数字越大字号越大"时，真正要的观感是"这两个数字的展示要合理" ——
> 而"255 元的支出比 10 万的收入还显眼"无论用哪个公式算都不合理。

### 从字号轴里只保留了一样：宽度反解兜底

`NumScale`（三档轨道 / 守恒分配 / 各自量程 / 行框锁死 / 字号过渡动画）**已整体移除**
（`Dimensions.kt` 净减 127 行）。`HeroMetrics` 只剩一个固定字号 + 一个 `fitScale()`：

- **两个金额共用同一个缩放系数** —— 各自缩会破对称（一个缩一个没缩，同一行里就不是"一套"）
- 系数留 0.1% 余量：反解出的字号要经过一次浮点取整
- **24sp 是按最窄容器反推的**：并排后每容器内容宽约 160dp，
  最长一档 `¥1,000,000.00` 折合 6.4 个全宽数字位 → `160 / 6.4 ≈ 25sp`。
  **百万级金额不需要缩放** —— 缩峰会破坏"字号固定"的观感，要尽量不触发

### 换任何版式都成立的两条

- 量文字自然宽度要用 `Range.getBoundingClientRect()`（Compose 用 `TextMeasurer`）——
  **块级元素的 `scrollWidth` 会撑满容器，量不出真实内容宽**（第一版就是这么量错的）
- 两个金额的**符号与颜色双写**（`−¥11,824.86` / `+¥16,334.00`）：
  颜色对色盲用户无效，**符号才是可靠的那一层**
- 仅「收支」金额带符号：**资产余额/笔数不带**（它不是收支），
  **变化量 `↑512.40` 不带**（已有箭头表方向，再加正负号是双重编码）

> 完整设计推理与复算留在 `design/UI-REDESIGN.md §3.9`（历史）与 §10.8（现行）。

## CSS 镜像里的一个静默陷阱：`rgb(var(--x) / a)` 是非法写法

`design/tokens.css` 是把令牌镜像给 Web/HTML 原型用的。它把通道存成**逗号形式**
（`--cl-accent-rgb: 59,91,219`），于是合成时**必须**用 `rgba(var(--x), a)`：

| 写法 | 展开结果 | 实测（Chromium） |
|---|---|---|
| `rgb(var(--x) / .24)` | `rgb(59,91,219 / .24)` | **非法 → 整条声明被丢弃，`box-shadow` 变成 `none`** |
| `rgba(var(--x), .24)` | `rgba(59,91,219, .24)` | 正常 |
| `rgb(59 91 219 / .24)` | 同上 | 正常（**空格**形式才支持 `/` 透明度） |

**危险在于它静默**：不报错、不警告，只是投影/焦点环**静静地不存在**。
2026-09-22 实测发现 `tokens.css` 里 **9 处全中**（`--el-raised` / `--el-accent` /
`--el-soft` / `--el-float` / `--focus-ring` / `--el-well` / `--el-wellInset`），已全部修正。
v1 废弃镜像 `design-tokens.css` 另有 6 处（已废弃，未动）。

> 排查手法：**任何"应该有投影/环"的元素，读一次 `getComputedStyle(el).boxShadow`**。
> 看到 `none` 先怀疑这条语法，而不是怀疑浏览器。

## 主题相关的字色：随「块」定，不随「主题」定

品牌色块的底色是**品牌资产**（微信绿 / 支付宝蓝 / 抖音黑），**不随主题变化** ——
所以它们上面的字色也必须**按各自底色**挑，而不是统一取一个 `var(--on-slice)`。

第一版踩的坑：把 `.pf` / `.av` 的字色统一做成 `var(--on-slice)`（浅色白、深色近黑），
结果**两个主题各有各的错**：浅色下白字压微信绿 `2.65:1`、深色下深字压抖音黑 `1.18:1`。

| 块 | 字色 | 对比度 |
|---|---|---|
| 微信 `#22B573` | 深字 | 7.07:1 |
| 支付宝 `#1677FF` | 深字 | 4.53:1 |
| 抖音 `#20232A` | 白字 | 15.73:1 |

另：抖音块（近黑）在深色页底（`#111316`）上几乎同亮度 → **深色下补一道发丝环**把它勾出来。

> 判据：**底色变不变，决定字色该怎么定。** 底随主题变 → 字色跟主题；
> 底不随主题变（品牌资产）→ 字色随块。混用必错。

## 软拟态：默认关闭，可选用

v4 默认**扁平**（与 Komi Classic 把装饰层关到 0 一致）。拟态降级为 `data-shape="soft"` 可选项。

| 令牌 | 作用 |
|---|---|
| `--cl-wellTop` / `--cl-wellBottom` | 圆底同色系**上下渐变**（浅 `#FFFFFF → #ECEEF3`；深 `#25272C → #191B1E`） |
| `--el-well` | **凸起** = 外投影 + 顶部内高光 |
| `--el-wellInset` | **凹陷** = 内投影。用于分段控件轨道、进度条槽、按压态 |

**价值在「凸起 ↔ 凹陷」的状态对比**，不是加渐变。只做渐变不做状态反转就只是"软萌"，不是拟态。
原型里有 `.catcircle`（凸起）+ `.catcircle.pressed`（凹陷）示例。

## 这个项目的令牌体系长什么样

```
design/tokens.json   ← 机器可读真源（被 contrast_check.py 校验）
design/tokens.css    ← 同上的 CSS 表述，每个色值只出现一次
        ↕ token_parity.py 双向对账（阶段二已交付）
app/src/main/java/com/cozyledger/app/ui/theme/Tokens.kt   ← Compose 侧
```

> 文件名**不带版本号**。原先叫 `tokens-v2.*` 而内容已是 v3，本身就是个坑（v4 时已改名）。
> ⚠️ **项目根目录还有一对 `design-tokens.{css,json}`** —— 那是 v1 时代的人工镜像，
> 版本停在 v1、零功能性引用，**自称"唯一真源"**。它正是 2026-09-11 那次
> 「设计真源三方冲突」的成因。**不要读它、不要改它。**
> 2026-09-22 已给它俩加醒目废弃标记（CSS 注释 / JSON `_deprecated` 字段）并登记进
> `UI-REDESIGN.md §11` 的 Q7，但**没有删除**（决定权归项目所有者）。

### Compose 侧（v4 结构，2026-09-22 落地）

- `Tokens.kt`
  - `PaletteColors` 接口 = **33 个角色**。取色唯一入口 `@Composable themeColor()`。
  - 结构是 **`NeutralColors`（不随强调色变）+ `AccentRoles`（4 角色）→ `TokenPalette` 组合**。
    拆开的目的是让「换强调色」只可能动那 4 个值。
  - `AccentPreset` 枚举：`cobalt`（默认）/ `copper` / `frost` / `mono`，× 浅/深 = 8 套。
    **8 个组合预建并缓存**，保证实例引用恒定。
  - `CategoryColor` 枚举：6 槽（`cat_sky` / `grass` / `olive` / `honey` / `clay` / `other`），
    **存库存 key 不存 hex**；`PaletteColors.categoryColor(key)` 容错解析，未知值回退 `OTHER`。
  - `action` / `onAction` / `focus` 是 **`PaletteColors` 的接口默认实现**（= accent 系）。
    **不要给它们写独立 override** —— 独立赋值会让「换强调色」时主 CTA 不跟着变。
    `token_parity.py` 会断言这一点。
  - 已删除的旧 API：`TokenColor` / `Dark`（两个单例对象）、`token(isDark){}`、`themeColors()`。
- `Theme.kt`
  - `CozyLedgerTheme(darkTheme, accent, content)` —— **`accent` 是参数**。
  - `colorScheme` **逐槽覆盖**，含 `surfaceContainer*` 全系列 + `surfaceBright/Dim` + `inverse*`。
  - 🔴 **`surfaceTint = Color.Transparent` 不能改**。M3 用它给 elevation 表面自动染 primary 色，
    改回默认值等于把「整体有个颜色」请回来。
  - `ThemeColors(isDark, palette)` 是 `LocalThemeColors` 的承载；值是 `remember(darkTheme, accent)` 缓存的。
- `Type.kt`（v4 新增）
  - `CozyTypography` 覆写 M3 全 15 槽（不覆写则 Dialog 标题 / TextField 输入文字落回 M3 基线）。
  - `CozyText` 13 档语义阶梯（`screenTitle` / `sectionLabel` / `rowTitle` / `rowSub` / `amountRow` …）。
  - 金额类样式统一 `fontFeatureSettings = "tnum"`；全局 `includeFontPadding = false`。
- `Dimensions.kt`
  - `Space` / `Radius` / `FSize` / `FWeight` / `IconSize` / `Opacity` / `StrokeWidth`
  - `Leading` / `Tracking` / `Motion`（v4 新增；`Motion` 是从 `Elevation` 拆出来的）
  - `Chart` / `Segmented` / `Sheet` / `TxRow` / `Elevation`
  - **`NumScale`**（金额字号轴，见下）
- `MsIcon.kt`：用连字（ligature）把**图标名当文字渲染**，字体是 `res/font/material_symbols_rounded.ttf`。

### 🔴 `FSize` 在 v4 被整表重命名（读旧代码/旧文档前必看）

**这是本项目最容易读错尺寸的地方。** 重排是为了对齐 CSS 的 `--text-*`，**像素等价**：

| 语义 | v1 名 | v4 名 |
|---|---|---|
| 12 | `xs` | `xs` |
| 14 | `sm` | `sm` |
| 16 | `md` | `md` |
| 18 | `lg` → | **`heroSub`**（按用途命名：Hero 副数字 / 抽屉标题） |
| 20 | `xl` → | **`lg`** |
| 24 | `x2` → | **`xl`** |
| 32 | `x3` → | **`x2`** |
| 40 | `x4` → | **`x3`** |
| 48 | `x5` → | **`x4`** |

→ 看到旧文档写 `FSize.x5 = 48` 要换算成 `FSize.x4`；
看到旧代码 `FSize.lg`（想表达 18）现在是 **20**，正确写法是 `FSize.heroSub`。
**批量改名必须用单次正则映射**，不能顺序 replace —— `lg→heroSub` 与 `xl→lg` 会互相踩。

## 改色值后的强制流程

```bash
python tools/contrast_check.py     # CSS ↔ JSON 对比度与一致性，退出码 0
python tools/token_parity.py       # Tokens.kt ↔ tokens.json 逐值对账（84 项）
python tools/ui_token_lint.py      # 是否绕过令牌（裸 hex / 裸 hex 字符串 / 越界 dp / 直用浅色单例）
python tools/unused_import.py      # 未使用 import（Kotlin 编译器不报此项）
```
四个都必须退出码 0（`./gradlew check` 连带跑 `tokenLint` + `importLint`）。
改色值只需要动 `tokens.json` + `tokens.css` + `Tokens.kt` 三处，
**`token_parity.py` 会告诉你有没有漏改**。

它检查 7 件事，任何一项不过就是**真失败**：

1. 文本角色 ≥4.5:1（对 `surface` **和** `bg` 都要 —— 底不是纯白时必须双向验算）
2. 图形角色 ≥3.0:1
3. 深色表面阶梯单调递亮且相邻 ΔL* ≥2.5
4. 全部色值（含图表色组、分类色板、**强调色预设**）无紫粉系（hue 255–350 且 sat >0.20）
5. 图表分片两两距离 ≥30
6. **强调色跨组校验**：`onPrimary:primary` / `primary:bg` / `onPrimaryContainer:primaryContainer` 均 ≥4.5，且与 5 个状态色距离 ≥28，组内两两 ≥50（浅）/ ≥45（深）
7. **色板 vs 语义色/强调色** 距离 ≥28

> 第 6、7 条是 v4 新增，**都是实际踩到的坑**：单看每个预设/每个色板内部都自洽，
> 但跨组会撞（crimson = 19.6、cat_green = 13.1）。**配色校验不能只验组内。**

脚本依赖 JSON 里的元数据，加新角色时**必须同时给 `target`（`text`/`graphic`/`none`）和 `refs`**，否则该角色会被静默跳过不校验。

## 用数值方法调色时踩过的坑

这套令牌是用"求解 + 验证"的方式定的（不是凭感觉挑色）。踩过的坑：

1. **求解函数方向写反**（**同一个 bug 我犯过两次**）：`darkest()` 从纯黑起扫 → 黑色对任何浅底恒过 → 全返回 `#000000`。
   规则：**浅底上的文字用「从最浅端向下扫，取第一个达标值」（= 改动最小的色）；深底上的文字用「从最暗端向上扫」。**
   写这类求解器时，起扫端点必须按目标明暗方向选。
2. **HLS 索引取错**：`colorsys.rgb_to_hls()` 返回 `(h, l, s)`，索引 `[2]` 是**饱和度**不是明度。取错会把颜色全部变灰。
3. **用 RGB 距离当唯一目标函数会产出违背设计语言的解**（**已三次踩到**）：优化器会给出霓虹绿 `#209E1C`、亮青，甚至 `#6864D2` —— 后者视觉上就是淡紫，但 HSL hue 242 恰好绕过了「禁紫粉」的 255–350 区间，**机器检查抓不到**。
   → **必须先固定色相族与饱和度区间，只让明度/明度差做优化变量**；且最终值必须**人工过目**，不能只信校验器。
4. **明度带是可辨性的真正杠杆**：同族色降饱和度后 L\* 会全部挤在一起（实测 53–57），距离崩到 19.5。拉开明度交错才能同时保住低饱和与可辨性。
5. **对比度约束会压缩可用明度带**：深色模式要求"对深色面 ≥N:1"，逼色值偏亮，可用 L\* 区间收窄。**提高 N 会直接减少可用的色阶数量** —— 图形角色用 WCAG 标准的 3.0，不要自己加码到 4.0（我加过，结果色板从 7 色被迫降到 6 色）。
6. **Python 变量遮蔽**：把 `min((dist(a, b), name_a, name_b) for i, j in ...)` 写成 `dist(a, b)` —— 其中的 `a`/`b` 是**上一个循环遗留的变量**（比如字符串 `'frost'`），不是当前循环的色值。
   → 用 `min(list_of_tuples, key=lambda t: t[0])` 替代元组直接比较，既避免遮蔽也避免二次比较。


## 硬规则（改任何东西前先读）

1. 文本 ≥4.5:1、图形 ≥3.0:1。
2. 禁紫粉系（`#7C3AED` / `#A855F7` / `#EC4899` 及任何紫色）。**注意 HSL hue 235–350 都算可疑，不只是 255–350** —— 优化器产出的 `#6864D2` 就落在 242。
3. 透明度只用六阶 `.05/.1/.2/.4/.6/.8`。阴影着色 alpha 属深度系统，不受限。
4. 间距只用 4px 网格 `4/8/12/16/20/24/32/40/48/64/80`。裸的 3/18/22/34/44/52 非法。
5. **`accent` = 强调色本体**（填充 + 选中态 + 可读强调，4 组预设全部同时满足填充与文本的对比度）。`accentOn` 是它上面的前景，`accentSoft` / `accentStrong` 是它的 tonal 底/字。
   ⚠ v4 起 `accentStrong` 的语义是「**强调底上的文字**」，**不再**用于普通强调文本 —— 用 `accent`。
6. **`meta` 是图形角色，禁止用于正文**。文字只有 `fg`/`fg2`/`muted` 三级。
7. **金额色与状态色不可互替，且必须靠明度真正切开**：`income` vs `danger` ΔL\* ≥ 8；`expense` vs `success` ΔL\* ≥ 6。（v1 曾是 2.4° 色相差 / 完全同值，是原始缺陷。）
8. 禁 emoji。图标一律 Material Symbols。
9. **图表分片色取分类自己的色板色，不按排名序号分配**。
10. 深色用「明度阶梯 + 1px 描边」分层；浅色用「白卡 + 阴影 + 描边」分层（浅色 bg→surface 只有 ΔL\* 4.33–5.25，塞不下五层）。
11. **底色与面色不带颜色**（Lab 色度 ≤2.2）。自检法：**把截图饱和度拉到 0，如果层级塌了，说明颜色在承担本该由字体/间距/描边承担的层级。**
12. **强调色不碰底与面**，只出现在：主操作填充 / 选中态 / 小徽章 / 焦点环。首页上限 3 处。
12b. **动态排版要由算术保证不变量，不能靠事后兜底** —— 总量守恒 + 行框锁死 + 宽度反解，三件事缺一不可（见「金额字号轴」章节）。
    **引用外部色板（如 komi-store）前先算「色相预算」**：语义色占掉的红与琥珀，强调色和分类色都不能再用。

## 图标：校验与重建

```bash
# 必须用隔离环境（fontTools 装在这里，不污染全局）
C:/Users/10355/.workbuddy/binaries/python/envs/default/Scripts/python.exe tools/build_icon_sprite.py
```

- `--check` 只校验不重建。
- 它会**校验代码里的图标名在字体中是否真实存在** —— `MsIcon` 靠连字渲染，名字写错**不会编译报错**，只会静默渲染成字面文字（页面上出现 "person_outline" 这样的单词）。
- 往 `ICON_NAMES` 里加名字即可纳入 sprite。

### 解析这个字体时踩过的坑（脚本注释里也有，改脚本前必读）

1. **字体是可变字体**（FILL/GRAD/opsz/wght 四轴），`unitsPerEm = 960`。
2. **连字藏在 Extension 子表里**：`GSUB.LookupList.Lookup[i].LookupType == 7`，必须展开 `sub.ExtSubTable` 才读得到 `ligatures`。不展开会误判「字体没有连字」。
3. **fontTools 的 `LigatureSubst.ligatures` 以【首字形】为 key**，`Ligature.Component` 是**其余字形**，真实序列 = `[first] + Component`。顺序写反会全部匹配失败。
4. **下划线的字形名叫 `underscore`，不是字符 `_`**。拼字符串必须经 cmap 反查真实字符。
5. **字母与 PUA 图标分属不同 cmap 子表**，`getBestCmap()` 只返回一个，必须合并全部子表。
6. **同一字形同时被大写与小写码点映射**（`0x41` 与 `0x61` 都指向字形 `a`）。若"取最小码点"会得到大写，拼出 `PERSON_OUTLINE` 与真实小写键对不上 → 误报图标缺失。**必须优先取 ASCII 小写**。
7. **`font.getGlyphSet()` 会读 `gvar` 表而抛 `TTLibError`** —— 因为该文件的 `gvar` 是截断的（见下）。改为直接遍历 `font["glyf"]`：`SVGPathPen(glyf)` + `glyf[name].draw(pen, glyf)`。

## 已知问题：字体文件是残缺的

`res/font/material_symbols_rounded.ttf` 的 sfnt 表目录声明总长 **15,079,786** 字节，文件实际只有 **5,441,280** 字节；`gvar` 缺约 9.6MB（72%），推测是不完整下载。

- 图标**能正常显示**（`glyf` 静态轮廓完整，实测 95/95 图标名可用）。
- **可变轴全部失效**：`MsIcon.kt` 的 `FontVariation.Settings(weight(400), GRAD 0, opsz 24)` 是空操作。
- 今天没问题纯属巧合 —— 请求值恰好等于字体默认轴值。
- **隐患**：写 `FontVariation.weight(600)` 或 `Setting("FILL", 1f)` 会**静默无效**。
- 处置：重新下载完整 Rounded 可变字体（13–15MB），或改静态单实例字体 + 去掉 `MsIcon.kt` 里的 `FontVariation`。

## 护栏脚本（现状，2026-09-22 Stage 6 完成）

| 脚本 | 作用 | 状态 |
|---|---|---|
| `tools/contrast_check.py` | CSS ↔ JSON：对比度、深色阶梯、禁紫粉、分片可辨、强调色跨组、**别名断言** | ✅ 全绿 |
| `tools/token_parity.py` | **Tokens.kt ↔ tokens.json 逐值对账**（84 项）+ 覆盖率兜底 + 派生角色断言 | ✅ 全绿 |
| `tools/ui_token_lint.py` | 6 规则（bare-hex / **bare-hex-string** / named-color / literal-dp / literal-sp / pale-palette），**扫描范围分两档** | ✅ 零违规，**无任何容忍额度**（`token_lint_baseline.txt` 已删除）|
| `tools/unused_import.py` | **未使用 import**（Kotlin 编译器不报此项，只有 IDE inspection 会标灰）| ✅ 零违规（首次跑清掉 17 处 / 14 文件）|
| `tools/build_icon_sprite.py` | 图标 sprite 生成 + **图标名真实性校验**（含代码侧真实用法）| ✅ 96/96 + 46 项 |

`./gradlew check` 依赖 `tokenLint` + `importLint`（两者共用 `registerPythonCheck`；
无 Python 时**跳过并提示**而非失败 —— 否则没装 Python 的同事会完全无法构建）。

### ★ 护栏的「作用域」与「规则」同等重要

`bare-hex-string` 规则刚写完时**一条都抓不到** —— `ui_token_lint.py` 原先只扫 `ui/` 目录，
而裸 hex 字符串的典型违规现场（`MainActivity.kt` 的种子分类色、data 层的字段默认值）
**本就在 `ui/` 之外**。把范围扩到整个 app 包后，规则一次抓出 **9 处**，一处不漏。

> **一条永不会命中的规则，与没有这条规则在效果上等价，但它会给人"已经防住了"的错觉 ——
> 这比没有更危险。**

→ **写完任何静态检查，先确认它至少命中一个真实违规。** 命中数为 0 时先怀疑范围/正则，
  而不是庆祝"代码很干净"。

（注：`design/tokens.json` 里的 `_order_constraint` 早写明「先加规则再改数据」——
顺序是对的，但**作用域是那条约束没覆盖到的盲区**。）

### `unused_import.py` 的三个要点

1. **约定函数必须豁免**：`getValue` / `setValue` / `provideDelegate` 的名字**根本不出现在源码里**
   （`val x by ...` 编译后需要 `getValue`），删了直接编不过。**豁免表宁窄不宽** ——
   加宽会掩盖真问题，漏掉的假阳性下次运行还会再报一遍。
2. **块注释要状态机**：KDoc 是多行 `/** */`，逐行判 `startswith("//")` 判不出来；
   而 `[Foo]` 这类 KDoc 引用**不构成编译期使用**，不排除就会漏报。
3. **只报告、不自动修**：删除判定是「名字没出现」的静态近似，`by` / 反射 / KDoc 都可能让它翻车。
   让工具报、人来看，比让工具改便宜（编不过还算走运）。

**验证方法**：批量删除后**用编译器交叉验证** —— 编译通过即证明没误删隐式使用的 import。
⚠️ **测试用例要选对**：用 `import ...layout.width` 测不会报 —— `Modifier.width(...)` 真的在用
这个扩展函数，脚本判「已使用」是**正确**的；换 `aspectRatio` 才验证成功。
**用例选错会让人误以为工具坏了。**

### 种子分类色：写 key，不写 hex

`MainActivity.seedDemoCategories()` 的 9 个分类色曾是 hex（含 v1 珊瑚 `#E2734F` 与设计禁用的紫
`#9B59B6`），已改为 `CategoryColor` 枚举 + `.key` 落库。

**刻意不沿用「v1 hex 再靠吸附收敛」**：紫(购物) / 其他支出 / 其他收入会**同时吸附到石板灰**，
三个分类一个颜色，用户分不出哪个是哪个。改为按语义分配：**支出侧 5 个有色槽各用一次**，
「其他」类落中性槽。

用枚举而非字符串的另一个理由：**key 拼错会编译报错；hex 写错只会静默变成石板灰**
（无报错、无日志，只有用户觉得"颜色怎么怪怪的"）。

> ⚠️ 种子逻辑有 `if (list.isNotEmpty()) return` 守卫，**已有数据的设备不会重跑** ——
> 改种子色在开发者的旧装机上看不到效果，别误判成"改了没用"。

### 文档里的"第三方副本"要删掉，而不是更新

`Spec.md §8` 曾内联一整份色值表，它**落后实现两次**（v2/v3 转天空蓝青、v4 转中性底）——
那张表就是 v1「三方真源分叉」的成因。已改为**不再内联任何色值**，只留口径描述 + 真源位置 + 校验工具。

> **复制品一定会漂移。与其每次同步复制品，不如消灭复制品。**

（计划里的验收标准「`grep #E2734F` = 0」表述不准确：该色仍应出现在
`tokens.json` 的 `legacy_hash_map`、`Tokens.kt` 兼容实现的注释、历史记录文档里。
准确说法是**"不再有任何文档把它当作现行口径"**。）

### 写校验器时的两条经验（都是踩出来的）

1. **静默跳过比报错更危险。** `decls()` 原本有一行 `if v.startswith("var("): continue`，
   把别名声明悄悄丢掉了 —— 于是新加的别名校验永远报「缺失」。同理 `contrast_check.py` 早先
   按 JSON 里的 `target`/`refs` 元数据决定是否校验，**漏填元数据的角色就被静默放过**。
   → 正确做法：**覆盖率兜底**（每个角色必须被恰好校验一次，缺口显式报出），见 `token_parity.py` 第 5 节。
2. **新加的校验必须做反向测试。** 故意把 `--cl-action` 改成硬编码 hex、把某个色值改错 1 位，
   确认校验器真的抓得住 —— 否则你不知道它是「通过」还是「根本没跑」。

## 原型

`design/prototype/index.html`，`file://` 双击即开，无 CDN 无构建。支持深链接：

```
index.html#page=categories&theme=dark&accent=mono&shape=soft&grid=0&tokens=0
```

| 参数 | 取值 |
|---|---|
| `page` | `home record report categories pending summary profile settings goal couple onboarding autodrawer` |
| `theme` | `light` / `dark` / `both`（并排对比） |
| `accent` | `cobalt` / `copper` / `frost` / `mono` |
| `shape` | `flat`（默认）/ `soft`（软拟态） |
| `period` | `month` / `year` / `all`（驱动 Hero 金额，进而驱动字号） |
| `num` | `off` / `share`（默认，总量守恒）/ `role` |
| `save` | `idle` / `done` / `failed` |
| `grid` / `tokens` / `offline` | `0` / `1` |

无头验证渲染是否正常（改了原型后建议跑一遍）：

```bash
CHROME="/c/Program Files/Google/Chrome/Application/chrome.exe"
"$CHROME" --headless=new --disable-gpu --no-sandbox --virtual-time-budget=4000 \
  --dump-dom "file:///E:/14_myProject/shalajizhang/design/prototype/index.html#page=home" \
  > /tmp/dom.html
# 检查没出现 undefined、没残留 ${模板}、<use href="#i- 数量正常
```

**批量回归**（4 个强调色 × 12 屏，验证零 `undefined`）：

```bash
for acc in cobalt copper frost mono; do
  for p in home record report categories pending summary profile settings goal couple onboarding autodrawer; do
    "$CHROME" --headless=new --disable-gpu --no-sandbox --virtual-time-budget=2500 \
      --dump-dom "file:///E:/14_myProject/shalajizhang/design/prototype/index.html#page=$p&theme=both&accent=$acc" \
      2>/dev/null | grep -c 'undefined\|\[object'
  done
done
```

注意：Chrome 的 `--screenshot=` 用**相对路径会写到 Chrome 自己的工作目录**，必须给绝对路径。

**改原型时的两个易漏点**：

- 内联 `style="background:var(--cl-accentSoft)"` 会**覆盖**组件的默认中性底。改组件 CSS 时务必同时清掉内联覆盖，否则"改了没生效"。
- 深色下漏白的常见来源：CSS 里硬编码 `#FFF` 的类（如 `.note`）。**凡是会出现在设备内部的类都必须走令牌。** 用脚本扫 `<style>` 区的 `#[0-9A-Fa-f]{3,8}` 可以一次找全。

## 验证降级阶梯（本项目 assembleDebug 常因内存失败）

曾因 JVM 提交量耗尽反复报 `errno 1455 页面文件太小`，属系统资源问题非代码问题：

| 级 | 命令 | 说明 |
|---|---|---|
| L1 | `contrast_check.py` + `token_parity.py` + `ui_token_lint.py` | 零 JVM，秒级 |
| **L2（主力）** | `./gradlew compileDebugKotlin --offline` | 约 20–30 秒 |
| L3 | 见下「出包命令」 | 约 1.5 分钟 |
| L4 | `adb install -r` + 冷启动 + 抓崩溃/Worker 日志 | 需要设备 |

**出包命令（2026-09-22 实测稳定通过）**：
```bash
./gradlew assembleDebug --offline --no-build-cache --no-daemon \
  -Dorg.gradle.jvmargs="-Xmx6144m -XX:MaxMetaspaceSize=1024m -Dfile.encoding=UTF-8" \
  -Dkotlin.compiler.execution.strategy=in-process \
  -Dorg.gradle.workers.max=2
```

🔴 **纪律：不要连续只跑 L2 就收工。** 反复只跑 `compileDebugKotlin` 会把增量状态切碎，
之后 `assembleDebug` 编出的包**启动即崩**（`NoSuchMethodError: -$$Nest$fget...`，Hilt/Dagger 的
dex 合成访问器新旧混装）。每个批次结束必须出一次完整包，改变量/依赖结构时加 `clean`。
**APK 体积是哨兵：干净构建 47–50MB，明显偏大就是增量脏了。** 详见 `docs/perf-refactor.md §9.5.2`。

## 批量改代码的注意事项

本项目有过**「脚本回报成功但未落盘」**的记录（`themeColor(). bg ` 这类点号前带空格的自动化重构残留遍布 13 个文件 90+ 处）。批量替换后**必须每文件重读校验**，不能只信脚本输出。

### 三个 Kotlin 侧踩过的坑（2026-09-22）

1. **变量遮蔽**：`fun resolve(dark: Boolean): Color = if (dark) dark else light` —— 参数 `dark`
   把枚举自身的 `dark: Color` 属性遮住了，返回类型被推断成 `Any`。参数改名 `darkTheme` 即解。
   **在枚举/类里给函数参数起与成员同名的名字，是静默类型错误的高发区。**
2. **`private constructor` 是「类作用域」不是「文件作用域」** —— 同文件的顶层函数
   （如 `paletteOf()`）访问不到，报 `it is private in 'X'`。要「本模块可见」得用 `internal`。
3. **用正则批量改枚举名/令牌名时，`` 边界要留神** ——
   `FSize.(lg|xl|x2|x3|x4|x5)` 在改名后**依然会匹配新名字**（因为新集合里也有 lg/xl/x2…），
   所以「改完再 grep 旧名字检查」这种验证方式是无效的。**正确做法是用 git diff 抽查真实改动行。**
