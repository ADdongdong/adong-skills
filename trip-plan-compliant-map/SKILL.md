---
name: trip-plan-compliant-map
description: 生成「带图带地图、手机可读」的旅行行程 HTML 手册——含置顶导航与抽屉目录、手机端自适应（表格改写/示意图横向滑动）、**按天分布的高德/百度导航链接卡**、**「玩什么/吃什么」图文条目卡（缩略图+描述+一键导航）**、合规的腾讯地图交互地图（自动 fit 全部标记）、按真实经纬度投影的 SVG 动线示意图（环线按天分段上色），以及从网络抓取并 base64 内嵌的真实景点照片；同时覆盖**自驾/跨省环线**场景（高速免费时段、限行、停车、长下坡与团雾风险、油费测算、去回不同线的环线设计）。当用户提出旅行/旅游/行程规划、自驾规划、行程攻略，或要求"有图/有地图/有图片/有定位/导航链接/有目录/手机上看"的行程产出时使用。覆盖信息采集 → 真实经纬度获取 → 逐日动线编排 → 自驾核实清单 → 实景照片抓取与校验 → 目录与手机端适配 → 无头浏览器渲染 QA → 单文件 HTML 输出。
agent_created: true
---

# 带图带地图的旅行行程手册生成

产出：**单个自包含 HTML 文件**（含内嵌照片约 3–5 MB），含封面照片墙 + 3–4 张 SVG 图 + 1 张腾讯地图交互地图 + 每日照片墙 + 逐时行程 + 预算表 + 贴士。

## 铁律

1. **地图合规**：生成地图前**必须**先加载 `geo-map-compliance-guard` skill。禁用 Google/Apple/Bing 海外版/**OpenStreetMap 直连瓦片**/Leaflet+OSM/Mapbox。只允许腾讯/高德/百度/天地图，**默认腾讯地图 GL JS + 密钥代理模式**（前端不落 key）。详见步骤 5。
2. **坐标必须真实**：所有景点坐标靠地理编码实取，禁止凭记忆估坐标（唯一例外是地图外景区的标注点，需在图上标注「约」）。
3. **照片必须目视校验**：抓完照片**一定要拼成缩略图并用 Read 看一遍**，确认主体对不对；有烧进画面的标题/大水印要裁掉或换图。宁可少一张，不要放错图。
4. **票价/时刻给区间并注明以官方为准**，不编造精确数字。
5. **不赶路**：单日 3–5 个点；明确写出「体力有限可删减」的骨架。
6. **手机端是主场景**：默认就要做置顶导航 + 抽屉目录 + 表格改写 + 示意图横向滑动，不要等用户提（见步骤 8）。
7. **交付前必须真实渲染 QA**：用无头浏览器截图看一遍，不能只靠"代码看起来对"（见步骤 9）。
8. 结尾固定免责：「以上行程与价格基于公开信息整理，出行前请以官方实时信息（景区公告、车票机票、天气）为准。」

## 步骤 1 · 信息采集（一次问全，用 AskUserQuestion）

必问：目的地+出发地、天数与日期、**具体的抵达/返程车站或机场（自驾则问清出发点精确到小区、座驾型号、几辆车）**、同行人与人数、**预算档次**、**行程主线偏好**（市区深度 / 加一天周边自然 / 博物馆人文）、**图片方案**。

图片方案必须让用户选（AI 生图涉及积分消耗，不能默认替用户花）：
- AI 生成景点插图（消耗额度）— 用 ImageGen 前**必须先告知消耗**
- **抓取真实照片内嵌（免费）** ← 现在可行，见步骤 4
- 只做地图与路线图（免费）

顺手做一件事：**算出每天的星期几**（用 `date` 命令，别手算）。它直接决定行程顺序——**周一闭馆的博物馆、周末高峰、节假日是否照常开放**都靠它。

抵达/返程站一旦确定，整条动线会变：先算「车站 → 酒店」的地铁/打车方案，把抵达日排成"寄存行李 → 午餐 → 一个近的免费景点 → 夜市"，返程日排成"晨游 → 退房 → 午餐 → 地铁去车站"，并给出「若车次早于 X 点就砍掉哪个点」的分支。

## 步骤 2 · 真实经纬度（Geocoding）

可用且免费的 Photon（OSM 数据源，无需 key）：
```
https://photon.komoot.io/api/?q=<名称>&limit=5
```
- 中文名可直接作 `q`；**`lang` 只支持 default/en/de/fr，传 `lang=zh` 会报错**。
- 返回 `geometry.coordinates` 为 `[经度, 纬度]`（WGS-84）。
- 一次 8 个请求并行发，快且稳。
- 地名查不到时换更宽的词（如「兰州老街」查不到就查「南关十字」拿区域坐标再推）。

