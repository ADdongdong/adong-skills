# 层级卡片

用于分区架构、能力清单、嵌套网格，例如 AIOps 与可信数据空间。节点标题应保留用户术语和职责；没有真实关系时不造边。

薄 HTML 示例：

```html
<main data-kind="cards" data-template="stack-arch" data-template-version="2" data-title="平台能力" data-columns="2">
  <section id="business" data-title="业务能力">
    <p>订单管理</p>
    <p>库存管理</p>
  </section>
  <section id="technical" data-title="技术能力">
    <p>事件处理</p>
    <p>规则引擎</p>
  </section>
  <a data-from="business" data-to="technical">调用</a>
</main>
```

等价 JSON（实际调用只选一种）：

```json
{"kind":"cards","template":"stack-arch","template_version":2,"title":"平台能力","columns":2,"items":[{"id":"business","title":"业务能力","items":["订单管理","库存管理"]},{"id":"technical","title":"技术能力","items":["事件处理","规则引擎"]}],"edges":[{"from":"business","to":"technical","label":"调用"}]}
```

- `main` 是唯一根；`section` 表示分区；`p` 表示叶节点；根下的 `a` 表示真实关系，不是网页链接。
- 新建使用模板版本 2，先确认 `/capabilities` 中该模板的 `versions` 包含 2。旧规范模型保留其 `template_version`；版本 1 缺省单列，不能静默升级旧图。
- v2 根缺省单列保留纵向分层，内部缺省或 `columns: "auto"` / `data-columns="auto"` 由渲染器按测量尺寸自动选列；不需要 LLM 计算行列。需要根也自动排布时可显式设置根为 auto。
- 只有用户明确要求或已确认的结构约束才写整数 `columns`；显式 1 同样会保留。`flow` 为 `row` 或 `column`，指定阅读填充顺序，不等于固定列数。带真实连线等受保护区域不会强行改成多列。
- `data-template` / `template` 支持 `stack-arch`（默认）和 `trusted-space`；模板负责配色层次与布局尺寸。
- 关系端点使用显式唯一 `id`，标识符使用英文字母或下划线起始、后接字母数字下划线。
- 可用 `data-role` / `role` 指定 `section`、`group`、`entity`、`layout`；纯排版包装使用 `layout`，不能作为业务边端点。不靠嵌套深度表达业务身份。
- 不写 CSS、`style`、坐标、宽高、字体或 D2 类。格式外的标签、属性会被拒绝。
- 修改时读取保存的规范 JSON，保留 ID，而不是从原始字符串列表重新生成。
