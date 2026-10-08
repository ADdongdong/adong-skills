# 授权协议

按以下流程处理所有依赖 `EM_API_KEY` 的调用。优先复用平台私有的跨会话持久存储；平台凭据不可读、缺失或失效时，再复用本机私有缓存；两级缓存都不可用时，再使用东方财富妙想 MCP 的 `mx_get_user_api_key` 提供的用户级 API Key；只有在该 MCP 工具不可用或未返回有效凭据时，才回退到 skill 内置授权。正常调用直接运行业务脚本，不要先运行 `scripts/auth.py ensure`。

## 凭据读取与授权

1. 先从平台私有的跨会话持久存储读取 `EM_API_KEY`。若存在有效凭据，只为当前业务脚本进程注入环境变量并执行脚本；不要重复调用 `mx_get_user_api_key`。
2. 若平台私有存储不可读、未提供或没有凭据，再安全检查本机私有缓存 `~/.mx-skills/em_api_key`。若文件存在且长度大于 0，直接执行业务脚本，脚本会自行读取该凭据；不要重复调用 `mx_get_user_api_key`。
3. 若两级缓存都没有凭据，再调用东方财富妙想 MCP 的 `mx_get_user_api_key`。该工具成功返回有效 `apiKey` 时，优先把完整 `apiKey` 保存为平台私有的跨会话 `EM_API_KEY`；同时必须写入 `~/.mx-skills/em_api_key`，作为业务脚本可直接读取的本机私有缓存，权限尽量设为仅当前用户可读写。随后直接执行业务脚本；不要向用户展示、复述、打印到 stdout/stderr、写入日志或通过命令回显暴露真实值。
4. 若 `mx_get_user_api_key` 不可用、调用失败、未返回有效 `apiKey`，或当前环境没有可用的东方财富妙想 MCP，再直接运行业务脚本；脚本会检查 `EM_API_KEY` 环境变量与 `~/.mx-skills/em_api_key`，必要时输出 `need_auth: true`。
5. 退出码为 `10` 时，优先把 `authUrl:` 显示为二维码；无法扫码时再提供 `apiKeyUrl:`。不要轮询、等待或询问是否完成，提示用户授权后重新发送原指令。
6. 当且仅当 stdout 同时出现 `remember_api_key: true` 与 `apiKey:` 时，优先把完整 `apiKey` 保存为平台私有的跨会话 `EM_API_KEY`；同时可写入 `~/.mx-skills/em_api_key` 作为脚本可读缓存。不得向用户展示、复述、打印到 stdout/stderr、写入日志或通过命令回显暴露真实值；`apiKeyUrl` 不是凭据。
7. 若 HTTP 或业务 `code/status` 返回 401/403，删除平台私有跨会话存储中的失效 `EM_API_KEY` 与本地私有缓存 `~/.mx-skills/em_api_key`，然后优先重新调用东方财富妙想 MCP 的 `mx_get_user_api_key` 获取当前用户的新凭据并重新缓存；如果仍不可用或仍失败，再进入 skill 内置授权。脚本会清理文件凭据并生成新授权链接；若失效值来自环境变量，按脚本提示先清除环境变量。
8. `~/.mx-skills/pending_auth.json` 只保存待完成授权状态，不是凭据缓存；不要打印其内容。`~/.mx-skills/em_api_key` 是当前机器上供脚本直接读取的本机私有凭据缓存，不替代平台私有跨会话存储的第一优先级。

检查凭据状态时，禁止使用 `cat ~/.mx-skills/em_api_key`、`cat ~/.mx-skills/pending_auth.json`、`echo "$EM_API_KEY"`、`env | grep -i EM_API` 或在 shell 命令中直接拼接真实 key。可以检查文件是否存在、文件长度是否大于 0，或只输出脱敏值（例如仅显示前 4 位和后 4 位）。

缓存命中调用示例：

```bash
python3 <业务脚本> <其余参数>
```

workbuddy 首次获取并缓存后调用示例：

```bash
python3 <业务脚本> <其余参数>
```

skill 内置授权回退注入示例（占位符不是真实凭据）：

```bash
EM_API_KEY='<从私有持久存储读取的值>' python3 <业务脚本> <其余参数>
```

`python3 scripts/auth.py ensure` 只用于调试；退出码 `0/10/2` 分别表示就绪、需要用户授权、授权错误。
