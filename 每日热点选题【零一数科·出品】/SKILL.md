---
name: 每日热点选题【零一数科·出品】
description: 【零一数科·出品】：每日热点选题——每天获取抖音、小红书等平台今日热榜，结合你指定行业/品牌关键词，匹配出可跟进的热点选题（含切入角度、文案方向、形式建议、风险提示、排期建议），把当天热点跟你产品结合出选题，一键出 Markdown 日报。热门搜索词：小红书热点、抖音热点、今日热搜、蹭热点、热点选题、追热点。触发词：热点日报、今日热点、热点选题、热点追踪、社媒热点。
metadata:
  slug: lingyi-daily-hot-topic
  version: v0.1.0
  author: 小风、CoderPig、Awen
  requires:
    bins:
      - python3
---

# 每日热点选题【零一数科·出品】

> 版本：v0.1.0 · 作者：小风、CoderPig、Awen

每日社媒热点采集 + 选题匹配：给一个行业（可补品牌/产品关键词、平台、营销目标、选题数量），后端自动采集抖音/小红书等今日热榜，结合品牌关系算法匹配出可借势选题，并给到切入角度、文案方向（Hook/信息点/CTA/避雷表述）、形式建议、风险提示与排期建议，产出一份完整 Markdown 日报。

通过 **异步统一任务接口** 提交：`POST /api/v1/content/hot-daily/tasks` **立即返回 `task_id`**，再通过 `GET /api/v1/content/hot-daily/tasks/{id}` 轮询进度与结果。服务端后台完成采集/生成/结算，任务级结算扣点；脚本从 `data.markdown` 取完整日报、从 `data.billing.total_points` 读实扣。接口契约见 [references/api.md](references/api.md)，交互约定见 [references/usage-notes.md](references/usage-notes.md)。

## 执行流程

按以下顺序执行，每一步都对应后续章节细节：

1. **取 API Key**：读技能目录下 `config.json` 的 `LY_API_KEY`（回退环境变量）。缺失按「鉴权」流程引导用户获取并写入，再继续。
2. **收集信息**：与用户确认行业（必填），其余品牌/平台/目标/数量缺项给默认。详见「信息收集」。
3. **扣点确认（必做，跳过不得）**：跑脚本**前**向用户说明「本次任务较复杂，预计扣点约 12 点，实际扣点视任务复杂程度而定、以最终完成任务时的实际点数为准」，请用户确认后再继续；用户未确认不要运行脚本。详见「扣点与确认」。
4. **拆分轮询（关键，防会话中断）**：热点日报跑 1～2 分钟，WorkBuddy/Web 单轮对话有时长上限——**禁止**一次同步调脚本阻塞到完成。改成「创建 + 多次短轮询」：
   a. **创建**：`python3 scripts/hot_daily.py --industry "美妆" --only-create`，立即拿 `HOT_DAILY_TASK_ID` + `HOT_DAILY_STATUS` + 初始进度（退出码 0）。**创建调用必须用 `--only-create`，不要把轮询塞进同一次调用。**
   b. **告知用户**：用 task_id 诚实告知，例如「热点日报已提交，任务 ID xxx，约 1～2 分钟。我会持续跟踪进度，有进展同步给你。」**不要**承诺「完成后自动取回」——单轮阻塞做不到自动续接，要靠你主动循环轮询续接。
   c. **循环轮询**：立即跑 `python3 scripts/hot_daily.py --poll-task <id> --industry "美妆" --out ...`（单次 ≤90s）。建议带 `--industry`（报告标题兜底）。每次返回后**无论结果如何都先给用户一句话进度**，再决定下一步：
      - **退出码 0**（终态成功）：进入「输出交付」。
      - **退出码 13**（仍进行中，**非失败**）：取 stdout 的 `HOT_DAILY_STATUS` / `HOT_DAILY_PROGRESS` / `HOT_DAILY_EAPSED` 转述，**立刻再跑一次 `--poll-task <id> --industry "..."`** 继续。不要停。
      - **退出码 12**（任务真失败）：按「退出码处理」走失败话术 + 可 `--retry-task`。
      - **退出码 2/3/4/8/10/11**：按「退出码处理」。
   > 要点：会话不中断的核心是「每轮轮询都给用户一句话 + 立即续下一轮」。
