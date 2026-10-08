---
name: android-compose-perf-audit
description: 诊断并修复 Android + Jetpack Compose 应用的卡顿（「软件很卡」「性能优化」「整体重构提速」）。基于静态证据定位真实缺陷并按影响排序，而不是凭架构直觉重构。适用于任何 Android/Compose 项目，含本项目（沙拉记账）的具体基线数据。
agent_created: true
---

# Android / Compose 卡顿诊断与止血

## 铁律：先量病因，再谈重构

用户说「卡」时，**不要先谈架构**。绝大多数「卡」来自几个具体缺陷，
而架构重构（拆模块、换架构模式）**治不了它们**。

我在这条上踩过：用户问「能参考某个优秀项目整体重构么」，
而那个参照项目本身没有 Paging、没有稳定性配置、没有基准测试 ——
它流畅只是因为**没犯那些错**，不是因为它的模块划分。照搬模块划分 = 净负收益。

**流程**：列缺陷 → 按影响排序 → 拿证据 → 分级修复 → 编译验证。

### 铁律 -1：先确认测的是**哪个包**（最前置，别跳过）

**拿到任何 `.apk` 的性能数据之前，先问：这是 debug 包还是 release 包？**

| | debug | release |
|---|---|---|
| `android:debuggable` | true | false |
| ART 安装期 AOT（dex2oat） | ❌ 只做 verify | ✅ speed 编译 |
| 运行时 | 解释器 + JIT 逐步预热 | AOT 机器码 |
| R8 裁剪 / 内联 | 无 | 有 |
| **本项目实测体积** | **47.6MB** | **24.2MB** |

**debug 包的帧率可能只有 release 的 1/3~1/5**，尤其是在刚启动、JIT 还没热起来的阶段。
在 debug 包上量到 40–50fps，**推不出「代码有性能问题」**。

**本项目实例（2026-09-22）**：用户在 120Hz 屏上看到「滑动只有 40–50fps」，
我正准备进一步改 Compose 代码，先查构建配置才发现 ——
`release` 一直**没配 `signingConfig`**，所以历次装机测的全是 debug 包。
**体积差 23.4MB（几乎一倍）就是最直观的证据：体积对不上，测的就不是同一个东西。**

**让 release 可本地安装**：
```kotlin
release {
    isMinifyEnabled = true
    proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
    signingConfig = signingConfigs.getByName("debug")   // 仅本地测性能，不可分发
}
```
构建约 4 分钟（R8 慢），产出体积约为 debug 的一半。

**注意区分两类失败**：release 首启崩溃 = R8 规则缺失（补 keep 规则）；
release 也掉帧 = 才是真的代码性能问题。**两者不要混为一谈。**

**排查顺序**：先排除「测量工具」本身的问题，再谈代码。
否则可能在优化一个根本不存在的问题。

### 铁律 0：先分清「卡顿」和「帧率上不去」——这是两个病

拿到性能反馈，**先问三件事**，不要直接跳进清单：

| 问 | 为什么决定方向 |
|---|---|
| **是偶发卡顿，还是持续不够顺？** | 偶发 = 找**偶发**重活（I/O、首次组合、GC）；持续 = 降**每帧**工作量 |
| **哪些页面都这样？** | 全都如此 → 先查**全局因素**，不是页面内容 |
| **屏幕刷新率多少？** | 120Hz 屏上"只有 60Hz 顺滑度"是个极常见且独立的病 |

**本项目实例（2026-09-22）**：用户先说"滑动掉帧"，我按 jank 排查，找到三处每帧开销
（列表行里的 `DateTimeFormatter.ofPattern`、缺 `contentType`、多余 `background`）——
方向只对了一半。用户随后澄清：**不是卡顿感，是 120Hz 屏只有不到 60Hz，而且三个 Tab 都这样**。

后半句才是决定性线索：「我的」页只有一张用户卡 + 几个列表项，没有任何图表 / 图片 / 自绘，
**连它都跑不满 120Hz → 不可能是页面内容的问题** → 指向全局帧率偏好。

**处置清单**：
- 代码侧声明偏好：`window.attributes = window.attributes.apply { preferredRefreshRate = 120f }`
  （**API 21+**；注意 `Window.setFrameRate` 是 API 30+，在部分项目上直接编译不过）
  它是**偏好不是命令** —— 系统照常在静止时降频，不必担心锁死耗电
