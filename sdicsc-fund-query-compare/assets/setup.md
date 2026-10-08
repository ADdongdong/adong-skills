# API Key 配置

本技能依赖国投证券数据服务，需配置 API Key。

## 获取 API Key

1. 访问 [国投智慧助手](https://www.sdicsc.com.cn/skills)
2. 点击「登录」并登录账号
3. 点击账号，一键复制 API Key

## 写入配置

用户提供 API Key 后，写入 `memory.md`（位于当前skill根目录下，即 `sdicsc-fund-query-compare/memory.md`）：

```markdown
## 基金对比服务配置

- API Key: [用户提供的API Key]
- 配置时间: [当前时间]
```

脚本自动从 `memory.md` 读取 API Key。如用户更换 Key，更新该文件即可。

## 异常码

- 返回 `401`：未携带 API Key，引导用户按上述步骤配置
- 返回 `403`：API Key 无效，引导用户重新获取并更新 `memory.md`