5. **进度应答**：用户中途问进度时，取最近一次 `--poll-task` 返回的状态自然转述；距上次轮询过一会儿可再跑一次现查。**禁止**回复「查不了任务状态 / 没有 task_id」。
6. **交付报告（成功）**：见「输出交付」——把分隔符之间的 Markdown **真正渲染**给用户，告知实际扣点与查看方式。
7. **失败处理**：见「退出码处理」——非发起阶段失败（2/3/4/8）按对应话术；已发起但失败（11/12）告知「因网络原因本次任务执行失败，相应点数已返还」。退出码 13 **不是失败**，按第 4c 步续轮询。

任一步异常按「退出码处理」表对号入座，**不要自行判定失败**。

## 鉴权

Token 取「技能目录」（SKILL.md 所在目录）下 `config.json` 的 `LY_API_KEY` 字段，回退环境变量 `LY_API_KEY`。请求头 `Authorization: Bearer <api_key>` + `X-Appbuilder-From: openclaw`。`config.json` 形如：

```json
{ "LY_API_KEY": "你的密钥" }
```

运行前先确认 key：

1. **检查是否已有 key**：读 `config.json` 的 `LY_API_KEY` 是否非空；无则看环境变量 `LY_API_KEY`。任一有值即就绪。
2. **缺失则引导用户获取**：前往 `https://claw.lingyishuke.com/webapps/01claw-auth/index.html?source=workbuddy` 取 API Key，把 key 直接发给你；收到后写入 `config.json` 的 `LY_API_KEY` 字段（保留其它内容）再继续。该文件已被 `.gitignore` 忽略。
3. **鉴权失败（退出码 8）**：key 失效或过期，重新获取并覆盖写 `config.json` 后重试，不反复用同一失效 key。
4. **SSL 错误**：可设环境变量 `LY_SKIP_SSL_VERIFY=1` 或 `--insecure` 后重试（仅在受控环境临时用）。

## 信息收集

详见 [references/usage-notes.md](references/usage-notes.md)。要点：

| 字段 | 必填 | 默认 |
|------|------|------|
| `industry` 行业 | 是 | — |
| `brand_keywords` 品牌关键词 | 否 | `[]`（建议给，越准越能植入自身产品） |
| `platforms` 平台 | 否 | 全部平台 |
| `goal` 营销目标 | 否 | 种草 |
| `count` 选题数量 | 否 | 8 |
| `additional_requirements` 额外要求 | 否 | 无 |

- 触发后先看行业是否已给；行业缺失则一次性问清（只问 1 轮），其余缺省用默认、不阻塞。
- 平台/目标等用中文与用户沟通，内部枚举值（`douyin`/`种草` 等）不暴露给用户。
- `--platforms`/`--brand-keywords` 接逗号分隔 CSV（如 `--platforms douyin,xiaohongshu`）。

## 扣点与确认

本技能每次「新发起」任务会消耗点数（统一任务成功结算一次），整条链路对用户的扣点感知由你（assistant）贯穿：

- **执行前确认（必做，跳过不得）**：信息收集完成、API Key 就绪后，运行脚本**前**向用户说明并请其确认：
  > 本次任务较复杂，预计扣点约 **12 点**，实际扣点视任务复杂程度而定、以最终完成任务时的实际点数为准。是否继续？
  等用户**明确确认**后再运行脚本；用户未确认、未回应或要求改主意时，**不要运行脚本**。
- **执行成功后回告实际扣点**：把脚本透出的 `HOT_DAILY_POINTS_USED` 告诉用户（为空时按「约 12 点（实际以服务端扣点为准，可在 01Claw 账户查看）」说明），并给出查看报告方式。
- **执行失败后告知点数返还**：任务已发起但未成功产出日报时（退出码 11/12），告知用户「因网络原因本次任务执行失败，相应点数已返还」并询问是否重试；有 task_id 可用 `--retry-task` 重试。

