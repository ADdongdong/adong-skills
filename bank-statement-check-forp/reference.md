# 银行流水核查 输出规范

> **何时使用本文件**：仅在 `json_to_excel` 脚本已执行、参数已传入、并返回结果之后。  
> **何时禁止使用**：`file_to_json` 刚返回时、LLM 正在整理 JSON 时、尚未调用 `json_to_excel` 时。  
> **中途规则**：上述禁止时段内，**禁止向用户输出任何文字**，**禁止 ReAct `action=finish`**，只能静默继续调用脚本。

## 完整流程与输出门禁

```
① file_to_json（脚本）          ← 静默；禁止 finish / 任何用户可见文字
→ ② LLM 整理 JSON（对话）       ← 静默；JSON 禁止写入 thought/result
→ ③ json_to_excel（脚本）       ← tables_json 只放命令 input；四步核查 → Excel 写盘 → 直接交给 LLM
→ ④ action=finish + 本文件规则   ← 唯一允许的用户回复；先一至五节，再交付 Excel 文件
```

**完成判定**：只有将参数传入 `json_to_excel` 并拿到返回后，才允许 `action=finish` 并进入下方规则 1 / 5。  
`file_to_json` 的任何成功返回都**不等于**任务完成，也**不得**触发任何用户可见输出或 finish。

---

## 中间步骤说明（全程静默 · 非最终输出）

### 规则 0 — file_to_json 返回后（禁止任何回复 / 禁止 finish）

**必须**：静默继续 LLM 整理 → 调用 `json_to_excel`。  
**严禁**：
- ReAct `action=finish`（这是日志中「JSON 解析失败 / 任务中断」的主因）
- 向用户输出任何文字（含「已收到文件」「已识别 N 条」「正在整理」「请稍等」）
- 把交易明细 JSON 写入 `thought` / `result` / markdown 代码块
- 套用规则 1 / 5
- 声称核查已完成

### 规则 0b — LLM 整理过程中及完成后（禁止任何回复）

**必须**：整理完成后立刻将标准 9 列 JSON **仅作为** `json_to_excel` 的 `input.tables_json` 传入并调用该命令。  
**严禁**：
- 整理前/中/后 `action=finish`
- 整理前/中/后向用户描述进度或展示 JSON
- 把 headers/rows 粘贴进 `thought`/`result`（会导致外层 ReAct JSON 解析失败）
- 使用非标准列名（如「收支金额」「对手方」「银行名称」「账户名称」）作为 `tables_json`

### 规则 0c — 调用 json_to_excel 之前（总禁令）

在 `json_to_excel` 尚未返回之前：
- **零用户可见输出**
- **禁止 `action=finish`**
- **只允许**：工具/脚本调用与内部整理；`tables_json` 只出现在命令 input
- **唯一出口**：`json_to_excel` 返回后才允许 finish，并进入规则 1 / 5

---

## 最终输出规则（仅 json_to_excel 之后）

### data 字段说明（核查成功时）

脚本返回的 `data` 包含以下字段（**LLM 按此结构取值，不得编造不存在的字段**）：

| 字段 | 类型 | 说明 |
|---|---|---|
| `bank_count` | int | 涉及银行数量 |
| `total_count` | int | 标准化后流水总笔数 |
| `related_count` | int | 命中关联方往来的笔数 |
| `related_high` | int | 其中高风险关联方往来笔数 |
| `top_related` | list[str] | 主要关联方（名称+笔数），最多 5 个 |
| `anomaly_count` | int | 命中异常交易的笔数 |
| `r1_count` | int | R1 大额取现命中笔数 |
| `r2_count` | int | R2 高频往来命中笔数 |
| `r3_count` | int | R3 深夜交易命中笔数 |
| `r4_count` | int | R4 敏感摘要命中笔数 |
| `loop_count` | int | 可疑资金链条数量 |
| `loop_details` | list[str] | 各资金链条描述 |
| `follow_up` | list[str] | 核查线索与追问方向 |
| `file_name` | str | Excel 文件名 |
| `file_path` | str | Excel 本地绝对路径（脚本已写盘，直接交给 LLM） |
| `file_size` | int | 文件大小（bytes） |
| `mime_type` | str | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `pdf_convert_failures` | list[str] | 仅部分 PDF 流水转换失败时存在 |
| `file_errors` | list[str] | 仅个别流水/关联方清单文件读取失败时存在 |

列表字段展示规则：
- `top_related`：用顿号连接，如 `张三（3笔）、辰源贸易（2笔)`；空列表写 `无`
- `loop_details`：逐条换行展示；空列表写 `无`
- `follow_up`：逐条换行，前加 `- `；空列表写 `无`
- 若存在 `pdf_convert_failures` / `file_errors`，在「一、数据概况」末尾追加告警子弹

---

## 规则 1 — 核查 Excel 成功（json_to_excel 返回 success = true 且 file_path 非空）

**前置条件**：本轮已成功执行 `json_to_excel`（已传入 `tables_json` 等参数并拿到返回）。  
**取值来源**：下列占位符全部取自 `json_to_excel` 返回的 `data`，禁止编造、禁止从 `file_to_json` 取值。