**网络现实（本机实测）**：shell 走 `http_proxy=http://127.0.0.1:1193`。
- **沙箱内**多数外网站点返回 502；**加 `dangerouslyDisableSandbox: true` 后**才通。
- 通了也只限**国内站点**：`cn.bing.com`、`baike.baidu.com`、`image.baidu.com`、携程/新浪/中新网等图床可用；
  **Wikimedia、Wikipedia、Unsplash、OSM 瓦片一律 502**。
- 但 `WebFetch` / `WebSearch` 工具通道能访问境外站点，可用来读页面取 URL；只取**二进制**时才需要 shell。
- 结论：**取页面/坐标用 WebFetch，取图片二进制用 shell + 提权**。

## 步骤 3 · 编排动线

- **同一天的景点按真实坐标排成一条不折返的线**（例：兰州 Day2 = 省博 103.772 → 黄河母亲 103.796 → 水车园 103.801 → 中山桥 103.815 → 白塔山，由西向东一条直线）。
- 顺序被「营业时间 / 闭馆日 / 日落时间」约束时优先满足约束（博物馆放上午，日落观景点放傍晚）。
- 每天标注：上午 / 下午 / 晚上 + 停留时长 + 交通衔接；单列「餐饮」「交通」「住宿」「贴士」四个 meta 块。
- 出城日额外给**备选方案**（人多 / 抢不到票时改走哪条线）。

## 步骤 3.5 · 自驾场景（Road Trip）额外要做的事

用户说"自驾"时，信息采集要额外问清：**出发地精确到小区/出发点**（别只问城市名，楼盘名往往能反查出行区）、**座驾型号**（决定补能方式与成本）、**几辆车**、行李量。座驾型号一定要去查**官方配置表**（能源类型、油箱容积、CLTC 纯电/综合续航、馈电油耗、后备箱容积），据此算油费。

**必须核实的 6 件事**（都用 WebSearch）：

1. **高速免费时段**——国庆等长假要拿到精确到"X 月 X 日 0:00 至 X 月 X 日 24:00"，并务必告知**以驶离高速出口收费车道的时间为准**（这决定了是否要"先出站再进站"）。
2. **目的地城市限行政策**——三个要点：假期是否豁免、**新能源车是否豁免**（插混也算）、外地车牌规则（有些城市"来兰当日不受限、次日起同城同策"）。搜「X 市 限行 外地车」+「X 市 国庆 限号」。
3. **进城方向的施工/拥堵段**——直接搜「X 市 两公布一提示」，交警发布的东西最准。这类信息常包含"某收费站至某收费站半幅双向通行"，会直接改变进城出口选择。
4. **景区停车场**——是否免费、是否大型、节假日几点满。搜索时用「景区名 + 停车 + 自驾」。
5. **长下坡 / 团雾 / 事故多发路段**——搜「省名 + 高速 + 长下坡 危险路段」，交警公布的"危险路段及事故多发点段"列表是金矿，要写进手册并给驾驶动作（下坡挂低速挡、团雾「降速控距亮尾」且**不开远光**）。
6. **出发/返程高峰时段**——官方提示里通常写着"出程高峰 X 时、返程高峰 X 时"。**如果用户的返程日正好撞上返程高峰，必须明确点出来并给错峰方案。**

**环线设计原则（自驾最大的价值点）**：
- 去程走 A 线、回程走 B 线，**绕成环、不重复路段**。先算两条线的里程，比较"环线总里程"与"去回同线"的差异，把结论写进手册（例：兰州案例中环线比去回同线少走约 300 km 重复里程）。
- 两条高速常在某个枢纽城市交汇，**交汇点→目的地那一段不可避免会走两次**。别硬藏，在路线图注里说明清楚，这反而显得专业。
- 中途休息点、午餐服务区按"每 2 小时进一次服务区、连续驾驶不超过 4 小时"排。

**跨省环线 SVG 的画法**：
- 用城市节点（而非真实路网）画折线，bbox 取所有节点的外接矩形加 5% padding；投影公式同步骤 6。
- **交汇点城市的标签会天然重叠**（两条线都标它），结果是只显示一个——不用特殊处理。
- **指北针别放在起终点节点旁边**（会挤在一起），放到画面中部空白区的右侧。
- 两条线用「实线 + 虚线」区分，配色区分南北/去回，并直接在图上标"去程 · X 线 约 N km"。

**车费怎么算**：油费 = 里程 × 实际油耗 × 油价。**别直接用 CLTC 馈电油耗算**，要说明"高速 120 km/h 巡航实际约为 CLTC 的 1.6–2 倍"，并给区间。插混车型要写明"以油为主、电为辅"，因为假期服务区充电桩排队严重。

## 步骤 4 · 抓取真实景点照片（免费方案）

用 Bing 图片检索：`https://cn.bing.com/images/search?q=<关键词>`，HTML 里同时有原图与缩略图：

