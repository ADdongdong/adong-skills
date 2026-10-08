---
name: bank-statement-check-forp
display_name: "【forp】银行流水核查"
description: "【forp 对照测试版】对IPO/再融资/审计项目的银行流水执行四步确定性核查：①多银行流水格式标准化 ②关联方交易识别 ③异常交易筛查 ④资金闭环核查。从海量流水定位可疑交易、发现异常模式与资金回流线索，输出标准化流水、风险打标、异常清单与核查结论，为项目组访谈追问提供方向。AI 仅做'雷达'不做'判决书'，不做最终定性。中途禁止向用户输出任何文字；仅在 json_to_excel 返回后按 reference.md 回复。"
enable: true
ui_visible: 0
category: tools
long_task: true
metadata:
  keywords:
    - "银行流水"
    - "流水核查"
    - "流水分析"
    - "流水筛查"
    - "关联方交易"
    - "关联方往来"
    - "异常交易"
    - "资金闭环"
    - "资金回流"
    - "体外循环"
    - "大额取现"
    - "深夜交易"
    - "往来款"
    - "敏感摘要"
    - "高频往来"
  llm_params:
    temperature: 0.2
    max_tokens: 16384
    use_history: true
    max_history_turns: 6
  commands:
    - name: file_to_json
      description: 【第一步·中间步骤·静默·禁止 finish】识别一个或多个 PDF，合并为一份识别结果返回。本脚本返回后任务未完成；下一轮 ReAct 禁止 action=finish，必须整理后调用 json_to_excel；禁止把识别结果写入 result
      trigger_keywords: ["识别PDF","PDF转JSON","提取PDF表格","PDF内容识别","提取表格","识别表格","PDF表格提取","提取PDF内容","解析PDF","银行流水","交易明细","批量识别","多个PDF","流水核查","流水分析"]
      script: python3 scripts/file_to_json.py
      input_schema:
        file_id:
          required: false
          type: string
          desc: 单个 PDF 文件ID。不传则自动识别 context.files 中的所有 PDF
        file_ids:
          required: false
          type: array
          desc: 多个 PDF 文件ID列表。不传则自动识别所有 PDF 附件；多个 PDF 的识别结果会合并为一份返回

    - name: json_to_excel
      description: 【第三步·收尾脚本·必须执行】将整理好的交易明细作为 input.tables_json 传入（禁止放进 thought/result）。脚本内四步核查后生成 Excel 并写盘，直接把 file_path 交给 LLM（不上传、无 download_url）。仅本脚本返回后才允许 action=finish 并按 reference.md 回复
      trigger_keywords: ["生成Excel","转成Excel","导出Excel","JSON转Excel","流水核查","关联方","异常筛查","资金闭环","生成xlsx"]
      script: python3 scripts/json_to_excel.py
      input_schema:
        tables_json:
          required: true
          type: string
          desc: 【必填·仅放在本命令 input】标准9列交易明细 JSON 字符串。格式 {"headers":["交易日期","交易时间","摘要","交易金额","对方账号","对方户名","当前账户","当前户名","银行"],"rows":[["...",...],...]}。严禁写入 thought/result/finish
        related_parties:
          required: false
          type: string
          desc: 关联方清单 JSON。如 [{"name":"张三","type":"实控人","aliases":["张*"]},{"name":"辰源贸易","type":"关联企业"}]；也可传名称数组。缺省则跳过关联方匹配（仍做大额中风险与异常筛查）
        config:
          required: false
          type: string
          desc: 可选阈值 JSON。默认：取现50万、高频往来100万/7天、深夜23:00-05:00、敏感词借款/往来款/往来/暂付、大额支付100万、追踪窗口7天
        issuer_names:
          required: false
          type: string
          desc: 发行人户名（字符串或 JSON 数组）。缺省则按当前户名出现最多者推断
        file_name:
          required: false
          type: string
          desc: Excel 文件名，默认"银行流水核查结果.xlsx"
---

# 银行流水核查

