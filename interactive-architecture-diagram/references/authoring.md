# 结构化绘图 v1

仅在泳道、层级卡片或共享轨道矩阵能完整保留用户内容与关系时采用。Skill 写业务结构，后端校验、计算布局并编译 D2；这条生成及结构化编辑路径不调用后端模型。

## 输入与选择

- 新建顺序泳道读取 [泳道协议](authoring-swimlane.md)，默认 JSON。
- 新建分区、嵌套卡片读取 [卡片协议](authoring-cards.md)，默认薄 HTML。
- 各列需要共享行边界或跨行读取 [矩阵协议](authoring-matrix.md)，默认薄 HTML。
- 已有可用 JSON 直接复用。JSON 与薄 HTML 是同一模型的两种作者语法，每次仅提交一种；不让模型重复生成另一份。
- 不能保留关键关系、分支、并行、循环或布局要求时，使用普通请求流程并传 `--diagram_type general`；不得删除内容来套模板。
- v1 不支持局部 `accent_targets`；用户明确要求局部高亮时走 general。整体主色仍可通过 `--base_palette` 传入。

## 新建与修改

在工作区保存 `.cw_skill/requests/<name>.json` 或 `.html`，传绝对路径：

执行时保持当前目录为用户工作区，并用 Skill 内脚本的绝对路径调用；下例的 `scripts/...` 表示 Skill 中的脚本位置。不要为运行脚本切换到 Skill 目录，否则输入文件会被判为位于工作区之外。

```bash
node scripts/generate_contextweave.cjs --authoring_file "<绝对路径>" --output_name "<name>" --output_dir "docs/diagrams"
```

不需要 `# Request`、`# CW`、D2 或额外的长篇自然语言。不要同时传 `--input_file`、`--user_request`、`--outline_file`、`--enable_plan`、`--input_sequence`、`--diagram_style`、`--morphology`、`--diagram_type`、`--accent_targets` 或多候选参数。

客户端先查询 `/capabilities`，再提交版本化 `authoring`；不支持协议、字段校验失败或渲染失败时明确报错，不暗中回退生成，也不进入专家队列。根据错误中的字段或节点位置修正结构后重试。

成功返回 `saved_authoring_file`，指向后端补齐稳定 ID 的 `<name>.authoring.json`。后续编辑优先读取这份文件，保留已有实体及行的 ID 和模板版本；新增实体可省略 ID。仅改内容或顺序时不要重新编号。不要读取展开的 CW 来编辑结构化图。

```bash
node scripts/edit_contextweave.cjs --session_id "<上次返回值>" --authoring_file "<修改后规范 JSON 的绝对路径>" --output_name "<name>" --output_dir "docs/diagrams"
```

文件遗失时恢复业务模型：

```bash
node scripts/export_contextweave_code.cjs --session_id "<session_id>" --format authoring --path "<工作区内绝对目录>"
```

脚本把展开的 CW 保存在文件中而不打印到模型上下文；PPTX 变体仅保存业务模型和 PPTX，保持其导出范围。渲染成功后后端才更新会话，失败时保留旧图。

外部数据传输沿用本任务已有授权和当前变体的调用入口。付费版仍通过 `contextweave_paid.mjs probe` 转发 `--authoring_file`，编辑时同时传 `--session_id`，保持原支付流程。最终回复沿用当前变体的格式，`input_file` 填实际提交的结构文件路径，并在 `result` 中保留 `saved_authoring_file`。