```python
raw = get('https://cn.bing.com/images/search?q=' + quote(query) + '&form=HDRSC2').decode('utf-8','ignore')
t = html.unescape(raw).replace('\\\\/','/').replace('\\/','/')   # 先反转义，否则正则匹配不到
murls = re.findall(r'"murl":"(.*?)"', t)   # 原图（第三方站，质量高但可能下不动）
turls = re.findall(r'"turl":"(.*?)"', t)   # 缩略图 ts*.mm.bing.net（稳定、一定下得动）
```
- 每个词先试 `murl`，失败退到 `turl`（`ts{1,4}.mm.bing.net/th?id=OIP...`）；`turl` 可用 `&w=1280&rs=1&c=4` 提分辨率。
- **必须熔断**：单次请求 `timeout=8~9s, tries=2`，每个词给 `budget=75~120s` 总预算。否则会卡在某个 hang 住的域名上跑几十分钟（25s×4 次重试 × 35 个候选 = 灾难）。
- 过滤：`width>=900`、宽高比 `1.15~3.2`、`>=40KB`、PIL 能打开；
  黑名单 host：`699pic 58pic 588ku veer gettyimages shutterstock zhitu qiantu tukuppt pngtree niximg logo icon avatar alibaba taobao jd.com zcool huaban`（图库/水印站）。
- 去重：`md5(im.convert('L').resize((16,16)).tobytes())`。
- 存盘时统一 `RGB → 宽<=1280 → JPEG q80 optimize progressive`。

**抓完必须目视校验**（这一步不能省）：
```python
# 拼一张带文件名的 contact sheet，然后用 Read 工具看这张 PNG
sheet = Image.new('RGB', (cols*tw, rows*(th+pad)), 'white')  # 每格贴缩略图 + 文件名
sheet.save('imgs/_contact_sheet.png')
```
看的时候重点检查：主体是不是这个景点、有没有烧进画面的标题大字、有没有难看的水印。
- 标题字在画面中部时，**按竖直方向切成上下两条**就能同时得到两张干净图（先放大确认文字所在的高度区间，再 crop）。
- 水印站（昵图网、图库号 ID）直接弃用；新闻媒体水印（人民网/新华网）可接受。
- 主题存疑的图**宁可换掉**：换更具体的检索词（「兰州黄河楼 建筑 全景」比「兰州黄河楼 夜景」准）。

## 步骤 5 · 腾讯地图 GL JS（默认场景，密钥代理模式）

**在 SDK script 之前**：

```html
<script type="text/javascript">
  window._TMapSecurityConfig = {
    serviceHost: 'http://127.0.0.1:__WB_HTTP_PORT__/_TMapService/_wbt/__WB_TMAP_SECRET__',
  };
</script>
<script src="https://map.qq.com/api/gljs?v=1.exp"></script>
```
- **SDK URL 绝不带 `?key=xxx`**；两个占位符**原样保留**，运行时自动替换。
- 不要另调 `TMap.setConfig()`（白屏）；不要传 `mapStyleId`（底图变灰）。
- 容器必须有固定高度（`#tmap{height:520px}`），否则不渲染。
- 标记用**内联 SVG 的 data URI**（`'data:image/svg+xml;charset=utf-8,'+encodeURIComponent(svg)`），不引用官方 demo 图片。
- 动线用 `TMap.MultiPolyline` + `TMap.PolylineStyle({dashArray:[8,8]})`。
- 只画点线就别加 `libraries=service`。
- 必须写**降级兜底**：`typeof TMap === 'undefined'` → 「请参考上方示意图」，并用 `try/catch` 包住初始化。

### WGS-84 → GCJ-02（必做，腾讯地图要火星坐标）

```js
var PI=Math.PI, A=6378245.0, EE=0.00669342162296594323;
function outOfChina(lat,lng){ return !(lng>73.66 && lng<135.05 && lat>3.86 && lat<53.55); }
function tLat(x,y){var r=-100+2*x+3*y+0.2*y*y+0.1*x*y+0.2*Math.sqrt(Math.abs(x));
  r+=(20*Math.sin(6*x*PI)+20*Math.sin(2*x*PI))*2/3; r+=(20*Math.sin(y*PI)+40*Math.sin(y/3*PI))*2/3;
  r+=(160*Math.sin(y/12*PI)+320*Math.sin(y*PI/30))*2/3; return r;}
function tLng(x,y){var r=300+x+2*y+0.1*x*x+0.1*x*y+0.1*Math.sqrt(Math.abs(x));
  r+=(20*Math.sin(6*x*PI)+20*Math.sin(2*x*PI))*2/3; r+=(20*Math.sin(x*PI)+40*Math.sin(x/3*PI))*2/3;
  r+=(150*Math.sin(x/12*PI)+300*Math.sin(x/30*PI))*2/3; return r;}
function wgs2gcj(lat,lng){
  if(outOfChina(lat,lng)) return [lat,lng];
  var dLat=tLat(lng-105,lat-35), dLng=tLng(lng-105,lat-35);
  var radLat=lat/180*PI, magic=Math.sin(radLat); magic=1-EE*magic*magic; var sq=Math.sqrt(magic);
  dLat=(dLat*180)/((A*(1-EE))/(magic*sq)*PI); dLng=(dLng*180)/(A/sq*Math.cos(radLat)*PI);
  return [lat+dLat, lng+dLng];
}
```
地图 center 也要转。