- ROM 侧：小米「设置 → 显示 → 屏幕刷新率 → **自定义应用刷新率**」能把单个 App 限到 60Hz。
  **App 侧无法覆盖，必须让用户自己查** —— 别在这上面白改代码
- 同时仍要降每帧工作量：**每帧 8.3~16.7ms 的话，60Hz 装得下、120Hz 装不下**，
  系统就稳定跑 60Hz。这就是"120Hz 屏只有 60Hz"最常见的技术成因

**别忘了**：持续低帧也可能是**每帧工作量**造成的，不是只有 ROM 限帧这一个解释。
两条都要治。

## 高命中率的排查清单（按实际命中率排序）

### 1. 轮询 / 定时器
```
grep -rn "delay(\|while (isActive)\|setInterval\|scheduleAtFixed\|Polling" --include=*.kt
```
**本项目实例**：`MainActivity.onStart` 起了一个 `while(isActive){ pull(); delay(3000) }` ——
App 在前台期间**每 3 秒一次 HTTP**，永不停止，且每轮写一次 SharedPreferences 游标。
→ 1200 次/小时。这就是「有时候非常卡」的主因（卡在网络抖动的那几百毫秒里）。

**判断标准**：把「轮询间隔」换算成「每小时次数」。超过 60 次/小时就要问为什么。
实时性的正解是 SSE/WebSocket 长连接，不是缩短轮询间隔。

### 2. Room 失效风暴（比 N+1 更隐蔽，也更致命）
```
grep -rn "forEach { .*Dao\.\(insert\|upsert\|update\|markSynced\|softDelete\|setStatus\)" --include=*.kt
```
**关键认知**：Room 的**每一次**写操作都会对涉及的表发一次失效通知。
如果该表上挂着 K 个 `Flow` 查询，那么「逐条写 N 条」= **N × K 次全表重查**。

**本项目实例**：`transactions` 表上挂着 5 个 Flow（列表 + 待确认 + 3 个聚合），
下行同步 `SYNC_LIMIT = 200` 且逐条写、无事务 → 一次同步 **1000 次查询**，
首页分组、统计聚合全部跟着重算 200 遍。

**修法（三件一起做，缺一不可）**：
1. 循环内分流成 `toUpsert` / `toDelete` 两个列表；
2. 用 `db.withTransaction { }` 包住整批（room-ktx）；
3. DAO 加批量方法：`upsertAll(List)` / `markSyncedBatch(ids)` 用 `WHERE id IN (:ids)`。

### 3. 系统回调里的主线程重活
```
grep -rn "override fun on.*\(.*\).*{" --include=*Service.kt
grep -rn "SharedPreferences\|prefs.edit()" --include=*.kt
```
**本项目实例**：`NotificationListenerService.onNotificationPosted` 跑在**主线程**，
里面做了「写 SharedPreferences + 正则解析」。而白名单按**包名**判定 ——
**微信的任何一条通知**都会触发一次主线程写盘（6 小时判活精度却按通知频率落盘）。

**修法**：读字符串留在主线程（O(1)，且 `StatusBarNotification` 回调返回后可能被回收），
解析移到后台；写盘做节流（内存记最后落盘时间）。

### 4. UI 读取状态的作用域（Compose 特有）
```
grep -rn "collectAsStateWithLifecycle()" --include=*.kt   # 看读在哪个作用域
```
**核心规则**：`collectAsState*` 读在哪个 Composable 作用域，就订阅在哪个作用域。

**本项目实例**：`RecordScreen` 顶部 9 个 `by vm.xxx.collectAsStateWithLifecycle()` ——
在金额框敲一个字符，整个抽屉（分类横滑、日期卡、隐私开关、CTA）全部重组。

**修法（切片订阅）**：不读值，只把 `State<T>` 句柄传给专用子组件，由子组件内部读。
```kotlin
val amountState = vm.amount.collectAsStateWithLifecycle()   // 不 .value
AmountInput(amount = amountState, onChange = { vm.amount.value = it })
// private fun AmountInput(amount: State<String>, ...) { val v = amount.value; ... }
```