> **排版硬性规则（必须遵守，违反即错误）：**
>
> - 下列标题/句子**各自独占新段落**，其正上方必须先输出一个空行（即连续两个换行 `\n\n`），再用下一行写标题本身：
>   - `**二、关联方交易识别**`
>   - `**三、异常交易筛查**`
>   - `**四、资金闭环核查**`
>   - `**五、核查线索与追问方向**`
>   - `AI 仅做「雷达」不做「判决书」…`
> - 模板中的 `<br>` **必须原样保留并输出**（用于强制换行；禁止删掉或改成空格）
> - **严禁**把上一节末尾与下一节标题粘在同一段 / 同一行（如 `…账户名称**二、关联方…`）

**固定回复模板（一至五节在 Excel 交付上方；`<br>` 必须原样输出）：**

---

银行流水核查完成。

**一、数据概况**

- 核查银行数：{bank_count} 家
- 流水总笔数：{total_count} 笔
- 标准化后字段：交易日期、收支金额、对手方、摘要、银行名称、账户名称

<br>

**二、关联方交易识别**

- 命中关联方往来：{related_count} 笔（其中高风险 {related_high} 笔）
- 主要关联方：{top_related}

<br>

**三、异常交易筛查**

- 命中异常交易：{anomaly_count} 笔
  - R1 大额取现：{r1_count} 笔
  - R2 高频往来：{r2_count} 笔
  - R3 深夜交易：{r3_count} 笔
  - R4 敏感摘要：{r4_count} 笔

<br>

**四、资金闭环核查**

- 可疑资金链条：{loop_count} 条

{loop_details}

<br>

**五、核查线索与追问方向**

{follow_up}

<br>

AI 仅做「雷达」不做「判决书」，不做最终定性；请项目组据此确定访谈追问方向。

核查底稿已生成：`{file_name}`  
文件路径：`{file_path}`

---

> **Excel 交付硬性规则（必须遵守，违反即错误）：**
>
> - 必须**逐字符原样**使用 `json_to_excel` 返回的 `data.file_path` 与 `data.file_name`
> - Excel 已由脚本写盘并直接交给 LLM；若运行环境已将文件作为附件/工件展示，直接交付即可
> - **严禁**在未执行 `json_to_excel` 时输出本模板
> - **严禁**在调用 `json_to_excel` 前输出任何中间话术
> - **严禁**编造 `data` 中不存在的统计字段

### 错误示例（严禁）

❌ `file_to_json` 后 `action=finish`，并在 `result` 里塞「已识别…」+ markdown JSON（→ ReAct JSON 解析失败）  
❌ `file_to_json` 返回后输出「已收到文件 / 正在整理 / 请稍等」  
❌ LLM 整理中输出进度或 JSON 预览  
❌ 未调用 `json_to_excel` 就输出「核查完成」或编造文件路径  
❌ 自行编造 R1/R2 笔数或关联方名单  
❌ `tables_json` 使用「收支金额」「对手方」等非标准列名  
❌ 章节粘连：`…银行名称、账户名称**二、关联方交易识别**`（漏空行 / 漏 `<br>`）

### 正确示例

✅ 中途零文字 / 禁止 finish → 调用 `json_to_excel`（`tables_json` 仅在命令 input）→ 返回后才 `action=finish` 并输出本模板  
✅ 使用返回的真实 `file_path`，例如 `/Users/.../银行流水核查结果.xlsx`  
✅ 每节之间输出 `<br>` 再写下一节标题，标题不与上节末尾粘连

## 规则 3 — file_to_json 识别成功（中间步骤 · 静默）

- **禁止**向用户输出任何文字（含识别笔数、文件数、进度）
- **不要**在此步骤结束；**不要**套用规则 1；**不要**编造文件路径
- **必须**静默进入 LLM 整理并调用 `json_to_excel`

## 规则 4 — 识别失败（file_to_json success = false）

仅当 `file_to_json` 明确失败且无法继续时，才允许向用户输出：

---

识别失败：{message}

---

## 规则 5 — 核查 / 生成 Excel 失败（json_to_excel success = false）

**前置条件**：已执行 `json_to_excel`。

---

银行流水核查失败：{message}

---

## 通用规则

- **输出门禁**：未将参数传入并执行 `json_to_excel` 前，禁止使用规则 1 / 5，禁止任何中间话术，禁止 `action=finish`
- **静默门禁**：`file_to_json` → LLM 整理 → 调用 `json_to_excel` 全程零用户可见输出
- **ReAct 门禁**：`tables_json` 只能放在 `json_to_excel` 命令 input；禁止放进 thought/result（避免 JSON 解析失败）
- `json_to_excel` 成功后，**必须按规则 1**：先一至五节，再交付 `file_path` 对应 Excel
- 所有统计与列表字段只能来自 `json_to_excel` 的 `data`，禁止编造
- `file_path` / `file_name` 只能来自 `json_to_excel` 的 `data`
- AI 仅做「雷达」不做「判决书」，不做最终定性