> 扣点口径：脚本优先读服务端 `data.billing.total_points`；未命中留空。约定估值（约 12 点）仅作「约 N 点」提示，**不当作实扣数字**；实际以最终完成任务时的点数为准，真正实扣以 01Claw 账户为准。

## 运行方式

```bash
# —— 推荐：拆分轮询（WorkBuddy/Web 防会话中断）——
# 1) 创建（立即拿 task_id，退出0）
python3 scripts/hot_daily.py --industry "美妆" --brand-keywords "兰蔻,小棕瓶" \
  --platforms douyin,xiaohongshu --goal 种草 --count 8 --only-create
# 2) 循环轮询（单次≤90s；终态退出0交付报告，仍运行退出13续轮询）
python3 scripts/hot_daily.py --poll-task <task_id> --industry "美妆" --out ./热点日报.md
#   ↓ 退出13就再跑一次，循环到退出0

# —— 一把梭（同步：创建后内部轮询到终态，Web 端易被打断，慎用）——
python3 scripts/hot_daily.py --industry "美妆" --brand-keywords "兰蔻,小棕瓶" --out ./热点日报.md

# 失败后按 task_id 重试（异步，已成功不重跑）
python3 scripts/hot_daily.py --retry-task <task_id> --out ./热点日报.md
```

可选参数：

- `--industry`：行业名称，1～64 字符（必填，仅创建/新建模式必填）。
- `--brand-keywords`：品牌或产品关键词 CSV，如 `兰蔻,小棕瓶`。
- `--platforms`：平台过滤 CSV，如 `douyin,xiaohongshu`；可选 `douyin/xiaohongshu/weibo/kuaishou/zhihu`，缺省=全部。
- `--goal`：营销目标 `种草`/`带货`/`品宣`/`引私域`，默认 `种草`。
- `--count`：期望选题数量 5～10，默认 8。
- `--additional-requirements`：额外要求，≤2000 字符。
- `--out PATH`：报告输出路径；未传时自动写入当前目录的 `热点日报-<task_id>.md`。
- `--insecure`：跳过 SSL 校验。
- `--timeout 90`：单次轮询等待上限秒数（默认 90）。到点不是错误——进行中任务 emit 状态后退出 13 让你续轮询。
- `--poll-interval 5`：进度轮询间隔秒数，默认 5。
- `--idempotency-key KEY`：幂等键；缺省自动生成 UUID。同任务重复提交保持不变。
- `--only-create`：仅 POST 创建拿 task_id 后即退（退出码 0，不轮询）。
- `--poll-task TASK_ID`：对已有 task_id 执行 GET 轮询；建议带 `--industry`。
- `--retry-task TASK_ID`：对已有任务调用 `/tasks/{id}/retry`，跳过 `--industry`。

## 输出交付

成功时 stdout 形如：

```text
HOT_DAILY_POINTS_USED=<本次实际扣点，可能为空>
HOT_DAILY_PLAN_POINTS=12
HOT_DAILY_REPORT_FILE=<报告文件绝对路径或空>
HOT_DAILY_TASK_ID=<任务 id，便于重试>
=== HOT_DAILY_REPORT_START ===
<完整 Markdown 日报>
=== HOT_DAILY_REPORT_END ===
```

交付时**按顺序**做三件事（缺一不可）：

1. **渲染报告（最重要）**：截取 `=== HOT_DAILY_REPORT_START ===` 与 `=== HOT_DAILY_REPORT_END ===` 两个分隔符**之间**的 Markdown 正文，把它**作为 Markdown 渲染呈现给用户**——让用户看到真正的标题、热榜表格、选题卡片、排期表等排版，而不是带分隔符或 `\n` 字面的原始文本。
   - 不要展示分隔符行、`HOT_DAILY_*=` 协议行。
   - 不要只说「日报已生成」却不渲染正文。**正文必须出现在回复里**。日报较长时，至少完整渲染「今日速览 + 今日热榜 + 优先跟进选题 + 排期提示」并说明完整日报已落盘。
   - 日报 `markdown` 由后端原样返回，直接渲染，不二次加工、不改 table、不改选题文案。