### 5. 高开销的绘制 / 布局
```
grep -rn "listOf(\|floatArrayOf(\|String.format\|\.format(" --include=*.kt  # 看是否在 draw 闭包内
grep -rn "Modifier.shadow" --include=*.kt                                  # 看是否在列表行内
grep -rn "textSize = [0-9]*f" --include=*.kt                               # 裸 px（未乘 density）
```
- **draw 闭包内分配**：`listOf` / `floatArrayOf` / `PathEffect` / `String.format` 全部要提到 `remember`
  （我踩过：`sliceColor()` 在 Canvas 里每个分片 `listOf(8 项)`）。
- **列表行 `Modifier.shadow`**：会给每行建 elevation layer（离屏渲染）→ 滚动掉帧。
  修法：给卡片加 `Flat` 变体，用 1px 描边表达分层。
- **裸 px `textSize`**：3x 屏上只有 1/3 大小。

#### 5b. 列表行重组路径上的**昂贵对象构造**（本项目实测的头号掉帧原因）

```bash
grep -rn "ofPattern\|ZoneId.of\|SimpleDateFormat(" --include=*.kt
grep -rn '"%[0-9.]*f"\.format\|String\.format' --include=*.kt
```
逐条确认它落在**顶层 / `remember` / 非热路径**，还是**每个列表行的重组体里**。

**本项目实例**（`AllTransactionsScreen.AllTxRow`，2026-09 实测）：
```kotlin
Instant.ofEpochMilli(tx.transactionTime).atZone(ZoneId.of("Asia/Shanghai"))
    .format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm"))
```
- `ZoneId.of()` —— 要解析时区 id 字符串
- `DateTimeFormatter.ofPattern()` —— 要**编译日期模式**

两者都是常量却每次重建。60fps 下滑动时每帧十几行 = **每秒上千次模式编译**。
用户报「上下滑动掉帧」时，这一条要第一个查。

**判断标准**：换算成「**每帧次数**」。出现在 `items{}` 的 itemContent 里、或 Lazy 列表的 item 里，
任何"每次重组都新建"的非平凡对象都要拎出来。

**修法三层**（从轻到重，按需选）：
1. **提到文件顶层** `private val FMT = DateTimeFormatter.ofPattern(...)` —— 改动最小、收益最大，先做这个
2. 行数据改成**不可变快照**（`@Stable data class`）并在 `remember(list) { list.map { it.toUi() } }` 里
   预格式化（时间、金额、拼接文案），行内只做渲染 —— 顺带让 item 复用时能跳过重组
3. `remember(key)` 包住，key 取真正会变的值

**同族**：`"%.2f".format(x)`（每次新建 `Formatter`）、items lambda 里的 `BigDecimal(...)` 转换、
draw 闭包里的 `listOf(...)` / `floatArrayOf(...)`。

**反例（不要误改）**：在**位图预渲染**（`drawLineChartBitmap`）、`remember { }` 块、
`LaunchedEffect` 里的同类调用**不是问题** —— 它们每次数据/主题变化才跑一次。
排查时要区分"每帧"与"每次数据变化"，改错地方等于制造新的复杂度。

### 6. 调试脚手架残留在热路径
```
grep -rn "Log\.\|RecomposeCount\|recomposeMap\|nanoTime" --include=*.kt
```
`Log` 在重组/绘制路径里是**真的贵**（字符串拼接 + 系统调用）。
更危险的是**模块级 MutableMap 计数器**（如 `rowRecomposeMap`）—— 永不清理 → 内存持续增长。

### 7. 死依赖与资源
```
grep -rn "material-icons" app/build.gradle.kts   # 有依赖但源码零引用？
ls -la app/src/main/res/font/                    # 未子集化的字体
```
**本项目实例**：`material-icons-extended` 全项目零引用（真图标走字体连字），
纯 2000+ 图标的向量数据；字体 `material_symbols_rounded.ttf` 5.4MB 未子集化。

### 8. 状态刷新缺陷（不是「卡」，但常被误读成卡）
```
grep -rn "\.value" --include=*.kt | grep -i "vm\." | grep -v "\.value ="
```
`StateFlow.value` **读取不构成订阅** —— 页面永不刷新。
本项目有 **6 个页面**犯了这个错（报表永远显示 0、邀请码永远不显示）。

### 9. Worker 静默地从来没有运行过（最阴的一类：不报错、不崩溃、只是不工作）

