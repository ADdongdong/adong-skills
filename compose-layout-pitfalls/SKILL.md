---
name: compose-layout-pitfalls
description: 诊断并修复 Jetpack Compose 布局与渲染的视觉缺陷——文字/图标被容器裁切、抽屉或卡片高度失控、内容被遮挡、单行元素过密、底部/顶部多出一条空白带（insets 重复避让）、悬浮按钮「像单独占了一行」、切换选中态时滑块「闪没」、叠放布局中「按钮从背后透出来」、位移元素「看得见却点不到」。适用于任何 Compose 项目。当用户说「字被挡住了」「按钮文字显示不全」「占空间太大」「布局怪怪的」「空了一大块」「底部莫名多一条白边」「加号像单独占了一行」「切换的时候白块消失一下」「删除按钮不该露出来」「点上去没反应」时使用。
agent_created: true
---

# Compose 布局陷阱：编译能过、装机才现形

## 铁律：布局几何的问题，只有真机能发现

编译、单元测试、设计令牌护栏（查颜色/间距常量）**都拦不住**"文字被容器裁掉"：

- 编译当然过（语法没错）
- 令牌护栏查的是"有没有写裸 dp"，**不查这个 dp 值合不合理**
- 出包只证明能构建

**本项目实例**：一整套按钮组件（`PrimaryButton` / `SecondaryButton` / `GhostButton`）写完，
编译 + 4 项护栏 + `assembleDebug` 全绿，**到用户装机才发现"字和图标被遮挡"** ——
拖了整整一轮，而它影响 6 个页面。同一项目里「空态占位 160dp 把有效内容推出屏幕」
也是装机才看到的。

→ **凡改动涉及高度 / 内边距 / 对齐，出包后必须装机看一眼。**
  这条不是"最好做"，是"不做就会返工"。

## 陷阱清单（按实际命中率排序）

### 1. 固定高度 + 过大内边距 = 内容被裁 ⭐ 最高频

```kotlin
// ❌ 48 − 16×2 = 16dp 才是留给内容的；图标 20dp、文字行高 19.2dp 都超过它
modifier = modifier.height(48.dp),
contentPadding = PaddingValues(horizontal = 24.dp, vertical = 16.dp)

// ✅ 两道保险
modifier = modifier.heightIn(min = 48.dp),           // 只保最小值，内容高时允许长高
contentPadding = PaddingValues(horizontal = 24.dp, vertical = 8.dp)
```

**判断式**：`容器高度 − 上下内边距 ≥ max(图标尺寸, 文字行高)`

**为什么用 `heightIn` 而不是 `height`**：`height` 是硬约束。用户把系统字号调大、
或将来改字号/加图标，会**再次**裁切。`heightIn(min=)` 只保证触控目标达标，其余交给内容。

**同类**：`Modifier.size(32.dp)` 里放单个 20dp 图标 ✓ 安全；放两行文字 ✗ 裁切。

### 2. `fillMaxHeight` 是「钉死」不是「上限」

```kotlin
// ❌ 强制占满 92% 屏高 —— 内容少时下方一片空白，CTA 被推到拇指够不到的地方
Modifier.fillMaxHeight(0.92f)

// ✅ 上限约束
val max = (LocalConfiguration.current.screenHeightDp * 0.92f).dp
Modifier.heightIn(max = max)

// 并且内容区必须配：
Modifier.weight(1f, fill = false)      // ← fill = false 是关键
```

**`weight(1f)` 的 `fill` 默认是 `true`** —— 它会**占满**分配到的空间，即使内容只有一半。
想让"内容少时收缩、内容多时才滚动"，必须显式传 `fill = false`。**这是最容易漏的一处。**

### 3. `includeFontPadding = false` + 紧行高 = 文字上下被切

设计系统为了让行框紧凑，常设 `includeFontPadding = false`（去掉字体自带的额外 padding）。
此时**行框高度完全由 `lineHeight` 决定**：

- 16sp 中文字，字体自带 ascent+descent 常达 1.16~1.3 em ≈ 18.6~20.8sp
- 若 `lineHeight` 系数取 1.2（= 19.2sp），**刚好临界甚至不够** → 上下裁切

**检查**：`includeFontPadding = false` 的项目里，`lineHeight` 系数**不要低于 1.2**，
且按钮/标签这类紧凑容器要用 `heightIn` 兜底、别指望恰好贴住。

