---
name: mx-finance-data
description: 基于东方财富数据库，支持自然语言查询一个或多个明确标的的金融数据，覆盖A港美、基金、债券等资产的实时行情、公司信息、估值和财务报表，返回 xlsx 与 Markdown 文件。适用于按已知标的查指标；需要按条件筛选、排序或推荐多只标的时不要使用，改用 mx-stocks-screener。Natural language financial data lookup for known entities across stocks, funds and bonds. Do not use for screening, ranking or recommending multiple assets.
version: 1.2.0
category: investment-finance
author: 东方财富
license: proprietary
agent_created: true
---

# 金融数据查询

## 功能范围

### 1. 支持查询的对象范围

* 股票（A 股、港股、美股）
* 板块、指数、股东
* 企业发行人、债券、非上市公司
* 股票市场、基金市场、债券市场

### 2. 支持查询的数据类型

支持查询以下类型的结构化数据：

* **实时行情**（现价、涨跌幅、盘口数据等）
* **量化数据**（技术指标、资金流向等）
* **报表数据**（营收、净利润、财务比率等）

### 3. 查询方式与处理逻辑

统一使用 `--query` 传入自然语言问句（包含实体与指标），并使用 `--indicators` 传入从问句中提取的金融指标等关键信息。Skill 会先对 query 做实体识别，再按识别结果选择查数路径：

* **识别实体数 ≤ 5**：直接查数
* **识别实体数 > 5**：批量查数，最多处理识别结果中的前 **500** 个有效实体，如需大于500个实体，可分批多次调用

注意：当用户问句中只包含代词，需结合上下文或者提供文件读取所有实体名称，一并输入query。

#### `--indicators` 参数说明

调用本 Skill 前，需根据 `--query` 从用户问句中提取需要查询的**金融指标**（或指标组），填入 `--indicators`：

* 只填指标和时间范围等除实体外所有有效信息，不含实体名称等修饰语。
* 多个指标用用户原话拼接，如 `市盈率(动)和总市值`、`涨跌幅`、`营收、毛利、净利`。
* **不要在 `--indicators` 里重复写实体**。
* 提取 query 中除实体名称外的指标词和时间词，按用户原话用逗号拼接，**不得改写指标名称**。

> **示例**  
> 用户问「查询贵州茅台、五粮液近一年营收」  
> → `--query "查询贵州茅台、五粮液近一年营收" --indicators "近一年营收"`

> 用户问「这批股票的涨跌幅是多少」或列出 6 只以上股票  
> → `--query "查询 A、B、C、D、E、F 六只股票的涨跌幅、pe、市值" --indicators "涨跌幅、pe、市值"`

### 4. 输出结果

Skill 执行后会输出两个文件：

- **Excel（.xlsx）**：多 sheet 结构化数据表，每个实体/指标组合对应一个 sheet
- **Markdown（.md）**：与 Excel 内容一致的 Markdown 表格，按 sheet 分二级标题

------

## 前提条件

### 1. 授权（已内联，无需单独跑）

本 Skill 依赖 `EM_API_KEY`。优先复用已缓存凭据：先从平台私有的跨会话持久存储读取 `EM_API_KEY`，可用时仅将其注入当前业务脚本进程并直接执行，不要重复调用 `mx_get_user_api_key`。若平台私有存储不可读、未提供或没有凭据，再安全检查本机私有缓存 `~/.mx-skills/em_api_key`（只能检查是否存在、长度是否大于 0，不能 `cat` 或打印真实值）；若存在有效凭据，直接运行本 Skill 的业务脚本，脚本会自动读取该文件。

仅当平台私有存储与本机缓存都缺失或已确认失效时，才调用东方财富妙想 MCP 的 `mx_get_user_api_key` 工具获取当前 OAuth2 登录用户的东方财富 API Key。若成功取得 `apiKey`，优先保存为平台私有的跨会话 `EM_API_KEY`；同时必须把完整值写入 `~/.mx-skills/em_api_key`，作为本 Skill 业务脚本可直接读取的本机私有缓存（权限尽量设为仅当前用户可读写）。随后仅注入当前业务脚本进程并直接执行本 Skill 的业务脚本，不要再触发 skill 层面的二次授权、扫码授权或 `auth.py ensure`。

