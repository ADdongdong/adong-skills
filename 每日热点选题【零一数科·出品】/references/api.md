# 每日热点选题 API 契约（v0.1.0 · 异步任务）

**异步任务模型**：创建/重试立即返回 `task_id`，客户端用 `GET` 轮询进度与结果。

base url 固定 `https://claw.lingyishuke.com/services`（写死脚本，可用环境变量 `LY_BASE_URL` 覆盖）。任务路径前缀为 `/api/v1/content/hot-daily`。

鉴权：`Authorization: Bearer <api_key>` + `X-Appbuilder-From: openclaw` + `Content-Type: application/json`。API Key 由脚本从技能目录 `config.json` 的 `LY_API_KEY` 读取（回退环境变量 `LY_API_KEY`）。

幂等：请求头 `X-Idempotency-Key` 与请求体 `idempotency_key`（**请求体优先**）；缺省脚本生成 UUID。相同幂等键 + 相同参数复用已有任务；相同幂等键用于不同参数返回 HTTP 400。

脚本流程：`POST /api/v1/content/hot-daily/tasks` → 立即拿 `task_id` → `GET /api/v1/content/hot-daily/tasks/{id}` 轮询 → 终态交付。失败可 `POST /api/v1/content/hot-daily/tasks/{id}/retry` 后再轮询（已成功不重跑）。

## 概览

| 接口 | Method | 路径 | 脚本使用 |
|------|--------|------|----------|
| 创建/恢复任务 | POST | `/api/v1/content/hot-daily/tasks` | 主路径（立即返回） |
| 查询任务 | GET | `/api/v1/content/hot-daily/tasks/{task_id}` | 轮询进度与结果 |
| 重试失败任务 | POST | `/api/v1/content/hot-daily/tasks/{task_id}/retry` | `--retry-task` |

## 通用响应外壳

成功：
```json
{
  "api_version": "v1",
  "result": "success",
  "code": 200,
  "message": "Success",
  "timestamp": "2026-07-24T10:30:00.123456",
  "data": {}
}
```
失败：
```json
{
  "api_version": "v1",
  "result": "error.bad_request",
  "code": 400,
  "message": "错误说明",
  "detail": null,
  "trace_id": null
}
```

| HTTP | 场景 | 脚本退出码 |
|------|------|------------|
| 200 | 成功查询到任务（业务 status 另判） | — |
| 400 | 业务参数错误 / 幂等键用于不同参数 | 3 |
| 401 | 缺/无效 API Key | 8 |
| 402 | 余额不足（若网关返回） | 4 |
| 404 | 任务不存在或不属于当前账号 | 10 |
| 422 | JSON 结构/字段类型/取值校验失败 | 3 |
| 500 / 502 | 服务端错误 / 上游账号服务校验失败 | 11 |

---

## 1. 创建热点日报任务（异步）

`POST /api/v1/content/hot-daily/tasks`

服务端在后台完成热点采集、内容生成、点数结算，接口立即返回任务信息。HTTP `200` 仅表示任务已创建或复用幂等任务，**不代表日报已生成完成**；客户端必须保存 `task_id` 并轮询。

### 请求体

```json
{
  "industry": "美妆",
  "brand_keywords": ["兰蔻", "小棕瓶"],
  "platforms": ["douyin", "xiaohongshu"],
  "goal": "种草",
  "count": 8,
  "additional_requirements": "优先口播脚本，避开竞品硬广",
  "idempotency_key": "client-uuid-or-stable-key"
}
```

| 字段 | 类型 | 必填 | 默认值 | 约束 | 说明 |
|------|------|------|--------|------|------|
| `industry` | string | 是 | — | 去空格后 1～64 字符 | 行业名称，如美妆 |
| `brand_keywords` | string[] | 否 | `[]` | — | 品牌/产品关键词列表 |
| `platforms` | string[] | 否 | `[]` | ⊆ `{douyin,xiaohongshu,weibo,kuaishou,zhihu}`；空=全部 | 平台过滤 |
| `goal` | string | 否 | `"种草"` | `种草`/`带货`/`品宣`/`引私域` | 营销目标 |
| `count` | integer | 否 | `8` | 5～10 | 期望输出选题数量 |
| `additional_requirements` | string | 否 | `""` | ≤2000 字符 | 额外要求 |
| `idempotency_key` | string\|null | 否 | `null` | 1～128 字符 | 请求体幂等键；与 Header 同时传时以请求体为准 |

> `platforms`、`brand_keywords`、`goal`、`count`、`additional_requirements` 均**可引导但不强制**，缺省不传由后端用默认值；只有 `industry` 必填。

### 响应 `data`

创建成功时为进行中状态，`markdown` 为空字符串：

```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "pending",
  "markdown": "",
  "billing_status": "pending",
  "billing": null,
  "failure_code": null,
  "failure_message": null
}
```

终态 `succeeded` 时示例：