2. **告知实际扣点**：非空说「本次实际扣除 N 点」；空说「约 12 点（实际以服务端扣点为准，可在 01Claw 账户查看）」。
3. **告知报告查看方式**：报告已渲染在上方对话中；同时已保存为 MD 文件，路径见 `HOT_DAILY_REPORT_FILE`（绝对路径）。脚本对落盘做了三级兜底（`--out` → 当前目录 `热点日报-<task_id>.md` → `/tmp/热点日报-<task_id>.md`），只要终态有 markdown 就一定生成 md 文件。

## 退出码处理

| 码 | 含义 | 处理 |
|----|------|------|
| 0 | 成功 | 按「输出交付」处理。 |
| 2 | 缺 API Key | 引导去 `https://claw.lingyishuke.com/webapps/01claw-auth/index.html?source=workbuddy` 取 key，写入 `config.json` 后重试。任务未发起，不涉扣点。 |
| 3 | 参数非法（含 400/422） | 行业为空/超长、goal 非法、count 越界、platforms 非法、幂等键冲突等 → 补全后重试。任务未发起，不涉扣点。 |
| 4 | 余额不足（402） | 透出 `recharge_url`（若有），引导充值。任务未发起，不涉扣点。 |
| 8 | 401 key 无效 | 重新获取覆盖 `config.json` 后重试。任务未发起，不涉扣点。 |
| 10 | 其他 4xx（如 404 任务不存在/不属于本账号） | 透出服务端 message，检查 task_id 与 API Key。4xx 一般未扣。 |
| 11 | 5xx / 网络错误 | 告知「因网络原因本次任务执行失败，相应点数已返还」，转述 stderr 原因，询问是否稍后重试。 |
| 12 | 已发起但任务未成功 | status 为 `failed`/`billing_failed` 等，或终态但无可读日报。告知「点数已返还」；有 `task_id` 可 `--retry-task` 重试。`failure_code=ATTEMPTS_EXCEEDED` 已达最大尝试次数，停止重试转人工；`MISSING_ACCOUNT` 提示检查 API Key/账号。 |
| 13 | 进行中，未到终态（**非失败**） | **不涉及扣点返还**——取 stdout 进度转述，立即再跑 `--poll-task` 续轮询，循环到终态(0)或真失败(12)。 |

> 任务已发起但未出日报（11、12）统一告知「点数已返还」并问是否重试；13 是「进行中、可续轮询」，既非失败也不返还；任务未发起到位（2/3/4/8）不涉扣点，正常引导修正。

未知错误**不要自行判定失败**；按表对号入座，按 stderr 透出的原因处理。

## 免责声明

- 热点榜单与热度数据由后端实时采集，可能存在采集时延与平台口径差异，**时效性强，建议尽快落地**，过期需重新生成。
- 选题推荐与「相关度/综合分」为模型参考判断，**不承诺精确**，仅作选题灵感，正式发布前建议人工复核合规与品牌调性。
- 日报中的「避雷表述」为参考，不构成法律/合规免责，重大发布前以平台规则与法律法规为准。

## 通用原则

- 引用 reference 用相对于 SKILL.md 的路径。
- 日报 `markdown` 由后端原样返回，skill 不做模板、不改 table；脚本仅在内容无 `#` 起首时兜底补一级标题。
- 最终 MD 由脚本一次性覆写 `--out`，agent 不要手动追加/改写输出文件。
- **交付日报时务必把分隔符之间的 Markdown 真正渲染给用户**，这是硬性交付要求。
- 只使用异步统一任务接口：`POST /api/v1/content/hot-daily/tasks` 创建 → `GET /tasks/{id}` 轮询 → 可选 `POST /retry`，见 [references/api.md](references/api.md)。
