# 外部数据传输与授权

ContextWeave 只连接官方服务 `https://pptx.chenxitech.site`。本任务首次联网前，简要说明将发送的数据类别和用途并取得一次明确同意；用户未同意时不调用脚本。

同一任务内，已披露类别可以继续用于生成、修改、导出和轮询，不重复询问。只有后来新增完整 CW、绝对本地路径、邮箱、验证码或反馈内容等敏感类别时，才补充说明新增类别并再确认一次。用户提供数据本身不等于同意外发。

## 数据说明

| 操作与端点 | 数据类别 | 用途 |
|---|---|---|
| 绘图或修改 `POST /run` | `user_request`；修改时还包括完整 `initial_cw_code`；链接注入时还包括绝对 `base_path` | 生成或修改图，并在需要时生成本地文件链接 |
| 领取额度 `POST /api/quota/send_code`、`POST /api/quota/redeem` | 完整 `email`；兑换时还包括一次性 `code` | 发送验证码、频率限制、验证邮箱并发放 API Key |
| 导入 `POST /session/import` | 完整 `cw_code` 和可能包含本地绝对路径的 `source_name` | 创建云端会话 |
| 导出或继续处理 `/session/export`、`/export-session`、`/session/recompile` | `session_id`，导出时还包括 `format` | 找回、导出或继续处理当前图 |
| 反馈 `POST /api/feedback` | `session_id`、`user_complaint`、`agent_analysis`，可能包含用户自愿提供的邮箱 | 排查问题与后续联系 |

服务端还会看到 HTTPS 连接所需的常规网络元数据；若配置了 API Key，也会把它作为鉴权请求头发送到同一服务。不得显示凭据、完整验证码、CW 全文或绝对路径，也不要承诺未明确说明的数据保留周期。

## 简短询问模板

根据当前任务删去不涉及的项目，一句话说明即可：

```text
ContextWeave 需要把本次绘图要求〔如涉及：现有 CW / 工作区绝对路径 / 邮箱和验证码〕发送到官方服务 pptx.chenxitech.site，用于生成、修改或领取额度；同一任务内不再重复询问。是否同意？
```

如果用户之后新增了未披露的敏感类别，只说明新增项并询问一次，例如：“新增文件链接需要发送工作区绝对路径，用于生成可打开的本地链接，是否同意？”
