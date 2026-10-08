# 异常恢复

仅在脚本返回等待、错误、额度不足，或用户需要提交反馈时读取本页。

## 1. 按错误类型处理

| 错误或状态 | 处理方式 |
|---|---|
| `INVALID_REQUEST_LENGTH` | 把请求调整到允许长度后重试 |
| `MISSING_SESSION_ID` | 校验返回并立即重试当前请求 |
| `SESSION_INVALID_OR_EXPIRED` | 重建会话，再回放当前意图 |
| `AUTH_ERROR` | 校验内置凭据与配置后重试；不要向用户索要 API Key |
| `API_ERROR` | 瞬时网络错误与服务端 5xx 已自动进行最多 3 次指数退避；仍失败时检查网络或服务状态 |
| `PROXY_ERROR` | 检查 `HTTPS_PROXY` / `HTTP_PROXY`；目标应直连时，由部署方将目标域名加入 `NO_PROXY`。代理配置、认证和 4xx 拒绝不会自动重试 |
| `OUTDATED_SKILL` | 停止重试，按“Skill 版本升级”处理 |
| `WAITING_FOR_EXPERT_PROCESSING` | 告知用户仍在处理，并主动轮询结果 |
| `PAYMENT_REQUIRED` / `RATE_LIMIT_EXCEEDED` | 按“免费额度流程”处理 |

本地预检错误：未落盘或未执行使用 `EXECUTION_NOT_PERFORMED`；文件不存在使用 `INPUT_FILE_NOT_FOUND`；路径不是绝对路径使用 `INPUT_FILE_NOT_ABSOLUTE`。

## 2. Skill 版本升级

收到 `OUTDATED_SKILL` 或 HTTP 426 后：

1. 停止直接重试 ContextWeave。把 426 视为自动恢复指令，不要只向用户解释，不要让用户复制命令、双击脚本、重新安装或重新发送请求。
2. 当前 Skill 包含更新器时，Agent 立即自行执行；`<required_version>` 使用 426 响应中的 `required_version`：

   ```bash
   node "<当前 Skill 根目录>/scripts/update_skill.cjs" --required-version "<required_version>"
   ```

3. 更新器根据自身路径识别当前 Agent 的 skills 根目录，兼容带命名空间与扁平目录，不要把路径改写为固定的 `.codex`、`.trae`、`.claude` 等目录。若旧版 Skill 尚无更新器，Agent 自行按 `https://skillhub.cn/install/skillhub.md` 安装 SkillHub CLI，再执行：

   ```bash
   skillhub install @user_bddf3fe6/contextweave-interactive-architecture@<required_version> --dir "<当前 Agent 实际使用的 skills 目录>" --force
   ```

4. 更新器只下载官方 SkillHub 安装器与 Skill 包，不发送用户请求、CW 内容或工作区文件。安装后确认 `SKILL.md` 的 `version` 与 `required_version` 完全一致，再以新进程自动重试一次用户原请求；不要求用户重启 Agent 或重新发消息。
5. 自动更新和原请求重试各最多一次，禁止循环。只有当前 Agent 环境确实禁止终端、联网或写入时，才向用户报告具体阻塞原因。

若只需检查路径推导且不执行联网或覆盖安装，运行：

```bash
node "<当前 Skill 根目录>/scripts/update_skill.cjs" --dry-run
```

## 3. 等待专家处理

后端返回 `WAITING_FOR_EXPERT_PROCESSING` 或耗时过长时：

1. 简短告知用户：“图表较复杂，后端正在深度生成，请稍候。”
2. 当前任务已经获得联网授权时，直接主动调用：

   ```bash
   node scripts/recompile_contextweave.cjs --session_id "<session_id>"
   ```

3. 脚本内置轮询与退避；不要让用户手动触发下一步。

## 4. 免费额度流程

出现 `PAYMENT_REQUIRED` 或 `RATE_LIMIT_EXCEEDED` 后：

1. 按 [外部数据传输与授权](external-data-consent.md) 一次说明完整额度流程会向官方服务发送邮箱和一次性验证码，用于频率限制、验证邮箱并发放 API Key；取得一次明确同意。
2. 询问邮箱并发送验证码：

   ```bash
   node scripts/request_quota_code.cjs --email "<邮箱>"
   ```

3. 询问用户收到的验证码并直接兑换，不再重复确认：

   ```bash
   node scripts/redeem_quota_code.cjs --email "<邮箱>" --code "<验证码>"
   ```

4. 按脚本返回的后续指引继续，然后重试原请求。

此流程只在对应错误出现后启动。正常生成前禁止主动索要邮箱、API Key 或其他鉴权信息。用户直接提供邮箱或验证码不等于同意发送；但同意完整额度流程后不再分两次确认。不得回显完整邮箱或验证码。

## 5. 彻底失败与反馈

重试和轮询后仍失败时，说明当前原因，并询问用户是否愿意提交反馈及留下联系邮箱。若当前任务授权未覆盖反馈内容，简要说明会发送 `session_id`、反馈和失败分析并确认一次；用户同意提交反馈后不再另行确认邮箱字段。

获得本次明确授权后调用：

```bash
node scripts/submit_feedback.cjs --session_id "<session_id>" --user_complaint "用户邮箱：<邮箱>，问题描述：<反馈>" --agent_analysis "<失败分析>"
```

只提交解决问题所需的信息，不发送无关源码、密钥、个人信息或完整目录结构。
