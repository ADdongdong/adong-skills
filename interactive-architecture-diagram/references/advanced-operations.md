# 高级操作

仅在任务涉及已有图、现成 CW 文件、导出或链接注入时读取本页。

## 修改结构化图

若上次返回 `saved_authoring_file`，先读取该规范 JSON，保留 ID 和模板版本，修改后通过 `--authoring_file` 提交；不展开 D2/CW。文件丢失时使用 `export_contextweave_code.cjs --session_id "<id>" --format authoring --path "<工作区绝对目录>"` 恢复。完整流程见 [结构化调用与编辑](authoring.md)。付费变体沿用自己的调用入口。

## 修改普通图

从上一轮返回 JSON 中取得 `session_id` 并复用。把当前 CW 全文放入请求文件的 `# CW` 代码块；不要只写“基于上一张图修改”。

若本任务此前只授权了普通生成，修改前按 [外部数据传输与授权](external-data-consent.md) 补充说明会发送完整 `initial_cw_code` 并确认一次；已覆盖该类别时不重复询问。

使用 `edit_contextweave.cjs` 按 `session_id` 提交修改意图。客户端本身无状态，因此旧图上下文必须随请求明确提供。

## 导入现成 CW

用户明确提供 `.cw` 文件并要求导入时，直接调用：

首次联网前按 [外部数据传输与授权](external-data-consent.md) 简要说明会发送完整 `cw_code` 和来源路径并取得一次授权。

```bash
node scripts/import_contextweave_code.cjs --path "<绝对文件路径>"
```

此场景禁止重新生成结构化意图文件，也禁止调用 `generate_contextweave.cjs`。

## 导出或找回 CW

用户要求导出或找回某个 `session_id` 的 CW 代码时，必须调用：

如果本任务尚未获得联网授权，先按 [外部数据传输与授权](external-data-consent.md) 简要说明会发送 `session_id` 以找回云端 CW；已有当前任务授权时不重复询问。

```bash
node scripts/export_contextweave_code.cjs --session_id "<session_id>"
```

不要在对话中粘贴 CW 代码来代替实际导出。

## 导出图形产物

用户要求导出已有会话的图形产物时，调用：

如果本任务尚未获得联网授权，先按 [外部数据传输与授权](external-data-consent.md) 简要说明会发送 `session_id` 与目标 `format`；已有当前任务授权时不重复询问。

```bash
node scripts/export_session_asset.cjs \
  --session_id "<session_id>" \
  --format "<format>" \
  --output_name "<语义化英文名>" \
  --output_dir "<输出目录>"
```

根据用户的编辑目标选择格式。用户只说“导出 PPTX”而没有指定实现形式时，使用 `pptx`；用户只说“导出 Visio/VSDX”时，使用 `vsdx`。脚本会将这两个默认值确定性地映射为对应的原生 Office 导出：

| 用户目标 | `format` | 结果特征 |
|---|---|---|
| 浏览器、文档或图片方式使用 | `svg` | 通用矢量图 |
| 默认导出 Visio | `vsdx` | 默认映射为原生二维形状与双端粘附的一维连接器 |
| 明确指定原生 Visio | `vsdx-native` | 与 `vsdx` 等效；保留当前图的路由几何并支持原生编辑 |
| 默认导出 PowerPoint | `pptx` | 默认映射为原生形状与原生连接器 |
| 明确指定原生 PowerPoint | `pptx-native` | 与 `pptx` 等效；原生形状与原生连接器 |
| PowerPoint 中保持 SVG 高保真外观 | `pptx-svg` | SVG 作为矢量媒体嵌入 |
| 必须沿用旧版 PowerPoint 导出链路 | `pptx-legacy` | 映射到后端旧版 `pptx` 格式，仅用于兼容 |

默认原生 PPTX 与 VSDX 导出支持移动节点后连接线继续吸附，但复杂样式可能降级。用户更看重 PowerPoint 视觉还原并明确接受非原生连接器时才选择 `pptx-svg`；只有明确要求兼容旧链路时才选择 `pptx-legacy`。不要把普通 SVG“转换为形状”描述为原生连接器，也不要把 PPTX 改扩展名描述为 Visio 导出。

## 为节点或连线添加文件链接

绘图与链接设置必须分两步完成：

1. 调用 `generate_contextweave.cjs` 生成结构，首次请求忽略链接要求。
2. 取得 `session_id` 后，调用 `edit_contextweave.cjs` 批量注入链接。

如果首次授权已经包含链接注入，则两步之间不再询问。否则在第二步前补充说明会发送完整 `initial_cw_code` 和绝对 `base_path`，取得一次确认；不回显路径值。用户不同意时停止链接注入，但保留第一步生成的不带链接图形。

第二步的 `# Request` 使用以下 JSON 指令：

```json
{
  "base_path": "<当前工作区绝对路径>",
  "links": [
    { "targets": ["模块A"], "link": "./src/module.py#L10-L25" },
    { "targets": ["模块A到模块B的连线"], "link": "./src/api_handler.py" }
  ]
}
```

- `base_path` 必填。
- 文件路径不加 `file:///` 前缀。
- 指向代码行时使用 `#L<起始>-L<结束>`。

## 脚本能力索引

| 脚本 | 用途 |
|---|---|
| `generate_contextweave.cjs` | 从 `input_file` 生成新图 |
| `edit_contextweave.cjs` | 基于 `session_id` 修改已有图或注入链接 |
| `import_contextweave_code.cjs` | 导入现成 `.cw` |
| `export_contextweave_code.cjs` | 导出或找回会话中的 CW |
| `export_session_asset.cjs` | 导出 SVG、原生可编辑 VSDX、默认原生可连接 PPTX、SVG 高保真 PPTX 或旧版兼容 PPTX |
| `recompile_contextweave.cjs` | 轮询专家处理结果；见 [异常恢复](error-recovery.md) |
| `request_quota_code.cjs` | 发送免费额度验证码；只在相关错误时使用 |
| `redeem_quota_code.cjs` | 兑换免费额度；只在相关错误时使用 |
| `submit_feedback.cjs` | 提交失败分析与用户反馈 |

需要拆分多视图时，读取 [多视图与 Scenarios](multi-view-scenarios.md)。


## 请求记录与结果找回

生成请求发送前保存 `.cw_skill/requests/<请求号>.receipt.json`；成功、草稿和失败都会写回原响应。网络异常时状态为未确认，不能推断已失败或未扣次。先查询原请求，不要直接再次生成：

```bash
node scripts/query_request.cjs --record "/绝对路径/请求号.receipt.json" --output_dir "/绝对路径/输出目录"
node scripts/query_request.cjs --list
node scripts/query_request.cjs --request_id "原请求号" --output_dir "/绝对路径/输出目录"
```

查询使用现有环境变量里的额度 Key；公共体验必须保留原回执文件中的随机查询凭证。不要将 Key 写入命令、回执或反馈。查询本身不扣次，有结果时恢复 CW 和文件；运行中继续等待，无可用结果且已返还后才可发起新的请求。有图但未通过完整校验时交付草稿并说明 warnings。面向用户应给出文件（若有）、本次次数处理及记录位置，不能只转述错误码。

用户也可以打开 https://pptx.chenxitech.site/requests/view ，输入邮件额度 Key 查看上线后的记录。会话状态仍由后端托管，本地文件仅保存请求回执。旧请求没有完整回执，不声称已经自动补录。