### ⚠️ 必须按容器尺寸自动 fit，不能写死 zoom

写死 `zoom:12` 在手机上会把边缘标记（离市区远的景区）挤出视野。用墨卡托公式算：

```js
var bLatMin=90,bLatMax=-90,bLngMin=180,bLngMax=-180;
P.forEach(function(p){                       // P 里要存转换后的 g=[lat,lng]
  bLatMin=Math.min(bLatMin,p.g[0]); bLatMax=Math.max(bLatMax,p.g[0]);
  bLngMin=Math.min(bLngMin,p.g[1]); bLngMax=Math.max(bLngMax,p.g[1]);
});
function fitView(){
  var W=el.clientWidth||360, H=el.clientHeight||420, pad=0.18;
  var dLng=(bLngMax-bLngMin)*(1+pad), dLat=(bLatMax-bLatMin)*(1+pad);
  var midLat=(bLatMin+bLatMax)/2;
  var zLng=Math.log(W*360.0/(256*dLng))/Math.LN2;
  var zLat=Math.log(H*360.0*Math.cos(midLat*Math.PI/180)/(256*dLat))/Math.LN2;
  map.setCenter(new TMap.LatLng((bLatMin+bLatMax)/2,(bLngMin+bLngMax)/2));
  map.setZoom(Math.max(9,Math.min(16,Math.floor(Math.min(zLng,zLat)))));
}
```
再配一个浮在地图右下角的「全览全部标记」按钮方便复位（`position:absolute`，`bottom` 要避开腾讯署名条，约 40px）。

市中心点位密集时（一天 5 个点全在 2 km 内）fit 后必然重叠——在 `#mapinfo` 里加一句「放大后可逐个点开，点右下角可一键复位」即可，别硬拆。

## 步骤 6 · SVG 示意图（离线可看的第二张地图）

交互地图可能因代理/网络失败，**必须**再给纯 SVG 的城区动线示意图。

等距圆柱投影（小范围城区足够准）：
```py
k_x = W/(lon_max-lon_min);  k_y = H/(lat_max-lat_min)
x = (lon-lon_min)*k_x
y = (lat_max-lat)*k_y      # 纬度越大越靠上
```
- 先定 bbox（包住所有点位），再按 `W:H = dlon*cos(lat)*111 : dlat*111` 定宽高比，别把地图拉扁。
- 水系/地铁拿不到真实几何就画**示意走向**，图注写明「为示意」。
- 四天四种颜色画虚线动线（带 `marker-end` 箭头）+ 圆点标记，配 HTML legend；加指北针和比例尺。
- 出城目的地放**第二张**市域示意图（同一套投影，换 bbox）。
- 每张 SVG 都过一遍 `xml.etree.ElementTree.fromstring()`，确认是合法 XML。

## 步骤 7 · 内嵌照片 + 校验 + 交付

**base64 内嵌**（预览面板只稳定服务单文件，相对路径不可靠）：

```python
def fig(name):
    data = load(name, maxw=1280, q=80)                    # 重压再编码，控制体积
    b64 = base64.b64encode(data).decode('ascii')
    return '<figure><img alt="%s" loading="lazy" src="data:image/jpeg;base64,%s">'\
           '<figcaption>%s</figcaption></figure>' % (title, b64, caption)
```
- CSS：`.photos{display:grid;grid-template-columns:repeat(auto-fit,minmax(228px,1fr));gap:12px}`
  `img{height:168px;object-fit:cover}`，封面 `.photos.cover img{height:210px;}` 且隐藏 caption。
