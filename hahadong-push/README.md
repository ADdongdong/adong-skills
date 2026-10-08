# 哈哈栋推 GitHub

把本地目录一键推送到 GitHub 的 WorkBuddy skill（显示名「哈哈栋推github」）。

## 为什么需要它

在 WorkBuddy 沙箱里直接 `git push` 会被网络层拦截（curl 能通、git 不能），且 GitHub MCP 连接器是平台只读 token，看不到个人仓库、不能建仓/推文件。本 skill 改用 **GitHub Contents API + 本机个人 token** 直连推送，稳定可用。

## 用法

在 WorkBuddy 对话中说：

> 用哈哈栋推github 把 `E:/xxx/my-skill` 推到 github（公共）

或在 Bash 中直接运行：

```bash
bash <skill_dir>/scripts/push_to_github.sh "E:/xxx/my-skill" [repo_name] [public|private]
```

- 第 1 参数：要推送的目录（默认当前目录）
- 第 2 参数：仓库名（默认 = 目录名）
- 第 3 参数：可见性 `public`（默认）或 `private`

## 它会自动做

1. `git init`（若未初始化）
2. 写入/补全 `.gitignore`，强制排除 `.env`、密钥等
3. 提交改动
4. 从本机 Windows 凭据管理器（GCM）取 GitHub 个人 token
5. 通过 API 创建仓库
6. 逐个文件 PUT 到 GitHub Contents API（已存在则更新）

## 注意

- **不使用代理**（本机全局代理未运行，留着会断网）
- token 不入库、不回显
- 推送后在本地终端跑一次 `git fetch origin && git reset --hard origin/main` 即可对齐历史