```bash
grep -rn "@HiltWorker" --include=*.kt
grep -n "InitializationProvider" -A 6 app/src/main/AndroidManifest.xml
adb logcat -d | grep -E "WM-WorkerFactory|NoSuchMethodException.*Worker"
```

**症状**：`WM-WorkerFactory: Could not instantiate <pkg>.XxxWorker` +
`java.lang.NoSuchMethodException: XxxWorker.<init>[class android.content.Context, class androidx.work.WorkerParameters]`。

**根因不是代码写错。** `@HiltWorker` + `@AssistedInject(Context, WorkerParameters, ...)`、
`Application : Configuration.Provider` + `HiltWorkerFactory` **全都写对了也没用**，因为
`androidx.startup.InitializationProvider` 里保留着 `androidx.work.WorkManagerInitializer` 元数据 ——
它在 `Application.onCreate` **之前**就用默认 `Configuration` 执行了 `WorkManager.initialize()`，
之后 `WorkManager.getInstance()` 直接返回这个默认实例，`Configuration.Provider` 永远不被读取
→ 落到默认反射工厂 → 只认 `(Context, WorkerParameters)` 两参构造 → `@HiltWorker` 全部失效。

**修法**（manifest，缺一不可）：
```xml
<provider
    android:name="androidx.startup.InitializationProvider"
    android:authorities="${applicationId}.androidx-startup"
    android:exported="false"
    tools:node="merge">
    <meta-data android:name="androidx.work.WorkManagerInitializer"
               android:value="androidx.startup"
               tools:node="remove" />
</provider>
```
移除后改为惰性初始化：首次 `WorkManager.getInstance()` 时才读 `Configuration.Provider`，此时 Hilt 已注入完毕。

**验证修好了**（成功时抓到的日志）：
```
WM-WorkerWrapper: Worker result RETRY for Work [tags={ <pkg>.data.worker.SyncWorker, sync }]
```
`RETRY` 是**好事** —— 说明 Worker 被实例化并执行了，只是业务失败（比如后端不通）按退避重试。

**⚠️ 这条对本项目的意义**：所有 Worker 都从来没跑过（周期下行同步、离线记账上送、看门狗）。
**推论：那个激进的「每 3 秒前台轮询」很可能就是作者在绕这个坏掉的 Worker。**
所以修完 Worker **才能**安全地删轮询 —— 顺序反了就是把唯一的同步路径拆掉。
**排查这类问题时要问自己：这个「性能缺陷」会不会是别人绕另一个 bug 的无奈之举？**

### 转场（AnimatedContent / NavHost）：位移的是整页，不是那个小控件

转场每帧都要把**整页内容**重新合成到新位置。全屏滑入（`slideInHorizontally { it }`）
在 16.7ms 预算的 60Hz 上还撑得住，在 8.3ms 预算的 120Hz 上就容易把帧时间推过线 ——
而它表现为"整体不够顺"，不像 jank 那么显眼（见铁律 0）。

**处置**：

- 用**轻位移 + 淡入**（屏宽 1/4，Tab 之类平级切换用 1/6）而不是整屏滑入。
  位移过半后离开视口的像素不再参与绘制。
- 进出时长不对称：进 `200ms` / 出 `150ms`。用户注意力已转到新内容，旧内容多留只是拖慢感知。
- `AnimatedContent` 显式关掉尺寸插值：`SizeTransform(clip = false)` ——
  对全屏内容毫无意义，却每帧白付一次测量 + 裁剪。
  注意 `ContentTransform.using` 是 `AnimatedContentTransitionScope` 的**成员函数**，
  只有在 `transitionSpec` lambda 内才可见；定义在普通对象里会报 `Unresolved reference 'using'`，
  需改为直接构造 `ContentTransform(...)`。

**副作用要接受**：`AnimatedContent` 在转场期间**两个页面同时存在于组合中** ——
两个 ViewModel 同时活跃、两份订阅同时在跑。用 `WhileSubscribed(5000)` 时多活的只是这两百毫秒；
若某页面的 VM 构造很贵（同步查库、建大对象），这里会变成一次瞬时尖峰。

**易错**：content lambda 里必须用**参数**（`{ current -> ... }`），不能用外层变量 ——
转场期间读外层变量会让两个页面都渲染成"最新选中的那个"。