- **插入位置用锚点定位**，把照片插到对应那张日卡里。
- ⚠️ **Day 序号 vs 日期不要搞错**：`DAY = {1:..., 2:...}` 里的 1/2/3/4 是天序号，锚点日期是 `10 月 (d+1) 日`。写错一位会让**所有照片整体错位一天**，而且因为每个 `<h3>10 月 N 日` 都存在，脚本不会报错——必须在插入后打印「h3 → 该段内的 figcaption」顺序核对。
- **已有多版手册时优先"复用旧手册的 `<style>` 与交互脚本"**：用 `re.search(r'<style>[\s\S]*?</style>', old)` 提取 CSS、取最后一个 `<script>` 作为 UI 脚本，再拼新 body。**但一定要清点新页面里出现的 id/class 是否在旧 CSS 里有对应规则**——踩过两次：漏了 `#totop`（导致 UI 脚本里 `totop.classList` 报错）和新加的 `.d5 .day-badge`（徽章没配色）。
- ⚠️ **自己重写 CSS 时，拼 HTML 千万别忘了包 `<style>` 标签**：`CSS` 变量若只存裸 CSS 规则，用 `+ CSS +` 直接拼进 `<head>` 会被 HTML 解析器当成正文文本丢到页面顶部，**整页变成一堆 CSS 源码文字**。要么 CSS 变量里就带 `<style>`，要么拼接时写 `'<style>' + CSS + '</style>'`。改完务必截图确认，别只看校验脚本——结构校验（标签闭合、SVG 合法性）**查不出这个错**。
- ⚠️ **给生成函数加可选参数时，位置参数调用会静默吃掉它**。真实翻车：`def day(cls, did, ..., extras, navhint='', nav=None)`，而所有调用方把导航卡片列表当**第 11 个位置参数**传进来 → 落到 `navhint`，`nav` 恒为 `None`，**7 张导航卡全部没渲染**。标签闭合、SVG、JS 语法校验**全过**。教训：① 新增参数尽量**用关键字传参**；② 校验脚本要**数关键 class 的出现次数**（`s.count('class="card daynav"')` 应为 7），而不是只查"有没有报错"。
- ⚠️ **`dict.get(k, [])` + `if not items: return ''` 会掩盖 key 写错**。真实翻车：`DAY_SPOTS` 的键是 `dayN`，某处写成 `nav_block('d4')` → 静默返回空串，卡片消失且不报错。**查表返回空应该抛 `ValueError`**。
- 图源声明放进 footer：「景点照片来源于公开网络图片检索，仅作个人行程参考，版权归原作者所有，请勿二次转载或商用。」

交付前跑校验：
```bash
python -c "
import re,io,xml.etree.ElementTree as ET
s=io.open('xx.html',encoding='utf-8').read()
for k in ['__WB_HTTP_PORT__','__WB_TMAP_SECRET__']: print(k, s.count(k))   # 各 1 次
for i,v in enumerate(re.findall(r'<svg[\s\S]*?</svg>', s)): ET.fromstring(v)
# 再用 HTMLParser 查未闭合/错配标签
"
```
最后 **必须调 `present_files([HTML 绝对路径])`**；不要只 Write 就结束，也不要起本地 http.server。

## 步骤 8 · 目录 + 手机端适配（用户大概率在手机上看，必做）

### 8.0 先定字体（用户说"字体太丑"时尤其重要）
**不要直接用 `"PingFang SC","Microsoft YaHei"` 那套**——Windows 上会落到微软雅黑，小字号发糊、字重单一，很容易被吐槽。

先**扫一遍用户实际装了哪些中文字体**，再据此定字体栈：
```python
from fontTools.ttLib import TTFont   # 没有就 pip install fonttools
for p in 字体目录: 读 nameID 1/2/4/16
```
扫描目录：`C:\Windows\Fonts` 和 `C:\Users\<user>\AppData\Local\Microsoft\Windows\Fonts`。

**优先选 `Noto Sans SC`**——它的 `nameID 1` 就是干净的 `Noto Sans SC`，而且常是**可变字体（VF）**，300–900 全字重都能正确渲染，做精细排版最省事（就是思源黑体的 Google 版）。
备选要看**字体族名是否带字重后缀**：阿里巴巴普惠体每个字重是独立 family（`Alibaba PuHuiTi L/R/M/B/H`），思源黑体同理（`Source Han Sans CN Regular`），写 `font-family:"Alibaba PuHuiTi"` 可能匹配不上。它们只适合放在 fallback 位置。

推荐栈：
```css
font-family:"Noto Sans SC","Source Han Sans CN","Alibaba PuHuiTi","PingFang SC","Microsoft YaHei",sans-serif;
```
西文/衬线点缀：`"Noto Serif SC",Georgia,serif`（用于 eyebrow、小标题、编号）。

### 8.1 拟物化：用户嫌"线条太多"时这样做
核心是**用光影代替描边**。把 `border:1px solid` 全部删掉，换成双层阴影：