对银行流水执行四步确定性核查：①格式标准化 ②关联方识别 ③异常筛查 ④资金闭环。输出多 sheet Excel（标准化流水 / 关联方打标 / 异常筛查 / 资金闭环 / 核查结论摘要）。

## ReAct 动作硬规则（最高优先级 · 解决 JSON 解析失败）

本技能在 ReAct 循环中运行。每一轮响应必须是**合法且短小的动作 JSON**，否则会触发「LLM 响应 JSON 解析失败」。

| 时机 | 正确 action | 严禁 |
|------|-------------|------|
| 开始 / 未识别 PDF | 调用命令 `file_to_json` | `action=finish` |
| `file_to_json` 已返回 | 内部整理后**立即**调用命令 `json_to_excel`，`tables_json` 只放在命令 **input** | `action=finish`；把 JSON 放进 `thought`/`result` |
| `json_to_excel` 已返回 | 才允许 `action=finish`，`result` 仅填 reference.md 模板（取自脚本 `data`） | 未调用 `json_to_excel` 就 finish |

**硬性约束（违反即错误）：**
1. `file_to_json` 返回后：**禁止** `action=finish`
2. 整理好的流水 JSON：**只能**作为 `json_to_excel` 的 `input.tables_json`，**禁止**写入 `thought` / `result` / 用户可见正文
3. `thought` 只写一两句计划（如「整理完毕，调用 json_to_excel」），**禁止**粘贴 headers/rows 或 markdown 代码块
4. 禁止在 `result` 里输出「已识别 N 条」「整理后的 JSON 如下」——这会导致外层 JSON 被截断/转义失败

