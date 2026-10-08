# 构图骨架规划

## 联合生成 v2（需要后端能力声明）

后端 `/capabilities.co_design` 同时声明 `versions` 包含 `2`、`execution: "joint"` 时，优先使用 v2 交接完整原文、宏观建议与规则。客户端提交前自动查询；能力缺失返回 `CO_DESIGN_UNSUPPORTED`，不自动降级成 v1。v1 的空跨区关系账本仍是白名单，不能直接换成 v2 的“尚未展开”。

v2 不要求用户侧枚举全部叶子或连线。后端在一次主创作中联合细分内容、建立关系与安排整张 D2；修复看同一候选的诊断和实际渲染。普通自然语言请求、兼容 `enable_plan` 以及外部宏观合同进入同一执行流程。严格 authoring 的完整结构编译仍使用 `--authoring_file`；本版本不支持混合固定 authoring 片段。

```json
{
  "outline_intent_version": 2,
  "source": "应用域包含客户门户，服务域包含订单服务。客户门户调用订单服务。两个域从左到右排列。",
  "focus": "看清两个域的职责和调用方向",
  "regions": [
    {"id":"app","label":"应用域","source_quote":"应用域包含客户门户","suggestions":{"grid_columns":2},"open":["layout","granularity","grouping","routing","style"]},
    {"id":"service","label":"服务域","source_quote":"服务域包含订单服务","open":["layout","granularity","grouping","routing","style"]}
  ],
  "relationships":"required",
  "requirements":[
    {"id":"call","kind":"edge","target":"客户门户","related":"订单服务","origin":"source","strength":"hard","source_quote":"客户门户调用订单服务"},
    {"id":"order","kind":"relative_position","target":"应用域","related":"服务域","value":"left","origin":"user","strength":"hard","source_quote":"两个域从左到右排列"}
  ],
  "budget":{"model_repairs":2,"handoffs":1,"layout_candidates":4,"max_tokens":64000,"seconds":600},
  "target_width":1600,"target_height":900,"min_font_size":10
}
```

- 保存为工作区内 JSON，并传绝对路径 `--outline_file`。`source` 保留完整需求材料，`source_quote` 必须命中该原文；普通 `user_request` 可补充本次编辑指令。客户端不会用字数较短的摘要替换完整原文。
- `hard` 只用于用户明确要求或原文事实；Agent 自己的选择使用 `origin: "agent", strength: "soft"` 或区域 `suggestions`。改变建议须有调整理由。`open` 表示可决定的维度，不授权删除内容。首次生成的固定维度用硬规则表达；缩小 `open` 需要已有已接受区域及绑定，缺少基线时后端明确拒绝。
- 关系状态：`unexpanded` 允许按原文继续识别关系；`required` 是最低覆盖；`forbidden` 禁止物理连线。所有物理边均须有证据，必需方向不能颠倒，不能用标签替代要求的线。
- 当前可检查 `content`、`parent`、`edge`、`forbid_edge`、`highlight`、`grid_columns`、`grid_rows`、`direction`、`shared_boundary`、`relative_position`、`track_span`。`parent/edge/forbid_edge` 用 `related` 表达另一端；共享边界 `value` 为 `left/right/top/bottom`，位置为 `left/right/above/below/same_row/same_column`。`track_span` 的 `target` 是分区，`related` 是共同轨道容器，`value` 为含首尾的 `"1:3"`；只从原文明确的跨度提取。后端测量同一轨道的各处分区边界及轨道顺序，不要求各轨道等高，不等于混合 authoring 编译。仅在能力声明的 `hard_dimensions` 包含 `track_span` 时使用。
- `co_design.status: needs_revision` 表示未通过，保留候选供修订，不宣称成图或进入专家队列。修订携带返回的 `--co_design_revision`，只能改自己的软建议，硬规则及已用预算保留；旧版本和超预算请求被拒绝。已接受图可用 `--session_id`、当前 revision 和自然语言编辑；`--co_design_edit_paths '["实际路径"]'` 限定编辑范围。
- `--co_design_upstream_usage '{"total_tokens":1234,"elapsed_seconds":10}'` 仅填本次用户侧调用由平台报告的真实用量，续传填增量。没有可获得用量时省略，后端记录未报告，不能把估算写成实耗。模型失败和重试也计入实验记录。
- 几何通过不等于业务或视觉验收通过。检查结果中的 `not_run` 必须单列，核对最终 SVG 的完整内容、阅读顺序、文字、边界和路线。失败、取消或超时不会用候选覆盖已接受源码。

实测成对示例：[原文、宏观交接、完整 D2 与 soft 调整理由](co-design-examples/soft-grid.md)。

### 版本化区域视觉方案

后端 `co_design.presentation_presets` 声明支持时，可通过已有 `--base_palette` 选择 `red-gold-compact-v1` 或 `blue-compact-v1`。在现有宏观 `regions` 上增加可选 `style_role`：`frame`（标题/侧栏）、`foundation`（基础）、`planning`（统筹）、`business`（业务）。例如 `{"id":"services","label":"业务服务","source_quote":"业务服务","style_role":"business"}`。不需要逐叶分配颜色；实际绑定到的区域向可见子项继承，嵌套区域取最近角色，显式硬高亮优先。未知角色、缺少方案或不支持的后端会报错，不能静默降级。