```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "succeeded",
  "markdown": "# 社媒热点日报｜2026-07-24｜美妆\n\n## 今日速览\n>...\n## 今日热榜\n## 选题推荐\n## 今日不建议跟进\n## 排期提示",
  "billing_status": "settled",
  "billing": { "total_points": "12" },
  "failure_code": null,
  "failure_message": null
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `task_id` | string | 任务 ID；轮询与重试都靠它 |
| `status` | string | 任务状态，见下方枚举 |
| `markdown` | string | **完整 Markdown 日报正文**（含一级标题）；未生成时为空字符串 |
| `billing_status` | string | `pending` / `settled` / `failed` |
| `billing` | object\|null | 结算信息；存在时含 `total_points` |
| `billing.total_points` | string | **本次实际扣除点数**（正式实扣字段） |
| `failure_code` | string\|null | 失败码，见第 5 节 |
| `failure_message` | string\|null | 失败说明 |

> **报告 markdown 取法**：本 API 为单一报告，取 `data.markdown`（顶层字符串，已是完整 Markdown，含 `# 社媒热点日报｜...` 一级标题）。脚本**原样落盘**，不开改 table、不做二次模板。仅当返回内容无 `#` 起首时兜底补一级标题。

### `status` 枚举

| 值 | 含义 | 是否终态 | 脚本处理 |
|----|------|----------|----------|
| `pending` | 排队中 | 否 | 继续轮询 |
| `running` | 采集与生成中 | 否 | 继续轮询，stderr 打进度 |
| `succeeded` | 全部成功且结算成功 | 是 | 交付 `markdown` + 实扣 |
| `failed` | 热点采集/内容生成/任务执行失败 | 是 | 退出码 12，可 `--retry-task` |
| `billing_failed` | 内容已生成但结算失败 | 是 | 退出码 12；已有 markdown 时先交付内容并提示 |

> `billing_failed` 状态下 `markdown` 可能已有内容，但应在任务变为 `succeeded` 后再视为完整成功。

未列出的状态按未知处理：原样透出，不报错。

---

## 2. 查询任务（进度轮询）

`GET /api/v1/content/hot-daily/tasks/{task_id}`

- 无请求体；只能查询当前 API Key 对应账号创建的任务，否则返回 HTTP `404`。
- 响应 `data` 形状与创建相同。脚本默认每 5s 轮询，单次 HTTP 超时 60s，单次轮询等待上限 90s（到点非失败，emit 进行中后退出 13，可续 `--poll-task`）。
- 进度只能从 `status` 与 `billing_status` 推断（本 API 无 `current_module` 等细分字段）。

> HTTP 请求成功只表示成功查询到任务。任务是否执行成功以 `data.status` 为准。

---

## 3. 重试失败任务（异步）

`POST /api/v1/content/hot-daily/tasks/{task_id}/retry`

- 无请求体；响应 `data` 结构与查询相同。
- 立即返回当前快照；后台任务可能尚未完成，客户端需继续轮询。

| 当前状态 | 服务端行为 |
|----------|------------|
| `failed` | 最大尝试次数内重新执行内容生成和结算 |
| `billing_failed` | 已有 `markdown` 时仅重试结算；否则重新执行完整流程 |
| `succeeded` | 不重复执行，直接返回当前任务 |
| `pending` / `running` | 继续现有流程；客户端不应主动重试非终态任务 |

- 脚本：`python3 scripts/hot_daily.py --retry-task <task_id> --out ./热点日报.md`

---

## 4. 扣点字段

```json
"billing": { "total_points": "12" }
```

| 路径 | 类型 | 说明 |
|------|------|------|
| `data.billing.total_points` | string | **唯一正式实扣字段** |

- 任务级汇总：一次提交只扣一次（成功结算后）。
- 脚本优先读 `data.billing.total_points`；未命中则 `HOT_DAILY_POINTS_USED` 留空，由 assistant 按约定估值「约 12 点」说明。
- 约定预估（仅提示，非实扣）：8 选题约 12 点；实际以最终完成任务时的点数为准。

---

## 5. 任务失败码

任务执行失败通过 HTTP `200` 响应中的 `data.failure_code` / `data.failure_message` 表示：

| `failure_code` | 说明 | 处理 |
|----------------|------|------|
| `HOT_DAILY_FAILED` | 热点采集/内容生成/任务执行失败 | 根据 `failure_message` 决定，可 `--retry-task` |
| `BILLING_FAILED` | 内容已生成但结算失败 | 调用重试接口，仅重试结算 |
| `ATTEMPTS_EXCEEDED` | 已达服务端最大尝试次数 | 停止自动重试，转人工排查 |
| `MISSING_ACCOUNT` | 任务缺少有效账号信息 | 检查 API Key 与账号配置 |

---

## 6. 枚举速查

| 字段 | 取值 |
|------|------|
| `status` | `pending` / `running` / `succeeded` / `failed` / `billing_failed` |
| `billing_status` | `pending` / `settled` / `failed` |
| `goal` | `种草` / `带货` / `品宣` / `引私域` |
| `platforms`[] | `douyin`(抖音) / `xiaohongshu`(小红书) / `weibo`(微博) / `kuaishou`(快手) / `zhihu`(知乎) |