```css
--raise:0 1px 2px rgba(72,56,32,.05), 0 5px 14px -6px rgba(72,56,32,.13),
        0 16px 34px -20px rgba(72,56,32,.22), inset 0 1px 0 rgba(255,255,255,.92);
--raise-sm:0 1px 2px rgba(72,56,32,.05), 0 3px 9px -4px rgba(72,56,32,.12), inset 0 1px 0 rgba(255,255,255,.9);
--sink:inset 0 2px 7px rgba(72,56,32,.10), inset 0 -1px 0 rgba(255,255,255,.75);
```
- **`inset 0 1px 0 rgba(255,255,255,.92)` 那层内高光就是"拟物感"的关键**，别省。
- 卡片底色用极淡渐变 `linear-gradient(180deg,#fff,#FEFBF5)`，比纯白有体积感。
- 按下态用 `--sink`（凹陷）而不是变色。
- **表格去线**：删掉 `border-bottom`，改用斑马纹 `tr:nth-child(even){background:#FBF8F1}`；表头 `background:#F6F0E5` + 两侧圆角。
- **页面底色**用径向渐变而不是纯色：`radial-gradient(130% 80% at 50% -10%, #FCF9F2, #F5EFE3 42%, #EFE6D6)`。
- **图标**：为每个章节做 44px 圆角方块徽章（渐变底 + 内高光 + 外阴影），里面放 24×24 描边 SVG；meta 小格用 34px 彩色渐变圆角方块同样处理。数字徽章（Day 1/2/3）用 `linear-gradient(160deg,亮色,深色)` + `inset 0 1px 0 rgba(255,255,255,.4)` + `inset 0 -2px 5px rgba(0,0,0,.16)`。
- 图标写成函数 `I('car')` 返回内联 SVG 字符串，用 `stroke="currentColor"` 跟随文字色。

### 8.2 以「天」为主索引的 IA
当页面内容一多，用户会说"这些章节其实都是一章，我只想知道每天干什么"。改成：
**行前必读（导航/路线/清单） → Day 1…Day N（每天自成一节，装齐当天所有信息：时间表 + 照片 + 花费 + 当天提醒） → 附录（自驾专项 / 费用 / 预约攻略 / 美食 / 贴士）**
- 每天卡里直接放"当天要用的东西"（如 Day 5 里放麦积山约票要点），把细节攻略放附录。
- 目录抽屉和正文目录卡都按这个顺序排，Day 用彩色徽章区分。

### 8.3 导航定位链接（用户说"只想要链接"时）
每个地点给两条链接 + 可复制的坐标，**用 URL 直出而不是让用户搜**：

```python
# 高德：唤起 App 直接规划路线（坐标是 WGS-84 时声明 coordinate=gps）
# https://uri.amap.com/navigation?to={lng},{lat},{urlencode(名称)}&mode=car&coordinate=gps&src=xxx&callnative=1
# 高德：只定位不导航
# https://uri.amap.com/marker?position={lng},{lat}&name={名称}&coordinate=gps&src=xxx&callnative=1
# 高德：关键词搜索（坐标不可靠时用，如小区、餐厅）
# https://uri.amap.com/search?keyword={关键词}&city={城市}&src=xxx&callnative=1
# 百度：网页搜索兜底，不需要坐标、不怕坐标系问题
# https://map.baidu.com/search/{urlencode(名称 城市)}
```
- **坐标明确的景区/车站/酒店 → 用 `navigation` 带坐标**；**小区名、餐厅名这类 POI → 用 `search` 关键词**（避免坐标偏差把人导错门）。
- 坐标一定要标 `coordinate=gps`（高德会自动转 GCJ-02），否则会有几百米偏移。
- 腾讯地图 URI 需要 referer 参数、容易失效，**用高德 + 百度双份更稳**。

**⚠️ 链接要拆到每一天，不要集中成一张大表。** 用户原话："我希望这些地址和链接，分布在每一天，而不要集中展示。"
集中表的问题：走到第三天要回头翻到页面顶部找地址，手机上尤其难用。

做法——把点位按天存成一个 dict，每天一个 `nav_block()` 卡片挂在当天行程下面：

```python
# (显示名, 高德搜索关键词, lng, lat, 城市, 一句话说明, 是否用坐标导航)
DAY_SPOTS = {'day1': [('古家油泼辣子火锅 · 清姜坡老古家', '古家火锅 清姜路', 107.1305, 34.3607, '宝鸡',
                       '渭滨区清姜路与西三路交叉口北行 50 m 路西 · 非遗辣子代表，人均约 60', False), ...], ...}

def nav_block(day, hint=''):
    items = DAY_SPOTS.get(day, [])
    if not items:
        raise ValueError('DAY_SPOTS 缺少 %s' % day)      # ← 别静默返回空
    ...
```
- 卡片标题固定写成「**今天要去的地方 · 点一下直接导航**」，比「导航链接」更像行程的一部分。
- 行结构：`名称 + 灰色小字说明` 一行，`高德导航 / 百度` 两个按钮靠右。
- 「行前必读」里只留一句说明+"点哪天的导航"，不再放点位表；起点/终点归到 D1、沿途服务区归到对应那天。
- 窄屏（≤760px）行要改成两行堆叠：`.navlist li{flex-wrap:wrap}`、`.nn{flex:1 1 100%}`、`.na{flex:1 1 100%}`。

### 8.5 「玩什么 / 吃什么」图文条目卡（用户要"带图片和定位"时）
当用户说"给我推荐一下游览和吃的东西，带图片和定位"，用统一的 `spot()` 组件铺成一列：