### 4. 单行常驻操作点 ≤ 3（360dp 宽）

六个元素塞进一行 → 名称只剩约 31px，被压成"餐…、交…、购…"。
**这是信息架构问题，不是样式没调好。** 解法：

- 常驻操作点压到 1~2 个，其余进 `more_vert` 溢出菜单
- 次要信息与主标题**分行**，把宽度还给主信息

### 5. 空态占位别按「最大尺寸」预留

图表/列表区域的空态若用满尺寸占位（如 160dp），会把下面**真正有内容**的区块推出屏幕 ——
新用户首屏看到的基本全是空白，必须先滚动才有信息。

空态只需要"放下一行提示 + 一个图标"的高度（约 80dp）。

### 6. 组件自带 window insets 时，外面再包一层 = 双重避让 ⭐ 最易误判

Material3 的 `Scaffold` / `NavigationBar` / `TopAppBar` / `BottomAppBar` / `ModalBottomSheet`
**默认已经消费 window insets**：

```kotlin
// M3 NavigationBar 的默认值（1.2.0 起）
NavigationBarDefaults.windowInsets
    = WindowInsets.systemBarsForVisualComponents.only(Horizontal + Bottom)
```

所以外面再包 `Modifier.navigationBarsPadding()` / `statusBarsPadding()` 就是**避让两次**，
凭空多出一条与系统栏等高的空白带。

**判断方法：拿实际 bounds 对比组件的规范高度。**

```bash
adb shell uiautomator dump /sdcard/ui.xml && adb pull /sdcard/ui.xml
# 节点的 bounds ÷ 屏幕密度 = dp；再和下方规范值比
```

| 实测容器高 | 结论 |
|---|---|
| **恰好等于**规范值 | insets 已被消费 → **不要再加** |
| **大于**规范值 | 已经叠加了 → 去掉多余那层 |
| **小于**规范值 | 内容可能被压 → 查 `consumeWindowInsets` 是否用错 |

M3 常见规范高度：`NavigationBar` **80dp**、`TopAppBar`(small) 64dp、`BottomAppBar` 80dp。

**这个陷阱的变体**：设计文档/交接说明写着「这里少了 padding，**是缺陷**」——
那条结论是**写下那一刻**的判断，会随依赖版本升级而失效。
执行前用「版本行为（解包 aar 看默认值）+ 实测 bounds」复核一遍，
成本两分钟；照做错了要返工一整轮。

（本项目实例：计划要求给 `NavigationBar` 补 `navigationBarsPadding()`，
解包 material3-1.3.0 确认默认已含，实测容器高恰好 80dp —— 判定计划有误，改为**不改**。）

### 7. 给「悬浮元素」让位的留白：必须在 `contentPadding`，不能在 `Modifier.padding` ⭐

同样是留 80dp，放的位置决定了视觉上是「FAB 悬浮在数据之上」还是「FAB 单独占了一行」：

```kotlin
// ❌ 缩小了列表视口 → 那 80dp 变成一条【内容之外】的空白带，FAB 浮在带子里
modifier = Modifier.fillMaxSize().padding(bottom = navBarHeight + Fab.clearance)

// ✅ 视口延伸到底，只是内容末尾多 80dp 滚动余量 → 数据能滚到 FAB 后面
modifier = Modifier.fillMaxSize().padding(bottom = navBarHeight)
contentPadding = PaddingValues(bottom = Fab.clearance)
```

**本项目实例**（用户反馈"加号像单独占了一行"）：dump UI 树取到
列表内容结束于 `y≈2190`、FAB 在 `y=[2214,2382]`、导航栏 `y=[2430,2670]` ——
2190→2430 正好是一条 240px(=80dp) 的空白带，**FAB 就浮在带子里**。

**判断口径**：
- 留白是「内容的一部分」（多滚一截就到）→ `contentPadding`
- 留白是「视口让位」（永远不该出现内容）→ `Modifier.padding`

悬浮元素（FAB / 悬浮按钮 / 吸底条）属于**前者**：用户预期"数据从它底下穿过去"。

> 与陷阱 6（双重 insets 避让）是同一类问题：**都是"留白放错位置/放错层"**。
> 遇到"某个元素看起来占了一行""底部莫名一条空白"，先 dump 坐标算一下那条空白归谁。

