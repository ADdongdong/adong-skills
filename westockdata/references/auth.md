# 认证详情与故障排除

> 何时打开：`auth` 流程失败需要诊断认证状态 / 需要手动设置 key / 需要退出登录。日常使用无需阅读。

## 诊断与退出

| 操作 | 命令 |
|------|------|
| 查看状态 | `westock auth status` |
| 退出登录 | `westock auth clear` |

## 鉴权交互流程（Agent 必读）

### 第一步：检查状态（立即返回）

```bash
westock auth status
```

| 输出 | 处理方式 |
|------|---------|
| `READY` | ✅ 已鉴权，直接执行用户任务，无需后续步骤 |
| `AUTH_REQUIRED:<url>` | 向用户展示授权链接（模板见第三步），随后**立即进入第二步** |
| `ERROR:*` | 告知用户具体错误信息，并引导走**第四步人工兜底** |

> 未鉴权时 `status` 会**顺带生成新的授权链接**，此前未使用的链接同时作废。

### 第二步：等待授权完成

> ⚠️ **展示链接后立刻开始轮询，不要停下来问用户「授权好了吗」。**
> 等待是**自动**的：用户只需扫码，Agent 自行轮询到结果出现为止，无需用户回报。

轮询 `auth fetch` 直到完成（间隔 8~10 秒，最多 30 次，覆盖授权链接 5 分钟有效期）：

```bash
for i in $(seq 1 30); do
  out=$(westock auth fetch)
  case "$out" in
    TOKEN_READY)   break ;;      # 授权完成
    ERROR:expired) break ;;      # 超时，回到第一步重新发起
    *)             sleep 10 ;;   # 含 not_authorized，继续等待
  esac
done
```

| 输出 | 处理方式 |
|------|---------|
| `TOKEN_READY` | ✅ 授权完成，继续执行用户任务 |
| `ERROR:not_authorized` | 尚未完成授权，**继续轮询**（用户可能仍在扫码） |
| `ERROR:cancelled` | 用户已主动取消，**立即停止轮询**；询问是否重新发起（回第一步） |
| `ERROR:expired` | 授权链接已过期（5 分钟），回到第一步重新发起 |
| `ERROR:*` | 告知用户错误信息，引导走第四步人工兜底 |

> ⚠️ **轮询期间只能执行 `auth fetch`，不要执行 `auth status`。**
> `status` 发现无 key 时会重新 `issue` 并覆盖本地 `auth-code`，
> 导致用户正在扫的码作废——表现为「明明刚授权完，却仍返回 `not_authorized`」。

### 第二步补充：用户取消 / 放弃授权怎么办

授权页的「取消」按钮**只改前端状态，不通知后端**（`handleCancel` 仅置 `cancelled=true`）；
后端也没有「已取消」状态（`device_code` 只有 `pending` / `done`，`expired` 仅用于响应语义、不落库）。

因此用户取消后（**服务端改造上线前**的行为）：

- 服务端 device_code **仍是 `pending`**，继续占用 5 分钟 TTL
- CLI **无法区分**「用户还没扫码」与「用户已取消」——两者都返回 `ERROR:not_authorized`
- 只能轮询到 5 分钟过期才会拿到 `ERROR:expired`

| 场景 | 处理方式 |
|------|---------|
| 用户明确不想授权 | 执行 `westock auth clear` **立即**清理本地 device_code，不必等超时 |
| 用户只是关掉页面 | 同上；或等待 5 分钟自动过期后重新发起 |
| 轮询满 30 次仍 `not_authorized` | 视为未完成：告知用户链接已过期，询问是否重新发起（回第一步） |

> **服务端改造上线后**：授权页取消会通知后端，CLI 下一次轮询即收到 `ERROR:cancelled`
> 并**秒级退出**，不再等待 5 分钟。届时优先按 `ERROR:cancelled` 处理，
> 上表仅在后端尚未支持取消时适用。详见 `docs/auth/device-auth-cancel-support.md`。

> 提示话术：「如果不想继续授权，可在终端执行 `westock auth clear` 立即取消，不必等链接过期。」

### 第三步：授权链接展示模板

第一步输出 `AUTH_REQUIRED:<url>` 时向用户展示：

> 🔑 **需要先完成专属 APIKey 授权**
>
> 请在**浏览器**中打开以下链接完成授权：**[点击授权]({url})**
>
> ⏰ **授权链接有效期 5 分钟**

### 第四步：人工兜底

自动流程持续失败时，引导用户在授权页拿到 key 后手动设置：

1. 用户在浏览器完成扫码后，授权页会显示专属 APIKey
2. 用户将 APIKey 提供给 Agent
3. Agent 保存到本地：`westock auth set "<WZQ_APIKEY>"`

清除本地 key（退出登录）：

```bash
westock auth clear
```

## 错误说明

| 错误 | 含义 |
|------|------|
| `ERROR:no_code` | 未找到授权码，需重新执行第一步 |
| `ERROR:not_authorized` | 用户尚未在浏览器完成授权，继续轮询等待 |
| `ERROR:expired` | 授权码已过期（5 分钟）或已被领取，重新执行第一步 |
| `ERROR:cancelled` | 用户在授权页主动取消，本次授权已终止；如需继续请重新发起 |
| `ERROR:network:<详情>` | 网络请求失败，检查网络后重试 |
| `ERROR:http_<状态码>` | 接口返回非 2xx（如 `http_404`、`http_500`） |
| `ERROR:code_<业务码>:<说明>` | 后端返回业务错误，如 `code_1620053003:device code dev_id mismatch` |
| `ERROR:save_code_failed` | 授权码写入本地失败，检查用户目录权限 |
| `ERROR:save_token_failed` | key 写入本地失败，检查用户目录权限 |
| `ERROR:empty_key` | 返回的 key 为空 |