仅当 `mx_get_user_api_key` 不可用、调用失败、未返回有效 `apiKey`，或当前运行环境没有可用的东方财富妙想 MCP 时，才回退到 skill 内置授权流程。内置授权检查已内联到业务脚本，**直接执行业务脚本，不要先单独运行 `auth.py ensure`**，也不要把内置授权做成默认独立前置步骤；不要因为环境里没有 `EM_API_KEY` 就跳过本 Skill。回退时脚本按 `EM_API_KEY` 环境变量、`~/.mx-skills/em_api_key` 文件的顺序读取凭据，不再使用内置兜底 key。

处理 `apiKey` 时不要把真实值输出到 stdout/stderr、日志、命令回显或对话正文中；不要使用 `echo`、`cat`、`env | grep`、或把真实 key 直接拼进 shell 命令行的方式检查或传递凭据。需要确认凭据存在时，只检查文件是否存在、长度是否大于 0、或输出脱敏后的前后缀。执行查询或生成任务时优先使用平台私有存储注入当前业务脚本进程；没有平台凭据时，再让脚本从 `~/.mx-skills/em_api_key` 读取。确需进程级注入时，使用工具/运行时的环境变量能力，不要把真实 key 写进 shell 命令字符串。

| 退出码 | 含义 | agent 动作 |
| --- | --- | --- |
| `0` | 成功 | 读末尾 `文件:` / `Markdown:` 行 |
| `10` | 需用户授权 | 见下文 need_auth 处理 |
| `2` | 网络/业务错误 | 检查网络后最多重试 1 次；持续失败联系客服 400-620-1818 |
| `1` | 参数错误 | 不重试，向用户报错 |

#### need_auth（退出码 `10`）处理

stdout 会打印带标签行：

```
need_auth: true
authUrl: <以实际返回为准>
apiKeyUrl: <以实际返回为准>
```


授权、凭据持久化及 401 失效处理必须遵循 [授权协议](references/auth_protocol.md)。

### 2. Shell 环境

**macOS：**
```bash
source ~/.zshrc
```

**Linux：**
```bash
source ~/.bashrc
```

### 3. 安装依赖

```bash
pip3 install -r requirements.txt
```

## 快速开始

在工作目录下执行：

```bash
python3 scripts/get_data.py --query "贵州茅台近期走势如何" --indicators "近期走势"
```

多实体示例：

```bash
python3 scripts/get_data.py --query "查询贵州茅台、五粮液、宁德时代、比亚迪、隆基绿能、中芯国际的市盈率(动)" --indicators "市盈率(动)"
```

参数说明：

| 参数 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `--query` | 是 | - | 自然语言查询问句，需包含所有查询实体名称|
| `--indicators` | 是 | - | 从 query 中提取的金融指标、时间范围等关键信息|

------

### 输出示例

**直接查数：**

```
识别实体数: 1
查数模式: 直接查数
返回实体数: 1
文件: /path/to/miaoxiang/mx_finance_data/mx_finance_data_9535fe18.xlsx
Markdown: /path/to/miaoxiang/mx_finance_data/mx_finance_data_9535fe18.md
表格行数: 42
```

**多实体查数：**

```
识别实体数: 128
查数模式: 多实体
返回实体数: 128
文件: /path/to/miaoxiang/mx_finance_data/mx_finance_data_a1b2c3d4.xlsx
Markdown: /path/to/miaoxiang/mx_finance_data/mx_finance_data_a1b2c3d4.md
表格行数: 150
```

### 输出文件说明

| 文件 | 说明 |
| --- | --- |
| `mx_finance_data_<查询id>.xlsx` | 结构化数据表，包含请求的实体与指标 |
| `mx_finance_data_<查询id>.md` | 与 Excel 内容一致的 Markdown 表格 |


## 常见问题

**曾授权成功但本次又返回 `need_auth`**

- `EM_API_KEY` 可能已被服务端失效。按 [授权协议](references/auth_protocol.md) 清理失效凭据并优先通过 `mx_get_user_api_key` 重新获取；仍不可用时再回退到 skill 内置授权。
- 频繁失效请联系客服 400-620-1818。

**多实体查数报错：缺少 --indicators**

- 识别实体数 > 5 时必须提供 `--indicators`，否则无法构造有效的查数问句。

**当前一次请求的数据量过大，部分数据可能会有缺失，请减少指标数量和查询日期范围**

- 可分批多次（分不同指标或者日期）调用该技能，一次性请求压力过大。

**多实体查数最多处理识别结果中前 500 个有效实体**

- 可分批多次（每次500个实体数量以内）调用该技能