### 8. 「移动中的元素 + 阴影」会在动画里闪没 ⭐

**症状**：切换选中态时，滑块 / 拇指「消失一瞬间再出现」——

**这不是动画问题**（已用逐帧日志证实动画值完全平滑，见下条）。
根因是 `Modifier.shadow` 会为该元素**建一个 graphics layer 来画投影**，
元素位置每帧变化时 layer 要跟着重定位，这条路径上容易掉帧或闪白。

```kotlin
// ❌ 移动中的元素带阴影
Modifier.offset(x = animatedOffset).shadow(2.dp, shape).background(surface)

// ✅ 平面 + 发丝描边（明度差 + 边界已足够表达"浮起"）
Modifier.offset(x = animatedOffset).clip(shape).background(surface)
    .border(hairline, borderSoft, shape)
```

**判据（不用试）**：`grep '\.shadow('` —— **出现在动画里的那一处就是它**。
静态元素（卡片 / 按钮）的阴影没问题。

**本项目实例**：全项目只有 2 处 `Modifier.shadow` —— 一处静态卡片（无风险），
一处是分段控件在 `animateDpAsState` 位移中的拇指，用户报的"切换时白块闪没"正是它。
Material3 自己的 `SegmentedButton` 也不用投影。

### 9. 用「逐帧日志」一刀切开逻辑问题与渲染问题 ⭐

**前提**：不能模拟点击时（国产 ROM 会拦 `adb shell input tap`，
报 `INJECT_EVENTS permission`），**让 App 自己触发** —— 在 VM 的 `init` 里定时驱动状态变化，
比等用户手动操作可靠得多，也不打扰用户：

```kotlin
// TEMP-DEBUG ★用完必须删，用统一标记便于 grep 确认清干净★
init {
    viewModelScope.launch {
        delay(1_500); openRecord()                     // 自动打开抽屉
        repeat(8) { setType(toggle()); delay(1_500) }  // 自动来回切换
    }
}
```

再在可疑组件里**每帧打一行**状态日志：

```kotlin
android.util.Log.e("SegThumb", "maxW=$maxWidth seg=$segmentWidth idx=$idx off=$offset")
```

**判读**：

| 日志表现 | 结论 |
|---|---|
| `off` 有完整中间值（`0.39 → 1.71 → 4.13 → …`）| **动画逻辑没问题** → 去查渲染 |
| `off` 直接跳变（无中间值）| 动画没跑：state 被重建 / duration 为 0 |
| `seg` 为 0 | 宽度约束异常，元素被压成不可见的线 |

> **先切开"逻辑 or 渲染"，再动手改**，否则会在正确的地方改来改去。

### 10. ⚠️ 探针本身也会「看起来在跑、其实没跑」⭐

**下结论之前，必须先确认探针真的生效了**（dump / 截图看状态变没变），否则会得出
"功能没生效"的错误结论，然后去改一个本来正确的实现。

两次真实失败：

```kotlin
// ✗ 以「频繁重发的状态」为 key —— 列表在启动阶段重发几次，delay 就被重启几次
LaunchedEffect(recent) { delay(3_000); revealedTxId = recent.first().id }

// ✗ 固定延迟 + effect 只跑一次 —— 到点时数据还没加载完，firstOrNull() 为 null 且不再重试
LaunchedEffect(Unit) { delay(4_000); revealedTxId = flow.value.firstOrNull()?.id }

// ✓ 轮询：不赌延迟，等到就退出
LaunchedEffect(Unit) {
    repeat(25) {
        delay(1_000)
        flow.value.firstOrNull()?.let { revealedTxId = it.id; return@LaunchedEffect }
    }
}
```

**排查同类问题的捷径：找「只有它这样」的那个元素。**
把全项目的 `Modifier.shadow` / 动画用法 grep 出来逐条比对 ——
**唯一同时命中两个条件的那个，天然是头号嫌疑。**

### 11. 「在上层」≠「看不见」：只有不透明才遮得住 ⭐

做「左滑露出按钮」「悬浮层」「遮罩」这类**叠放**布局时最容易踩。