**错误示范（日志中的真实失败）：**
```json
{"thought": "file_to_json已返回…开始整理…", "action": "finish", "result": "已识别42条…\n```json\n{\"headers\":...}```"}
```
→ 外层 JSON 解析失败，任务中断。

**正确示范：**
```json
{"thought": "已整理为标准9列，立即调用 json_to_excel", "action": "json_to_excel", "input": {"tables_json": "{\"headers\":[...],\"rows\":[...]}"}}
```
（字段名以平台实际 ReAct schema 为准；要点是：**调用命令**，且 `tables_json` 在命令入参里。）

## 静默执行硬规则

**在成功调用 `json_to_excel` 并拿到返回结果之前，禁止向用户输出任何内容。**

包括但不限于：
- ❌「好的，我已收到您上传的…」「已识别出 N 条…」「正在整理…」「请稍等…」
- ❌ 进度说明、确认话术、流程预告、JSON 预览、中间结果摘要
- ❌ 套用 `reference.md` 最终模板，或编造下载链接
- ❌ ReAct `action=finish`（等同于向用户收尾）

**允许的行为**：仅静默调用脚本、静默整理 JSON、静默传入 `json_to_excel`。  
**唯一允许的用户可见回复**：`json_to_excel` 返回之后，且必须严格按 `reference.md` 规则输出。

> 中途任何面向用户的文字或过早 finish 都视为错误。

## 完成判定（Completion Gate）

| 阶段 | 脚本 | 是否算完成 | 能否向用户输出 | 能否按 reference.md 输出 |
|------|------|------------|----------------|--------------------------|
| ① | `file_to_json` 已返回 | **否** | **禁止任何文字** | **禁止** |
| ② | LLM 整理完 JSON | **否** | **禁止任何文字** | **禁止**。必须立刻调用 `json_to_excel` |
| ③ | `json_to_excel` 已返回 | **是（可收尾）** | **允许** | **允许**。仅此时按 `reference.md` 输出 |

**硬性要求**：`file_to_json` 返回任何结构（含 `success=true`、`result_json`、识别文本）都**不代表任务结束**。未将参数传入并执行 `json_to_excel` 之前，禁止任何用户可见回复，禁止 `action=finish`。

## 强制执行顺序（不可跳步、不可颠倒）

```
① 执行脚本 file_to_json     → 静默；禁止 finish / 用户可见文字
② LLM 在对话中整理          → 静默映射为标准 9 列 JSON；禁止把 JSON 写入 thought/result
③ 执行脚本 json_to_excel    → tables_json 只放命令 input；四步核查 → Excel 写盘 → 直接交给 LLM
④ action=finish + reference → 仅在 json_to_excel 返回后；唯一允许的用户回复
```

**严禁**：
- 跳过 `file_to_json` 直接整理
- `file_to_json` 返回后 `action=finish`、向用户说话或按 `reference.md` 输出
- 把整理后的 JSON 放进 `thought` / `result` / markdown 代码块（会导致 ReAct JSON 解析失败）
- LLM 整理过程中或整理完成后向用户说话
- 跳过 `json_to_excel` 直接结束
- 用 `result_json` / 识别文本代替 `file_path`
- 上传平台或自行拼接 `/api/.../download` 链接
- 使用非标准列名的 JSON（如「收支金额」「对手方」「银行名称」「账户名称」）作为 `tables_json`

## 执行流程 (Core Workflow)

### 第一步：执行脚本 `file_to_json`（必须 · 静默中间步骤）

1. **静默**调用 `file_to_json` 脚本，定位并识别一个或多个 PDF
2. 标准型 → pdfplumber 提取；图片型/失败 → OCR 接口
3. 多 PDF 结果合并为一份，从返回的 `data.result_json` / `data.text` 读取
4. **本步结束后禁止 `action=finish`、禁止向用户输出任何文字**；禁止进度描述；立即进入第二步

### 第二步：LLM 整理交易明细（对话层，必须 · 静默中间步骤）

5. **静默**读取第一步脚本返回的合并识别结果（只在内部使用，不要回显）
6. 映射为标准 9 列（支持别名；**输出 headers 必须用下列标准列名，不得用别名**）：

| 标准列名 | 常见别名 |
|----------|----------|
| 交易日期 | 交易日、日期、记账日期、发生日期、入账日期 |
| 交易时间 | 时间、记账时间、发生时间、交易时刻、入账时间 |
| 摘要 | 用途、备注、说明、交易摘要、附言 |
| 交易金额 | 金额、发生额、借方金额、贷方金额、收入、支出、收支金额 |
| 对方账号 | 对方账户、对手账号、收款账号、付款账号、对方卡号 |
| 对方户名 | 对方名称、对手户名、收款人、付款人、对方姓名、收款户名、对手方 |
| 当前账户 | 账号、本方账号、账户、卡号、账户号码、银行账号 |
| 当前户名 | 户名、本方户名、账户名称、本方名称、账户名 |
| 银行 | 开户行、开户银行、银行名称、所属银行、银行名、本方银行、账户银行 |

7. 整理为以下 JSON 格式（**仅作为 `json_to_excel` 的 input.tables_json；禁止写入 thought/result/用户可见正文**）：

```json
{
  "headers": ["交易日期", "交易时间", "摘要", "交易金额", "对方账号", "对方户名", "当前账户", "当前户名", "银行"],
  "rows": [
    ["2024-01-01", "10:30:00", "转账", "1000.00", "6222****1234", "张三", "6217****5678", "李四", "工商银行"]
  ]
}
```

**交易金额正负规则（整理时必须遵守）：**
- 原文已有正负号 / 借贷标志 / 收入支出分列 → **原样保留**，不要改符号
- 原文金额**没有正负号**（纯绝对值）时，**必须根据摘要推断并写入带符号金额**：
  - **正数（收入）**：摘要含「货款」「回款」「收款」「销售收入」「销售款」「到账款」等
  - **负数（支出）**：摘要含「材料款」「采购款」「材料费」「采购」「付货款」「支付货款」等
  - 示例：摘要「货款」+ 金额 `50000` → 写成 `50000.00`；摘要「材料款」+ 金额 `30000` → 写成 `-30000.00`
- 摘要无法判断时保持原绝对值，交给脚本按默认规则处理

若用户提供了关联方清单，一并整理为 `related_parties` 参数传入第三步。

8. **整理完成后禁止 finish / 禁止向用户输出**；必须在同一决策中调用 `json_to_excel`，把上述 JSON 字符串放入命令入参 `tables_json`

### 第三步：执行脚本 `json_to_excel`（必须 · 收尾前置）

9. **必须调用** `json_to_excel` 脚本（调用前禁止 `action=finish`）
10. 将第二步整理好的 JSON **作为命令 input 的 `tables_json` 传入**（可选 `related_parties` / `config` / `issuer_names`）；**不要**放进 `thought` 或 `result`
11. 脚本**先对内容做四步核查处理，再生成 Excel 并写盘**（禁止跳过处理直接出表；**禁止上传平台**）：

| 步骤 | 处理 | 产出 |
|------|------|------|
| 3.1 标准化 | 日期→YYYY-MM-DD；无正负时按摘要推断收支（货款/回款→收入，材料款/采购款→支出）；收支分列；对手方名称清理 | sheet「标准化流水」 |
| 3.2 关联方 | 匹配关联方清单；打标是否关联方/风险等级；高亮 | sheet「关联方打标」 |
| 3.3 异常筛查 | R1大额取现 / R2高频往来 / R3深夜交易 / R4敏感摘要 | sheet「异常筛查」 |
| 3.4 资金闭环 | 大额支付追踪、回流/体外循环线索 | sheet「资金闭环」+「核查结论摘要」 |

12. 返回完整 `data` 统计字段（`bank_count` / `total_count` / `related_*` / `r1_count`…`r4_count` / `loop_*` / `follow_up` / `file_path` / `file_name` 等）；Excel 以 `file_path` 直接交给 LLM

### 第四步：按 reference.md 输出（仅 json_to_excel 之后 · 唯一用户回复）

13. **仅当 `json_to_excel` 已执行并返回后**，才读取并执行 `reference.md`
14. **必须按 reference.md 规则 1**：先输出一至五节核查内容（字段全部取自 `data`，禁止编造），再交付 Excel
15. 从 `data.file_path` 和 `data.file_name` 取值；**必须逐字符原样复制 `file_path`**
16. 将 `file_path` 对应的 Excel 文件直接交付给用户（环境若已展示附件/工件则直接引用，禁止再上传或拼接 download 链接）
17. AI 仅做「雷达」不做「判决书」，不做最终定性

## 约束条件（Guardrails）

- **必须先执行 file_to_json，再 LLM 整理，再执行 json_to_excel**，缺一不可；未跑完 `json_to_excel` 不算完成
- **`file_to_json` 返回后禁止 `action=finish`**；必须继续调用 `json_to_excel`
- **`tables_json` 只能出现在 `json_to_excel` 命令 input**，禁止出现在 thought/result（否则 ReAct JSON 解析失败）
- **`file_to_json` 返回后 / LLM 整理中 / 调用 `json_to_excel` 前：禁止向用户输出任何文字**
- 禁止进度描述、确认话术、「请稍等」、JSON 预览等中间回复
- 只基于原始识别数据整理，严禁编造交易记录
- `tables_json` 必须是标准 9 列 headers/rows JSON；禁止用「收支金额/对手方/银行名称/账户名称」等非标准列名
- json_to_excel 内必须完成四步核查后再写盘出表，禁止跳过处理，禁止上传平台
- 最终回复必须逐字符原样使用 `data.file_path` / `data.file_name`
- **严禁**使用 `/api/v1/forpclaw/download/`、`/api/storage/download/`、`https://` 或自行拼接的下载路径
- AI 仅做「雷达」不做「判决书」，不做最终定性

## 输出规范（Output Rules）

- **触发时机**：仅在 `json_to_excel` 执行完毕并返回后（此时才允许 `action=finish`）
- **禁止时机**：`file_to_json` 返回后、LLM 整理过程中、调用 `json_to_excel` 之前——此时零用户可见输出、禁止 finish
- 细则见 `reference.md`