## 一个必须纠正的认知（反直觉）

**「把 N 个 StateFlow 合成 1 个 UiState」不会改善性能，反而会让重组粒度变粗。**
任何字段变化都产生新的 UiState 对象 → 整屏失效。
决定重组范围的是「**谁在哪个作用域读状态**」，不是「状态装在几个对象里」。

两者的正确分工：
- **`UiState`（sealed interface）** 给「互斥的整体状态」用 —— Loading / Empty / Content / Failed。
  价值是**非法状态不可表达** + 可测试，**不是帧率**。
- **切片（各自 StateFlow + `State<T>` 下传）** 给「高频单字段」用 —— 输入框、开关。

## 修复顺序（按依赖与收益）

1. **止血批**（不改架构，可独立验收）：轮询 → 同步批量/事务 → 系统回调 → 状态订阅缺陷 →
   删调试脚手架 → 列表去阴影 → draw 分配 → 死依赖/字体
2. **结构批**：UiState 契约（见上）+ 切片订阅
3. **护栏**：Baseline Profile、`compose_compiler_config.conf`、macrobenchmark

## 验收：能用什么、不能用什么

**能**（无设备也可做）：
```bash
./gradlew compileDebugKotlin --offline      # 快速迭代用。本项目约 1–3 分钟
python tools/contrast_check.py              # 设计令牌（若项目有）
grep 扫描确认缺陷清零
```

**⚠️ 但只跑 `compileDebugKotlin` 会埋雷 —— 交付前至少跑一次完整 `assembleDebug`**，见下节。

**不能**：帧率、启动耗时、内存。**必须让用户在真机上跑**：
```bash
adb shell dumpsys gfxinfo <pkg> reset
adb shell dumpsys gfxinfo <pkg> | grep -A5 "Janky frames"
adb shell am start -W -n <pkg>/.MainActivity | grep TotalTime
```

**因此**：不要在没有设备的情况下做大面积的 UI 结构重写 —— 编译通过 ≠ 行为正确。
优先做**局部、可推理正确**的改动（去日志、批量写、去阴影、换 dispatch）。

## 装机实测：三个必踩的陷阱

### 陷阱 1（最贵）：只跑 `compileDebugKotlin` 会让后续 `assembleDebug` 编出「启动即崩」的包

**症状**：
```
java.lang.NoSuchMethodError: No static method -$$Nest$fget<xxx>(
  ...Dagger<App>_HiltComponents_SingletonC$SingletonCImpl;)Ldagger/internal/Provider;
```
注意 `-$$Nest$fgetXxx` —— 这种**合成访问器是 dex 阶段生成的**，不是源码里的。所以
「源码编译通过」完全不能说明 dex 一致。

**根因**：反复只跑 `compileDebugKotlin`（几秒~几分钟）而从不跑 `assembleDebug`，增量状态被切碎：
- Hilt 聚合组件源码是新的（今天）
- KSP 生成源码是旧的（昨天）
- Kotlin `.class` 也是旧的（昨天）

→ `mergeProjectDexDebug` 把**新旧 dex 混装**，`-$$Nest$` 访问器指向已不存在的成员。

**识别信号（不用等崩溃就能发现）**：**APK 体积异常大**。
本项目实测：脏增量包 **81.4MB** vs 干净重建 **49.6MB**，多出的 32MB 就是上上次构建遗留的
陈旧 dex（含早已从依赖里删掉的 `material-icons-extended`）。**体积对不上就是增量脏了。**

**修法**：
```bash
./gradlew clean assembleDebug --offline --no-build-cache --no-daemon \
  -Dorg.gradle.jvmargs="-Xmx6144m -XX:MaxMetaspaceSize=1024m -Dfile.encoding=UTF-8" \
  -Dkotlin.compiler.execution.strategy=in-process \
  -Dorg.gradle.workers.max=2
```
- `clean` 必须（删掉切碎的中间产物）
- `--no-build-cache` 也要 —— 否则脏中间产物可能被 build cache 命中还原回来

**纪律**：**每完成一个批次就 `assembleDebug` 一次**，不要攒到最后。攒着的代价是排查成本（本次花了三轮构建）。

### 陷阱 2：Gradle 守护进程构建中途静默消失