把操作按钮铺在内容层**下面**、指望"内容在上面自然盖住它"——**不成立**。
z 序只在两者都绘制时决定谁盖谁；内容层若是**透明背景**（纯文本行、无底色的 `Column`），
按钮会**直接从背后透出来**。

真机表现：账本每一行的右侧都挂着一个"删除"，金额与它叠在一起 ——
静态看图会以为"按钮位置错了"，其实是"没被遮住"。

```kotlin
Box {                                   // 容器
    Box(Modifier.matchParentSize()) { 删除按钮 }   // 底层
    Box(Modifier.fillMaxWidth().background(c.bg)) { 内容 }  // 上层：必须有实底
}
```

**修法要点：由容器统一给内容层铺底，不要指望每个调用方记得自己画底** ——
"约定式正确"迟早被下一个调用方破坏。

#### 孪生坑：越界内容默认不裁剪

内容位移后左端跑到父容器外，而 Compose 的 `Box` **默认不裁剪**越界子元素 ——
文字会画到列表的内边距上（像"错位"）。叠放布局的外层记得加 `Modifier.clipToBounds()`。

### 12. 修饰符链顺序决定「谁跟着谁走」⭐

`Modifier.a().b()` 中 **a 在 b 的外层**。而 `background` / `border` / `shadow`
绘制在**自己所属节点的 bounds** 上 —— 它们排在哪一层，决定了会不会跟着内部位移一起动。

```kotlin
// 滑动揭示行的正确顺序
Modifier
    .fillMaxWidth()
    .offset { IntOffset(offset.roundToInt(), 0) }  // 外层：先偏移
    .background(c.bg)                              // 内层：实底跟着一起平移
    .draggable(...)                                // 最内层：手势命中区也跟随
```

| 顺序写错 | 后果 |
|---|---|
| `background` 在 `offset` **之前**（外层）| 实底不随内容平移 → 一直盖在原处 → 滑开时按钮永远露不出来 |
| `draggable` 在 `offset` **之前**（外层）| 手势命中区停在原位 → 视觉上滑开了、**实际点不到按钮** |

**位移一律用 `offset`，不要用 `graphicsLayer.translationX`**：后者只改绘制图层，
命中测试与无障碍坐标都留在原地，是同一类问题的另一种成因。

## 排查手法

```bash
# 找"固定高度容器"（排除 Spacer —— 纯间距不会裁内容）
grep -rn "\.height(Space\.\|\.height([0-9]" --include=*.kt | grep -v "Spacer"

# 看行高与字体 padding 设置
grep -rn "includeFontPadding\|lineHeight\|Leading\." --include=*.kt

# 找多余的 insets 避让（M3 组件多已自带，只有自定义布局才真的需要）
grep -rn "navigationBarsPadding\|statusBarsPadding\|windowInsetsPadding" --include=*.kt

# 叠放布局：谁有实底？（"在上层"要遮住东西就必须不透明）
grep -rn "Modifier.matchParentSize()\|\.background(\|\.clipToBounds()" --include=*.kt
```

### 静态代码就能查出的两类叠放缺陷

| 症状 | 静态线索 |
|---|---|
| 按钮/图标"从背后透出来" | 底层元素用了 `matchParentSize()` 或 `Box` 叠放，而上层内容**没有 `.background(...)`** |
| 位移元素"看得见却点不到" | 用了 `graphicsLayer`/`alpha` 做位移，或 `offset` 排在 `draggable`/`clickable` **之后**（内层）|

**装机验证**：`adb exec-out screencap` / `screencap` + `pull` 之后
**一定要真的看那张图**（不能只看文件字节数）。重点看：

- 按钮/标签的文字是否完整（尤其是上下边缘）
- 抽屉/卡片的高度是否贴着内容，有没有大片无意义空白
- 单行里的名称是否被压成省略号
- **有没有"不该出现的东西"**（叠放层级没遮住、越界内容没裁剪）

## 一句总结

**间距和高度不是"看起来差不多就行"，它们是硬几何。**

`容器高度 − 内边距 ≥ 内容高度` 这条不等式，写代码时算一遍，
比装机后返工便宜得多 —— 尤其当它被打包进共享组件、影响 N 个页面时。

**叠放布局同理**："在上层"只是 z 序，**不透明才遮得住**；
而位移、绘制、命中测试是三条不同的链路，`offset` 三者都动、`graphicsLayer` 只动第一条。
