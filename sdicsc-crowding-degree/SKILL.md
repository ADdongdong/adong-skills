---
name: sdicsc-crowding-degree
displayName: 国投证券行业拥挤度
version: 1.0.2
description: 国投证券行业拥挤度查询工具，依托全市场成交额、总市值、换手率等指标，提供行业拥挤度数据查询服务。当用户查询行业拥挤度、某行业市场情况时使用此skill。 
trigger_keywords:
  - A股行业拥挤度
  - 行业拥挤度
  - 某行业交易市场情况
  - 半导体拥挤度
  - 互联网拥挤度
  - 医药拥挤度
  - 新能源拥挤度
allowed-tools:
  - execute_command
---

# 行业拥挤度查询工具

## 概述

提供行业拥挤度数据查询服务，依托全市场成交额、总市值、换手率等指标，帮助投资者了解各行业的市场交易情况。

## 工作流程

```
用户请求 → API Key检查 → 设置环境变量 → 调用脚本取数 → 解析JSON → 输出行业拥挤度报告 → 添加免责声明 → 结束
```

**执行步骤**：

0. **API Key 检查** — 读取 `memory.md`，确认已配置 API Key；未配置则提示用户先获取

1. **设置环境变量** — 从 `memory.md` 读取 API Key，设置环境变量 `GT_CROWDING_DEGREE_API_KEY`

2. **提取行业关键词** — 从用户输入中提取行业关键词（如"半导体"、"医药"、"新能源"等）

3. **调用脚本取数** — 无需读取 industry_info.json 文件，直接执行命令：
   ```bash
   python scripts/query_crowding.py 关键词  
   ```

4. **解析返回数据** — 解析 JSON 结构，输出数据：
   - 使用md表格输出数据
   - 基于数据输出指标解读
   - 提示客户数据来源：国投证券

   JSON 结构解析：
   - `code`：状态码
   - `msg`：信息
   - `data`：数组，包含：
     - `code`：指数代码
     - `name`：行业名称
     - `crowding_data`：原始拥挤度数据
   - 映射关系：
     - Max → stats.max
     - Min → stats.min
     - Now → stats.now
     - 分位数 → stats.quantile
     - 本周数据 → trend.last_week
     - 本周环比增减 → trend.diff_week
     - 环比增幅 → trend.diff_pct
     - 上周环比增减 → trend.last_diff_week
     - 环比增幅 → trend.last_diff_pct
     - 上上周环比增减 → trend.last2_diff_week
     - 环比增幅 → trend.last2_diff_pct

5. **输出 Markdown 报告** — 按指定格式输出行业拥挤度数据

6. **添加风险提示** — 报告末尾必须完整展示 `assets/disclaimer.md` 的声明内容

---

## 前置配置

### 获取 API Key

该技能依赖国投证券的数据服务，需要先配置 API Key。

**如未配置 API Key，请提示用户前往以下地址获取：**
**https://www.sdicsc.com.cn/skills**

### API Key 持久化存储

当用户提供 API Key 并完成凭证配置后，智能体**必须**执行以下操作：

1. **立即写入 memory.md**：
   - 创建或更新 `./memory.md` 文件
   - 添加以下内容：
     ```markdown
     ## 行业拥挤度服务配置

     - API Key: [用户提供的API Key]
     - 环境变量名: GT_CROWDING_DEGREE_API_KEY
     - 配置时间: [当前时间]
     ```

2. **后续调用脚本时设置环境变量**：
   - 从 memory.md 读取 API Key
   - 在调用脚本前设置环境变量：
     ```python
     import os
     api_key = 从memory.md读取的API Key
     os.environ["GT_CROWDING_DEGREE_API_KEY"] = api_key
     ```
   - 然后调用脚本执行行业拥挤度查询

3. **确认存储成功**：告知用户 API Key 已保存，后续使用无需重复配置

**注意事项**：
- memory.md 用于智能体长期记忆，确保 API Key 在会话间保持有效
- 环境变量 `GT_CROWDING_DEGREE_API_KEY` 是脚本读取 API Key 的唯一途径
- 每次调用脚本前必须设置该环境变量，否则脚本将无法获取 API Key
- 如用户更换 API Key，需同步更新 memory.md 中的配置

---

## 异常处理

### API Key 异常

- 返回 `401`：未携带 API Key，引导用户按上述步骤配置
- 返回 `403`：API Key 无效，引导用户重新获取并更新 `memory.md`

### 数据查询异常

- 返回 `超时（Timeout）`：自动重试，最多3次，间隔≥2秒
- 返回 `500`：服务器错误，自动重试，最多3次，间隔≥2秒
- 无响应：网络问题，检查网络连接后重试

### 数据为空

- 若 `crowding_data` 为空，输出：**当前指数暂无拥挤度统计数据**
- 若返回 `data` 为空数组，输出：**未找到匹配的行业，请检查行业名称是否正确**

---

## 输出规范

### 行业拥挤度监测数据

> 数据统计时间：{{crowding_data.calc_time}}

#### 指数信息
指数代码：{{code}}｜行业名称：{{name}}