视觉方案由程序保存在会话；后续修订继承，不新增模型调用。紧凑方案使用 18 px 字体、平直边框、无阴影，并在现有真实渲染检查中限制叶格额外纵向空白；模型仍负责真实内容、布局和关系。结构错位走原有反馈，不能靠配色通过结构验收。需要共享边界和跨行精确对齐时，优先按实际内容使用 authoring 的 `shared-tracks`，配合同名主题和矩阵 `style_role`，不固定为中央七列。中车式结构见[共享轨道示例](enterprise-central-example.md)，按真实内容调整列和分区。联合生成主题本身不保证矩阵边界对齐。

## v1 兼容规划

当内容适合骨架且准备推荐，或需要落实用户选择／布局授权时读取本参考。读取和提出方案不要求用户先点名骨架；实际生成 OutlineIntent 遵守 `SKILL.md` §3.2 的选择流程。OutlineIntent 是顶层意图约束，不是完整节点图，也不是让 Skill 猜测业务关系的规划器。

## 方案如何映射

- `layered`：采用分层呈现。通常用 `guided`；完整行列由用户指定或随具体推荐被接受时才用 `locked`。
- `three_lane`：采用三栏或中央主链配固定左右侧轨。固定侧轨用 `locked`，三栏必须分别占第 1、2、3 列并共享同一行跨度。
- `stage_grid`：采用多行阶段网格。用户指定或接受了明确 2×2 等完整行列安排时用 `locked`；仅要求紧凑分阶段或授权 Agent 自主安排时用 `guided`。

普通容器分组、普通单轴流程，以及仅仅“内容复杂、节点很多、文字很长”时不要创建 OutlineIntent。`guided` 保留分区身份和顺序，允许后端紧凑调整；`locked` 固定完整顶层 Grid。分行阅读顺序必须保留原文中的阶段顺序与分支，不能为了网格补出业务流程。

## 推荐示例

原文已有准备、执行、校验、回退四个阶段，每阶段都有可比较的输入和结果时，可以说：

> 这四个阶段各有输入和结果，建议按两行两列排列，便于逐阶段对照；主流程和回退分支仍按原文连接。可以采用这个安排，也可以保留普通流程布局。

用户接受该两行两列安排时，用 `stage_grid + locked`，无需再确认行列；只同意紧凑分阶段时用 `guided`。若用户已授权决定布局，说明选取阶段网格的理由后直接采用 `guided`。若只有四个连续动作而无分区阅读收益，直接生成普通流程。

## v1 最小合同

将 JSON 保存到工作区内，例如 `.cw_skill/requests/outline_<timestamp>.json`，再向生成命令传入其绝对路径 `--outline_file`。

```json
{
  "outline_intent_version": 1,
  "focus": "一句话说明读者必须看见的重点",
  "layout_policy": {
    "preset": "layered",
    "grid_mode": "guided"
  },
  "edge_policy": {
    "mode": "sparse_semantic",
    "focus": ["main_backbone", "explicit_dependencies"],
    "preferred_range": [2, 5],
    "inferred_scope": "local_only"
  },
  "content": [
    {
      "item_name": "application",
      "label": "应用层",
      "type": "grid",
      "grid-rows": "[1]",
      "grid-columns": "[1]",
      "content_generation_prompt": "只填充用户原文明确列出的应用层内容"
    }
  ],
  "global_relationships": []
}
```

约束：

- `preset` 仅为 `layered`、`three_lane`、`stage_grid` 或 `auto`；Skill 主动生成时使用前三种明确骨架。
- `grid_mode` 仅为 `guided` 或 `locked`。
- `edge_policy.mode` 仅为 `sparse_semantic`、`ordered_flow` 或 `explicit_only`，默认优先 `sparse_semantic`；`inferred_scope` 只用 `local_only`。
- `item_name` 与关系端点使用唯一 ASCII ID（字母或下划线开头，之后可含数字、`_`、`-`）；Grid 为升序正整数列表，各顶层分区不能占用同一单元格。
- `global_relationships` 只放用户明确表达且必须保留的跨区事实。每项使用 `from`、`to`、可选 `label`、必填 `evidence_quote`、可选 `kind`；端点必须引用 `content.item_name`。
- `evidence_quote` 必须是 `# Request` 中可逐字定位的原文。层级顺序、空间相邻、同属容器都不是关系证据。
- 连线是稀缺资源。不要把分层顺序自动补成 N-1 调用链，不要让通用支撑组件向所有层 fan-out；纯侧轨说明卡默认不挂边。参与真实调用或因果关系的系统不能为套三栏而当成无连线说明卡，用户明确关系仍须保留。
- `preferred_range` 是软目标，不能删除用户明确关系；没有证据的关系不要为了凑边数而创建。

## 三个短例子

- `6b` 分层架构：选 `layered + guided + sparse_semantic`。七个语义层各自成为顶层分区；保留原文明示的 clients → gateway → application → service → infra 主干，以及 Application/Service → Starter 两条集成关系。Nacos/Redis 的通用支撑描述留在来源分区，不扩散成多条边。
- `e9` 中央主链与左右说明：选 `three_lane + locked + explicit_only`。左侧说明、中央 13 步主链、右侧风险规则各占一列；说明卡不挂边，真实风险与否定条件保留为文字，不能添加 `phase_*`、`risk_group_*` 等技术包装分区。
- `670` 四阶段 2×2：选 `stage_grid + locked`，四个阶段按 row-major 占 `[1]/[1]`、`[1]/[2]`、`[2]/[1]`、`[2]/[2]`。只有用户明确声明阶段顺序时才用 `ordered_flow`；Allen 分支与安全限定按原文保留。
