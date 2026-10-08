# 共享轨道矩阵

适用于各区域分块粗细不同、但需要共享对齐边界的架构图。优先使用规范 JSON；薄 HTML 是等价输入。列数、列 ID、业务分区和跨度由原文决定，不要求中央七列。

## 先表达结构，再选主题

使用 `kind:"matrix"` 和 `template:"shared-tracks"`（后者可省略）。公共 `rows` 和每格的 `start/span` 表达对齐，程序根据内容统一计算行高。各列可以按不同粒度分组，例如六条轨道分别按 3+3、2+2+2 和 1+1+1+1+1+1 覆盖。轨道不要求等高，作者不写像素尺寸。

通过 `--base_palette '{"style_preset":"red-gold-compact-v1"}'` 或 `blue-compact-v1` 选择主题，也可在 JSON 根对象保存 `presentation_preset`。两处同时出现须一致，不与 `primary` 混用。先检查后端 `authoring.presentation_presets` 和 `authoring.style_roles`；旧后端可能只支持联合生成使用这两个主题，不能据此推断矩阵也支持。

`style_role` 可放在矩阵根、列、格或嵌套节点上：`frame`（框架）、`foundation`（基础）、`planning`（统筹）、`business`（业务）。可见内容继承最近角色，子项可显式覆盖；完全未标注的内容用 `business`。标题和可选通栏页脚使用框架色，布局包装保持透明。业务 ID 与颜色无关。结构 `role` 仍只有 `section/group/entity/layout`，不要与 `style_role` 混淆。

同一布局可用红金或蓝色主题，主题不规定列数或业务槽位。共享轨道跨行格的高度受对齐约束，不套用联合生成叶格的 64 px 纵向空白上限。

下面三列只是示例，可按需求增删列、行和分区，没有必需的中央列、基础/规划槽位或 footer。

```json
{
  "kind":"matrix", "template":"shared-tracks", "presentation_preset":"red-gold-compact-v1",
  "title":"研发交付协同", "rows":6,
  "columns":[
    {"id":"governance","title":"治理目标","style_role":"frame","cells":[
      {"id":"direction","title":"统一方向","span":3},
      {"id":"quality","title":"质量闭环","span":3}
    ]},
    {"id":"capabilities","title":"协作能力","style_role":"foundation","cells":[
      {"id":"common_services","title":"公共服务","span":2,"role":"group","columns":2,"items":[
        {"id":"standards","title":"标准规则"},{"id":"catalog","title":"产品目录"}
      ]},
      {"id":"coordination","title":"资源统筹","span":2,"style_role":"planning"},
      {"id":"delivery","title":"交付活动","span":2,"style_role":"business"}
    ]},
    {"id":"teams","title":"职责组织","style_role":"business","cells":[
      {"title":"决策委员会"},{"title":"规划办公室"},{"title":"研发团队"},
      {"title":"交付中心"},{"title":"质量团队"},{"title":"服务团队"}
    ]}
  ]
}
```

## 对齐与编辑规则

- `rows` 创建时可用正整数；规范模型返回稳定行 ID 列表，编辑时保留 ID。`start` 从 1 开始，省略时接在上一格之后；`span` 默认 1。
- 每列完整覆盖所有公共行，不允许空洞、重叠或越界。增删公共行时同步修改各列覆盖范围，不用虚构业务节点掩盖缺口。
- 格内用 `items`、`columns`、`flow` 组织嵌套分区。业务名称、列数和分组数量不固定。
- `footer` 可选，表达真实存在的通栏内容；普通业务内容也可按需求放在一列中，不按名称强制搬去页脚。
- 从返回的规范模型继续编辑，保留已有 ID。程序按 ID 恢复省略的主题/角色；新增节点继承父级角色，也可显式设置。显式更换整图主题仍需新会话。
- 当前支持列内跨行和格内嵌套；任意跨列合并、二维拼块和完整 CSS Grid 尚不支持。

## 薄 HTML 对应语法

JSON 的 `presentation_preset/style_role/start/span` 分别对应 `data-presentation-preset/data-style-role/data-start/data-span`：

```html
<main data-kind="matrix" data-title="组织职责" data-rows="3" data-presentation-preset="blue-compact-v1">
  <section id="department" data-title="部门" data-style-role="frame">
    <p id="headquarters" data-span="2">总部</p>
    <p id="branch">分部</p>
  </section>
  <section id="activities" data-title="活动" data-style-role="business">
    <p id="schedule" data-style-role="planning">规划</p>
    <p id="execute">执行</p>
    <p id="review">复核</p>
  </section>
</main>
```

没有版本化主题的普通矩阵仍可使用单主色和既有样式，不传 `style_role`。

## 中车式结构作为普通示例

参见[中车式采购协同示例](enterprise-central-example.md)和配套 JSON：使用相同共享轨道、跨行、嵌套和角色主题；七列只是示例数据，可增删或重排。

新图不再使用 `enterprise-central-v1` / `crrc-central-v1`。已有受管 CW/D2 源码可通过会话导入/恢复读取，后端单向转换成共享轨道规范模型，随后按通用规则编辑和重新渲染；原图的固定列宽不再保留。旧 JSON/HTML 或原型输入须改成新协议，或从原会话导出转换后的规范 JSON，不能只换名称而遗漏显式角色。失败不会覆盖旧图。