```python
def spot(name, img, desc, key, lng, lat, city, bycoord):
    g, b = nav_links(name, key, lng, lat, city, bycoord)
    im = '<img alt="%s" src="data:image/jpeg;base64,%s">' % (name, b64) if img else ''
    return ('<div class="spot">' + im + '<div class="sb"><h4>' + name + '</h4><p>' + desc + '</p>'
            '<span class="na"><a class="btn-g" href="' + g + '">高德导航</a>'
            '<a class="btn-b" href="' + b + '">百度</a></span></div></div>')
```
```css
.spotlist{display:grid;gap:12px;}
.spot{display:flex;gap:13px;padding:11px;border-radius:16px;background:linear-gradient(180deg,#fff,#FBF7F0);box-shadow:var(--raise-sm);}
.spot img{width:138px;height:100px;object-fit:cover;border-radius:12px;flex:none;}
@media (max-width:760px){.spot{flex-direction:column;} .spot img{width:100%;height:168px;}}
```
- 缩略图**必须单独用小的 `maxw`（约 430）重新编码**，别复用正文大图（1120px），否则一份图存两遍、文件暴涨。
- 分两张卡：「**玩什么**（按推荐度排）」+「**吃什么（本地人清单）**」，每张卡顶部放一句 `.note` 给"最省时的排法 / 节奏建议"，比堆条目有用。
- 没有对应实拍图的条目**允许不带图**（文字行照常渲染），不要硬塞一张不相关的图。
- 条目里的店名要落到**具体老字号**（如"常记呱呱（40 多年，只做早上，卖完即止）"），比"某家店"有用得多。

### 8.6 环线图按天分段上色
多天环线别只用"去程/回程"两色，**按天拆折线**：

```python
NORTH   = [...]   # 10/2 去程
SOUTH_A = [...]   # 10/5 兰州→天水
SOUTH_B = [...]   # 10/6 天水→麦积山→咸阳
# 蓝实线 / 金实线 / 橙虚线，节点标签分别 skip 掉已标过的城市
node_labels(SOUTH_A, '#C8961E', skip=('兰州','定西'), big_names=('天水',))
node_labels(SOUTH_B, '#B4643C', skip=('咸阳','宝鸡','天水'), big_names=('麦积山',))
```
腾讯地图的 `MultiPolyline` 同步拆成 3 条，legend 也跟着改。**标注文字要挪到折线右侧留白处**——放在左下方会压住节点名（实测压住了"陇西"，截图才发现）。


### 8.4 目录三件套
1. **sticky 顶栏**：标题 + 「目录」按钮。`position:sticky;top:0;z-index:60`，`padding-top:calc(9px + env(safe-area-inset-top,0px))` 适配刘海屏。
2. **抽屉式目录**：`position:fixed;right:0;transform:translateX(102%)`，打开时加 `body.toc-open` → `transform:translateX(0)` + 遮罩 + `body{overflow:hidden}`。目录含 9 个章节 + 4 个 Day 子项。
3. **正文目录卡**：插在封面照片墙之后（用 `<div>` 配对计数找到封面 div 的结束位置），9 个章节一行 + 4 个 Day 一行，Day 用四天色块区分。
4. 顺带加「回到顶部」浮动按钮（`scrollY>700` 才显示）和滚动高亮当前章节（缓存各锚点 `getBoundingClientRect().top + pageYOffset`，滚动时取最后一个 ≤ `scrollY+110` 的）。

跳转要**用 JS 手动算偏移**（顶栏高 70px），别只靠 `href="#id"`：
```js
var top = el.getBoundingClientRect().top + window.pageYOffset - 70;
window.scrollTo({ top: top < 0 ? 0 : top, behavior: 'smooth' });
```
另加 `html{scroll-behavior:smooth;scroll-padding-top:70px}` 和 `[id]{scroll-margin-top:70px}` 兜底。

**窄屏（≤760px）必须处理的三件事**

1. **表格全部改写**，否则 3–4 列的表格在 390px 下挤成一团：
   - **带时间列的行程表** → 时间做成胶囊标签 + 正文换行的卡片流：
     `.day-body table,tbody,tr,td{display:block}` + `td.t{display:inline-block;background:#FFFBF1;border:1px solid #EBD9A8;border-radius:7px}`
   - **带 `<th>` 表头的表**（交通/预算/美食）→ 隐藏首行表头，用 JS 把表头文字写进每个 `<td data-label="...">`，CSS 用 `::before{content:attr(data-label) "："}` 还原。这套是通用的，别为每张表手写。