`The message received from the daemon indicates that the daemon has disappeared.`
守护进程日志**戛然而止**，无异常栈、无 hs_err、heap 用量接近 0 —— 是进程被外部干掉的形态。

先排除两种干扰，再改参数：
1. **IDE 共享守护进程**：看守护进程日志的环境变量里有没有 `VSCODE_*` / `IDEA_*`。
   若 IDE 的 Gradle 同步刚好在跑（或触发了 "Stop daemons"），会把你的构建一起干掉。
   → 用 `--no-daemon` 隔离。
2. **资源耗尽**：查物理内存 / 系统提交量 / 磁盘剩余 / 页面文件。本项目当时都充足
   （物理 31.8GB 可用 11.6GB、提交可用 43GB、页面文件 32GB），所以不是资源问题。

上面那套参数（`--no-daemon` + 6GB 堆 + `in-process` + `workers.max=2`）之后连续三次构建稳定。

### 陷阱 3：国产 ROM（MIUI/HyperOS）会挡住 adb 能做的一部分事

| 操作 | 结果 | 替代 |
|---|---|---|
| `pm grant <pkg> android.permission.POST_NOTIFICATIONS` | ❌ `SecurityException: Neither user 2000 nor current process has GRANT_RUNTIME_PERMISSIONS` | 让用户去设置里手动开（`appops set ... POST_NOTIFICATION allow` 会被 uid-mode 的 `ignore` 覆盖） |
| `input swipe` / `input tap` | ❌ `SecurityException: Injecting input events requires INJECT_EVENTS` | 需用户开启「USB 调试（安全设置）」；否则**滚动掉帧测试只能让用户手动做** |
| `appops set <pkg> SYSTEM_ALERT_WINDOW allow` | ✅ 可用 | — |
| `cmd notification allow_listener <pkg>/<service>` | ✅ 可用 | 通知监听权限可以这样一键授予 |

**结论**：装机阶段我能验的是**崩溃 / 启动耗时 / 服务绑定 / Worker 是否运行 / 日志报错**；
**帧率与掉帧必须用户手动跑**，别承诺做不到的事。

### 装机阶段的验收清单（照这个顺序做）

```bash
ADB=/c/Android/Sdk/platform-tools/adb.exe     # Windows 下 adb 常见于 C:/Android/Sdk
"$ADB" devices -l                              # 1) 设备在线、看 ABI
"$ADB" install -r -t app/build/outputs/apk/debug/app-debug.apk      # 功能验证用
"$ADB" install -r -t app/build/outputs/apk/release/app-release.apk  # ★ 测性能必须用这个（见铁律 -1）
"$ADB" logcat -c && "$ADB" shell am force-stop <pkg>
"$ADB" shell am start -W -n <pkg>/.MainActivity    # 2) 冷启动耗时，看 LaunchState: COLD
sleep 8
"$ADB" logcat -d -b crash | tail -20           # 3) 崩溃缓冲
"$ADB" logcat -d | grep -c "FATAL EXCEPTION"   # 4) 应为 0
"$ADB" shell ps -A | grep <pkg>                # 5) 进程存活
"$ADB" shell dumpsys activity activities | grep topResumedActivity
"$ADB" logcat -d | grep -E "WM-|<pkg>" | grep -E " E | W "   # 6) 应用自身报错
"$ADB" exec-out screencap -p > shot.png        # 7) 截图确认真的渲染出来了（要看，不能只看字节数）
```

第 7 步很重要：**截图必须真看一眼**。本次就是靠截图才发现当前装机 UI 仍是旧版
（v4 设计只做在 HTML 原型里、Compose 还没落地），避免了「让用户以为测的是新 UI」的误会。

## 先确认项目有没有版本控制

```bash
git rev-parse --is-inside-work-tree
```
本项目**当前有 git**（2026-09-21 建立基线），`git log --oneline` 能看到分批记录。
但这条检查**每次都要做** —— 历史上它曾长期没有版本控制，而一批改 20 个文件
却没有回滚能力，比任何架构问题都严重。**没有就先 `git init && git commit` 再动手。**

## 本项目（沙拉记账 / CozyLedger）基线