### 一、5日维度拥挤度指标表
| 指标行 | 成交额占比-近5日平均值占比 | 总市值占比-近5日平均值占比 | 换手率占比-近5日平均值占比 |
| ---- | ---- | ---- | ---- |
| Max | {{crowding_data.5d.amount_ratio.stats.max}} | {{crowding_data.5d.total_market_value_ratio.stats.max}} | {{crowding_data.5d.turnover_ratio.stats.max}} |
| Min | {{crowding_data.5d.amount_ratio.stats.min}} | {{crowding_data.5d.total_market_value_ratio.stats.min}} | {{crowding_data.5d.turnover_ratio.stats.min}} |
| Now(当前周期) | {{crowding_data.5d.amount_ratio.stats.now}} | {{crowding_data.5d.total_market_value_ratio.stats.now}} | {{crowding_data.5d.turnover_ratio.stats.now}} |
| **分位数** | **{{crowding_data.5d.amount_ratio.stats.quantile}}** | **{{crowding_data.5d.total_market_value_ratio.stats.quantile}}** | **{{crowding_data.5d.turnover_ratio.stats.quantile}}** |
| 上周数据 | {{crowding_data.5d.amount_ratio.trend.last_week}} | {{crowding_data.5d.total_market_value_ratio.trend.last_week}} | {{crowding_data.5d.turnover_ratio.trend.last_week}} |
| 本周环比增减 | {{crowding_data.5d.amount_ratio.trend.diff_week}} | {{crowding_data.5d.total_market_value_ratio.trend.diff_week}} | {{crowding_data.5d.turnover_ratio.trend.diff_week}} |
| 环比增幅 | {{crowding_data.5d.amount_ratio.trend.diff_pct}} | {{crowding_data.5d.total_market_value_ratio.trend.diff_pct}} | {{crowding_data.5d.turnover_ratio.trend.diff_pct}} |
| 上周环比增减 | {{crowding_data.5d.amount_ratio.trend.last_diff_week}} | {{crowding_data.5d.total_market_value_ratio.trend.last_diff_week}} | {{crowding_data.5d.turnover_ratio.trend.last_diff_week}} |
| 环比增幅 | {{crowding_data.5d.amount_ratio.trend.last_diff_pct}} | {{crowding_data.5d.total_market_value_ratio.trend.last_diff_pct}} | {{crowding_data.5d.turnover_ratio.trend.last_diff_pct}} |
| 上上周环比增减 | {{crowding_data.5d.amount_ratio.trend.last2_diff_week}} | {{crowding_data.5d.total_market_value_ratio.trend.last2_diff_week}} | {{crowding_data.5d.turnover_ratio.trend.last2_diff_week}} |
| 环比增幅 | {{crowding_data.5d.amount_ratio.trend.last2_diff_pct}} | {{crowding_data.5d.total_market_value_ratio.trend.last2_diff_pct}} | {{crowding_data.5d.turnover_ratio.trend.last2_diff_pct}} |

---

### 二、20日维度拥挤度指标表
| 指标行 | 成交额占比-近20日平均值占比 | 总市值占比-近20日平均值占比 | 换手率占比-近20日平均值占比 |
| ---- | ---- | ---- | ---- |
| Max | {{crowding_data.20d.amount_ratio.stats.max}} | {{crowding_data.20d.total_market_value_ratio.stats.max}} | {{crowding_data.20d.turnover_ratio.stats.max}} |
| Min | {{crowding_data.20d.amount_ratio.stats.min}} | {{crowding_data.20d.total_market_value_ratio.stats.min}} | {{crowding_data.20d.turnover_ratio.stats.min}} |
| Now(当前周期) | {{crowding_data.20d.amount_ratio.stats.now}} | {{crowding_data.20d.total_market_value_ratio.stats.now}} | {{crowding_data.20d.turnover_ratio.stats.now}} |
| **分位数** | **{{crowding_data.20d.amount_ratio.stats.quantile}}** | **{{crowding_data.20d.total_market_value_ratio.stats.quantile}}** | **{{crowding_data.20d.turnover_ratio.stats.quantile}}** |
| 上周数据 | {{crowding_data.20d.amount_ratio.trend.last_week}} | {{crowding_data.20d.total_market_value_ratio.trend.last_week}} | {{crowding_data.20d.turnover_ratio.trend.last_week}} |
| 本周环比增减 | {{crowding_data.20d.amount_ratio.trend.diff_week}} | {{crowding_data.20d.total_market_value_ratio.trend.diff_week}} | {{crowding_data.20d.turnover_ratio.trend.diff_week}} |
| 环比增幅 | {{crowding_data.20d.amount_ratio.trend.diff_pct}} | {{crowding_data.20d.total_market_value_ratio.trend.diff_pct}} | {{crowding_data.20d.turnover_ratio.trend.diff_pct}} |
| 上周环比增减 | {{crowding_data.20d.amount_ratio.trend.last_diff_week}} | {{crowding_data.20d.total_market_value_ratio.trend.last_diff_week}} | {{crowding_data.20d.turnover_ratio.trend.last_diff_week}} |
| 环比增幅 | {{crowding_data.20d.amount_ratio.trend.last_diff_pct}} | {{crowding_data.20d.total_market_value_ratio.trend.last_diff_pct}} | {{crowding_data.20d.turnover_ratio.trend.last_diff_pct}} |
| 上上周环比增减 | {{crowding_data.20d.amount_ratio.trend.last2_diff_week}} | {{crowding_data.20d.total_market_value_ratio.trend.last2_diff_week}} | {{crowding_data.20d.turnover_ratio.trend.last2_diff_week}} |
| 环比增幅 | {{crowding_data.20d.amount_ratio.trend.last2_diff_pct}} | {{crowding_data.20d.total_market_value_ratio.trend.last2_diff_pct}} | {{crowding_data.20d.turnover_ratio.trend.last2_diff_pct}} |

---

## 数据来源

数据来源：国投证券

---

## 注意事项
**【重要】风险提示及免责声明** — 报告末尾必须完整展示 `assets/disclaimer.md` 的声明内容，不得省略