2. **手写 SVG 示意图必须能横向滑动**：`@media(max-width:760px){.fig{overflow-x:auto;overflow-y:hidden}.fig svg{min-width:660px}}`。
   > 不这么做的后果：900 单位 viewBox 的图在 347px 宽下缩放 0.386，11.8px 的标注变成 4.5px，**完全看不清**。同时在图上方加一行 `.scrollhint`「手机上可左右滑动查看完整示意图 →」。
3. **照片墙**：`grid-template-columns:1fr`（单列），封面首图通栏 + 其余两列；`img{height:196px}`。

顺手再做的：隐藏 `.sec-head` 的副标题（省横向空间）、`h1` 降到 23px、`.wrap` 底部留 76px（给回到顶部按钮让位）、420px 以下再降一档。

## 步骤 9 · 用无头浏览器做真实渲染 QA（强烈建议）

改完不要只靠"代码看起来对"就交付。用本机 Chrome 截图看一遍。

**关键坑：Chrome headless 的 `--window-size` 有最小宽度（约 500 CSS px）**，直接设 390 得到的是 504 宽的视口，截图只有 390 宽 → 看起来像"文字被右侧裁掉"，其实是假象。

**解法：用 iframe 锁死视口宽度**

```html
<!-- wrapper.html：iframe 内部就是真实的 390px 视口 -->
<iframe src="_pv.html#day2" style="width:390px;height:880px;border:0"></iframe>
```
```bash
chrome --headless=new --disable-gpu --hide-scrollbars --no-sandbox \
  --window-size=500,900 --virtual-time-budget=6000 \
  --screenshot=out.png "file:///.../wrapper.html"
```
- 复制一份 **纯 ASCII 文件名**（`_pv.html`）再测，避免中文路径在 `file://` 下出问题。
- 用 `#fragment` 让 iframe 直接滚到要检查的区块；每个区块一个 wrapper，一次截 8 张。
- 拼 contact sheet（PIL）后 **Read 看**，一次过 8 个区块。
- **判断是否真的横向溢出**：注入脚本比较 `document.documentElement.scrollWidth` 与 `window.innerWidth`，不要目测截图（截图宽 ≠ 视口宽）。
- **大页面（3 MB+）截图容易超时被 SIGTERM**：改成后台跑 `(chrome ... &) ; sleep 55`，或把 `--window-size` 缩小。
- **`#fragment` 定位在图片懒加载的页面上会漂移**，可能截到一片空白。改用**有 id 的中间元素**（如 `#mapinfo`）定位更稳。
- **要看某个 Day 卡下方的区块（如导航卡），`#dayN` 锚点没用**——Day 卡本身就可能比 iframe 高。
  **更稳的招：把目标 `<section>` 整块抽出来单独渲染**：
  ```python
  css = re.search(r'<style>[\s\S]*?</style>', s).group(0)
  i = s.find('<section id="day4">'); j = s.find('</section>', i) + 10
  open('_qa.html','w',encoding='utf-8').write(
      '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">' + css +
      '</head><body><div class="wrap">' + s[i:j] + '</div></body></html>')
  ```
  然后 `--window-size=1120,5200` 一次截完整块，再按需 crop。手机端同理，外面套一层 `iframe{width:390px;height:8000px}`。这比反复调 `#fragment` 快得多。
- **4.8 MB / 34 张 base64 图的页面，无头截图要 55–75 秒才落盘**，串行会超时。必须 `(chrome ... &)` 后台起 + `sleep 60` 等，一次并行 2 张。
- **已知测试环境限制**：`__WB_HTTP_PORT__` / `__WB_TMAP_SECRET__` 在测试副本里不会被替换，所以腾讯地图**底图瓦片不显示**（但标记、图标、动线、缩放控件、腾讯署名都会正常渲染）——这恰好能验证 SDK 与标记逻辑，底图等真实预览再看。
- QA 完删除所有 `_pv*.html` / `_w_*.html` / `_shots/` 临时产物，别留在用户工作区。

## 视觉规范（用户偏好）

- **浅色主题**（亮底深字），暖沙色系：底 `#FAF6EE`、卡片 `#FFF`、主文字 `#22302E`、强调红 `#C0392B`、金 `#C8961E`、绿 `#3E7A5E`、蓝 `#4A6FA5`、河蓝 `#3E7C9B`。
- 中文字体栈**按步骤 8.0 扫出来的实际字体来定**（推荐 `"Noto Sans SC"` 打头），不要照抄 `"PingFang SC","Microsoft YaHei"`。
- 结构：hero → **封面照片墙** → 总览卡片组 → 主线时间轴 → 城区示意图 → 市域示意图 → 交互地图 → 逐日行程卡（照片墙 + 表格 + 4 个 meta 块 + **当天导航卡**）→ 交通 → 预算表 → 必吃清单（配图）→ 贴士 → 免责。
- 信息优先**表格与分点**；照片按"每天一组、张数与该天内容量匹配"铺，别堆一起。
- 加 `@media (max-width:640px)` 适配手机（用户出行时会用手机看）。