| 项 | 值 |
|---|---|
| 位置 | `E:/14_myProject/shalajizhang` |
| 规模 | 92 个 Kotlin 文件 / 10273 行，单模块（2026-09-22） |
| 栈 | Compose + Material3 + Hilt + Room/SQLCipher + Retrofit + WorkManager，minSdk 28 / targetSdk 34 / compileSdk 35 |
| 编译验证 | `./gradlew compileDebugKotlin --offline`，约 1–3 分钟，**可用** |
| 完整出包 | `./gradlew clean assembleDebug --offline --no-build-cache --no-daemon` + 那套 jvmargs，约 1.5 分钟，**已可用** |
| APK 体积基线 | **47.6MB**（2026-09-22，v4 UI 落地后）。**明显大于此值 = 增量脏了**，需 `clean` 重建 |
| 目标设备 | 小米 14（houji / 23127PN0CC），Android 16，arm64-v8a，**1200×2670 @480dpi** |
| adb 路径 | `C:/Android/Sdk/platform-tools/adb.exe`（SDK 在 `C:/Android/Sdk`） |
| 截图注意 | Git Bash 下必须 `export MSYS_NO_PATHCONV=1`，否则设备路径 `/sdcard/x` 会被转成 Windows 路径 |
| 实测冷启动 | `COLD 553ms` |
| 后端 | `ApiClient.kt:17` 指向 CloudBase，**当前探测 HTTP 000 不可达** → `SyncWorker` 必然 RETRY，属环境问题 |
| 权限现状 | 通知监听 / 悬浮窗已由 adb 授予；**通知运行时权限未授予，且代码里无申请逻辑** |
| 诊断文档 | `docs/perf-refactor.md`（含全部行号与实测数据） |
| 设计侧护栏 | `tools/contrast_check.py` / `tools/ui_token_lint.py` / `tools/token_parity.py` / `tools/build_icon_sprite.py` |
| 版本控制 | **已有 git**（2026-09-21 建立基线）。`git log --oneline` 可看分批记录 |

### 本项目已修掉的两个「非性能」缺陷（都属于本次装机实测发现）

1. **manifest 缺 `WorkManagerInitializer` 的 `tools:node="remove"`** → 两个 Worker 从未运行（详见排查清单第 9 条）。
2. **脏增量构建**（只跑 `compileDebugKotlin` 累积） → 首次装机即崩，APK 虚高 32MB（详见装机陷阱 1）。

### 待办（未做，别以为已完成）

- **UiState 契约（逐屏）、模块拆分（需先做接口抽取）** —— 见 `docs/perf-refactor.md §9`。
  注意这两项是**可测试性 / 可维护性**投入，不是帧率投入 —— 别用「优化性能」的名义去推，
  那正是本 skill 开头那条铁律要拦的事。

### 已完成（别再当待办）

- **v4 设计已落地 Compose**（2026-09-22，Stage 0–4）：`Tokens.kt` 33 个角色 + `AccentPreset` 四组 +
  `CategoryColor` 六槽 + `Type.kt` 语义阶梯；13 个页面全部接入；导航层有统一转场。分批记录见 `design/UI-REDESIGN.md §9`。
  **装机看到的是新 UI**（中性底 + 可切强调色）。
- **导航层转场已统一**：`ui/navigation/Transitions.kt`（push/pop/引导交接/Tab 四类），
  reduced-motion 判定统一在 `ui/theme/MotionSupport.kt`。转场用**轻位移 + 淡入**（1/4 屏宽，
  Tab 用 1/6），不是整屏滑入 —— 这条是有意的性能选择，别"优化"回全屏滑动。
- 独立分片色已落到 `CategoryColor`；`sliceColor()` 降级为"拿不到 key"时的兜底，
  正解是 `legendColor` 按 key 取色。
- 分类色**存 key 不存 hex**；存量 hex 由 `CategoryColor.fromKey` 吸附到最近色板槽。
  ⚠️ 该解析**必须带缓存**（`ConcurrentHashMap`）—— 它会被列表每一行调用，
  无缓存时每行跑一遍「解析 + 12 次加权 RGB 距离比较」，这本身就是掉帧源（见 5b）。
- 外观设置（主题模式 + 强调色）已有入口：`我的 → 外观`；持久化在 `data/util/AppearancePrefs.kt`。
- 本 skill 清单第 1/2/6/7 条（前台轮询、Room 逐条写、调试脚手架、死依赖）已清除 ——
  对应的 grep 现在都是零命中，**改完再跑一遍确认**。
