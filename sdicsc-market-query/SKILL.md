---
name: sdicsc-market-query
displayName: 国投证券行情数据
description: 国投证券行情数据Skill，提供A股及主要指数的行情数据查询能力，支持实时与历史行情及板块表现等多维度数据获取，支持自然语言查询。此Skill在用户需要查询股票数据、获取实时行情、分析K线或查看排名时使用。
version: 1.0.2
---

# 国投证券行情Skill

## 功能介绍
本技能提供行情数据查询能力，支持：
- 实时行情查询，支持单个股票、指数、ETF、板块
- 批量行情查询
- 分时数据
- 日/周/月/年K线及分钟K线
- 股票、板块、ETF涨幅排名
- 支持沪深京A股、港股股票

---

## 风险提示及免责声明

国投证券Skills为AI辅助工具，所有输出内容均基于公开信息和算法模型生成，仅供学习参考，不构成任何投资建议或投资决策依据。国投证券Skills不对因使用本工具产生的任何直接或间接投资损失承担责任。市场有风险，投资需谨慎。

---

## ⚠️ 立即使用 - API Key 配置

**在使用本 skill 查询股票数据前，请先完成以下步骤：**

### 步骤1：获取 API Key

访问以下地址获取 API Key：

**地址**: https://www.sdicsc.com.cn/skills

### 步骤2：配置 API Key

获取 API Key 后，请告诉我你的 API Key，我会帮你保存到 `memory.md` 文件中。

例如：
> 我的 API Key 是：gt_xxxxxxxxxxxxx

保存后，系统会自动将 API Key 写入 `memory.md` 文件，后续查询将自动使用该 API Key。

### 步骤3：验证配置

配置成功后，再次查询股票数据时将自动使用已保存的 API Key。

---

## ⚠️ API Key 验证

**使用本 skill 前必须先配置 API Key！**

### 检查 API Key

在执行任何操作前，请先确认是否已配置 API Key。如果没有配置，请提供你的 API Key。

### 如果未设置 API Key

请访问以下地址获取 API Key：

- **地址**: https://www.sdicsc.com.cn/skills

获取 API Key 后，请告诉我："我的 API Key 是：xxx"，我会帮你保存到 `memory.md` 文件中。

**重要提示**：
- API Key 是用户身份标识，用于访问股票行情服务
- 请妥善保管您的 API Key，不要泄露给他人
- 如果 API Key 失效或过期，请重新到上述地址获取

---

## 服务地址

**网关地址**: `https://skills.sdicsc.com.cn/skill/hq`

所有 API 请求都通过网关统一认证鉴权。

## API Key 使用说明

在调用 API 时，需要在请求头中携带 API Key：

```bash
# 示例：带 API Key 的请求
curl -H "X-API-Key: {api_key}" https://skills.sdicsc.com.cn/skill/hq/api/quote/sh600061
```

**注意**：所有 API 调用都必须包含有效的 API Key，否则将返回 401 未授权错误。

### 错误处理与重试机制

调用 API 时如遇到以下错误，请按指引处理：

| HTTP 状态码 | 错误信息 | 原因 | 处理方式 |
|------------|----------|------|----------|
| 401 | Missing X-API-Key | 未携带 API Key | 请提供您的 API Key，格式："我的 API Key 是：xxx" |
| 403 | Invalid API Key | API Key 无效或已过期 | 请检查 API Key 是否正确，或重新获取新的 API Key |
| 429 | Too Many Requests | 请求频率超限 | 不可重试，请等待一段时间后再试 |
| 500 | validate service error | 鉴权服务异常或网络超时 | **自动重试最多 3 次**，若仍失败请稍后重试 |
| 503 | Service Unavailable | 服务暂时不可用 | 不可重试，请等待一段时间后再试 |

**重试策略**：
- 遇到 500 错误时，系统会自动重试，最多 3 次，每次重试间隔 1 秒
- 429 和 503 错误不可重试，请等待一段时间后再试

---

## 可用接口

### 1. 获取单个股票行情

```
GET /api/quote/:code
```

**参数**:
- `code` (path, 必需): 股票代码，支持格式如 `000001` 或 `sh600000`

**输出参数**:
| 字段 | 类型 | 说明 |
|------|------|------|
| code | string | 股票代码 |
| name | string | 股票名称 |
| price | number | 当前价格 |
| change | number | 涨跌额 |
| changePercent | string | 涨跌幅(%) |
| prevClose | number | 昨收价 |
| open | number | 开盘价 |
| high | number | 最高价 |
| low | number | 最低价 |
| avgPrice | number | 均价 |
| volume | string | 成交量(手) |
| amount | string | 成交额(元) |
| turnover | string | 换手率(%) |
| amplitude | string | 振幅(%) |
| outside | string | 外盘(手) |
| inside | string | 内盘(手) |
| volumeRatio | number | 量比 |
| pe | number | 市盈率 |
| dynamicPe | number | 动态市盈率 |
| peTtm | number | 市盈率TTM |
| marketValue | string | 总市值 |
| circulationMarketValue | string | 流通市值 |
| industryCode | string | 行业代码 |
| industryName | string | 行业名称 |
| change5 | string | 5日涨跌幅(%) |
| change20 | string | 20日涨跌幅(%) |
| change60 | string | 60日涨跌幅(%) |
| change120 | string | 120日涨跌幅(%) |
| change250 | string | 250日涨跌幅(%) |
| changeThisYear | string | 今年涨幅(%) |
| changeThisMonth | string | 本月涨幅(%) |
| changeThisWeek | string | 本周涨幅(%) |
| quickChangePercent | string | 快速涨跌幅(%) |
| iopv | string | IOPV |
| discountRate | string | 折价率 |
| fundScale | string | 基金规模 |
| date | string | 日期 |
| time | string | 时间 |
| suspFlag | string | 停牌标志 |

**示例**:
```
GET https://skills.sdicsc.com.cn/skill/hq/api/quote/sh600000
```

---

### 2. 批量获取股票行情

```
POST /api/quote/batch
```

**请求体**:
```json
{
  "codes": ["sh600000", "sz000001", "sh600061"],
  "sort": "changePercent",
  "order": "desc"
}
```

**参数**:
- `codes` (array, 必需): 股票代码数组
- `sort` (string, 可选): 排序字段 `price` | `change` | `changePercent`
- `order` (string, 可选): 排序方式 `asc` | `desc`

**输出**: 返回 `{ data: [...] }`，data数组中每个元素的字段与单个行情接口相同。

---

### 3. 获取股票分时数据

```
GET /api/trend/:code
```

**参数**:
- `code` (path, 必需): 股票代码

**输出**:
```json
{
  "success": true,
  "data": {
    "meta": {
      "stockCode": "600000",
      "stockName": "浦发银行",
      "date": "2024-01-15",
      "preClose": 10.50,
      "open": 10.48,
      "high": 10.55,
      "low": 10.45
    },
    "timeData": [
      {
        "time": 1,
        "price": 10.48,
        "avgPrice": 10.47,
        "volume": 1500,
        "change": -0.02,
        "changePercent": "-0.19%"
      }
    ]
  }
}
```

**timeData 数组中每条记录的字段**:
| 字段 | 类型 | 说明 |
|------|------|------|
| time | number | 分时序号(1-241) |
| price | number | 当前价格 |
| avgPrice | number | 均价 |
| volume | number | 成交量 |
| change | number | 涨跌额 |
| changePercent | string | 涨跌幅(%)，带%后缀 |

---

### 4. 获取K线数据

```
GET /api/kline/:code?type=day&count=100
```

**参数**:
- `code` (path, 必需): 股票代码
- `type` (query, 可选): K线类型 `day` | `week` | `month` | `year` | `1min` | `5min` | `15min` | `30min` | `60min`，默认 `day`
- `count` (query, 可选): 返回数据条数，默认 `100`

**输出** (日/周/月/年K线):
```json
{
  "meta": {
    "stockCode": "600000",
    "stockName": "浦发银行",
    "maxCount": 100,
    "beginDate": "2024-01-01",
    "endDate": "2024-12-31",
    "count": 100
  },
  "kLineData": [
    {
      "time": "2024-01-15",
      "open": 10.15,
      "high": 10.28,
      "low": 10.10,
      "close": 10.25,
      "volume": 1250000,
      "amount": 0
    }
  ]
}
```

**输出** (分钟K线):
```json
{
  "meta": {
    "stockCode": "600000",
    "stockName": "浦发银行",
    "maxCount": 50,
    "beginDate": "2025-06-18 09:30",
    "endDate": "2025-06-18 15:00",
    "count": 50
  },
  "kLineData": [
    {
      "time": "2025-06-18 09:35",
      "open": 10.50,
      "high": 10.55,
      "low": 10.48,
      "close": 10.52,
      "volume": 8500,
      "amount": 0
    }
  ]
}
```

**kLineData 数组中每条记录的字段**:
| 字段 | 类型 | 说明 |
|------|------|------|
| time | string | 日期字符串 (如 "2024-01-15" 或 "2025-06-18 09:35") |
| open | number | 开盘价 |
| high | number | 最高价 |
| low | number | 最低价 |
| close | number | 收盘价 |
| volume | number | 成交量 |
| amount | number | 成交金额 |

---

### 5. 获取股票涨幅排名

```
GET /api/rank/stock?sort=changePercent&order=desc&market=sh&count=10
```

**参数**:
- `sort` (query, 可选): 排序字段 `change` | `changePercent` | `volume` | `amount` | `change5` | `change20` | `change60` | `change120` | `change250` | `changeThisYear` | `changeThisMonth` | `changeThisWeek`
- `order` (query, 可选): 排序方式 `asc` | `desc`
- `market` (query, 可选): 市场筛选 `sh` | `sz` | `bj` | `hk` | `kcb` | `cyb`
- `sector` (query, 可选): 板块筛选(板块代码或名称)
- `count` (query, 可选): 返回数量，默认 `100`

**输出**: `{ "data": [...] }`

**data 数组中每条记录的字段**:
| 字段 | 类型 | 说明 |
|------|------|------|
| code | string | 股票代码 |
| name | string | 股票名称 |
| price | number | 当前价格 |
| change | number | 涨跌额 |
| changePercent | string | 涨跌幅(%) |
| prevClose | number | 昨收价 |
| open | number | 开盘价 |
| high | number | 最高价 |
| low | number | 最低价 |
| avgPrice | number | 均价 |
| volume | string | 成交量(手) |
| amount | string | 成交额(元) |
| turnover | string | 换手率(%) |
| amplitude | string | 振幅(%) |
| outside | string | 外盘(手) |
| inside | string | 内盘(手) |
| volumeRatio | number | 量比 |
| pe | number | 市盈率 |
| peDynamic | number | 动态市盈率 |
| peTTM | number | 市盈率TTM |
| totalMarketValue | string | 总市值 |
| circulationMarketValue | string | 流通市值 |
| industryCode | string | 行业代码 |
| industryName | string | 行业名称 |
| change5 | string | 5日涨跌幅(%) |
| change20 | string | 20日涨跌幅(%) |
| change60 | string | 60日涨跌幅(%) |
| change120 | string | 120日涨跌幅(%) |
| change250 | string | 250日涨跌幅(%) |
| changeThisYear | string | 今年涨幅(%) |
| changeThisMonth | string | 本月涨幅(%) |
| changeThisWeek | string | 本周涨幅(%) |
| quickChangePercent | string | 快速涨跌幅(%) |
| date | string | 日期(YYYY-MM-DD) |
| time | string | 时间(HH:mm:ss) |
| suspFlag | string | 停牌标志 |

---

### 6. 获取板块涨幅排名

```
GET /api/rank/sector?sort=changePercent&order=desc&count=10
```

**参数**:
- `sort` (query, 可选): 排序字段 `change` | `changePercent` | `volume` | `change5` | `change20` | `change60` | `change120` | `change250` | `changeThisYear` | `changeThisMonth` | `changeThisWeek` | `fundScale` | `discountRate`
- `order` (query, 可选): 排序方式 `asc` | `desc`
- `category` (query, 可选): 板块分类 `all` | `industry` | `concept` | `region`
- `level` (query, 可选): 板块层级 `1` | `2` | `3`
- `count` (query, 可选): 返回数量，默认 `100`

**输出**: `{ "data": [...] }`

**data 数组中每条记录的字段**:
| 字段 | 类型 | 说明 |
|------|------|------|
| code | string | 板块代码 |
| name | string | 板块名称 |
| price | number | 当前价格 |
| change | number | 涨跌额 |
| changePercent | string | 涨跌幅(%) |
| prevClose | number | 昨收价 |
| open | number | 开盘价 |
| high | number | 最高价 |
| low | number | 最低价 |
| avgPrice | number | 均价 |
| volume | string | 成交量(手) |
| amount | string | 成交额(元) |
| currentHand | number | 现手 |
| turnover | string | 换手率(%) |
| amplitude | string | 振幅(%) |
| volumeRatio | number | 量比 |
| leadStock | string | 领涨股票代码 |
| leadStockName | string | 领涨股票名称 |
| leadStockPrice | number | 领涨股票价格 |
| leadStockChange | number | 领涨股票涨幅(%) |
| change5 | string | 5日涨跌幅(%) |
| change20 | string | 20日涨跌幅(%) |
| change60 | string | 60日涨跌幅(%) |
| change120 | string | 120日涨跌幅(%) |
| change250 | string | 250日涨跌幅(%) |
| changeThisYear | string | 今年涨幅(%) |
| changeThisMonth | string | 本月涨幅(%) |
| changeThisWeek | string | 本周涨幅(%) |
| quickChangePercent | string | 快速涨跌幅(%) |
| date | string | 日期(YYYY-MM-DD) |
| time | string | 时间(HH:mm:ss) |

---

### 7. 获取ETF基金涨幅排名

```
GET /api/rank/etf?sort=changePercent&order=desc&count=10
```

**参数**:
- `sort` (query, 可选): 排序字段 `change` | `changePercent` | `volume` | `change5` | `change20` | `change60` | `change120` | `change250` | `changeThisYear` | `changeThisMonth` | `changeThisWeek` | `fundScale` | `discountRate`
- `order` (query, 可选): 排序方式 `asc` | `desc`
- `count` (query, 可选): 返回数量，默认 `100`

**输出**: `{ "data": [...] }`

**data 数组中每条记录的字段**:
| 字段 | 类型 | 说明 |
|------|------|------|
| code | string | ETF代码 |
| name | string | ETF名称 |
| price | number | 当前价格 |
| change | number | 涨跌额 |
| changePercent | string | 涨跌幅(%) |
| prevClose | number | 昨收价 |
| open | number | 开盘价 |
| high | number | 最高价 |
| low | number | 最低价 |
| avgPrice | number | 均价 |
| volume | string | 成交量(手) |
| amount | string | 成交额(元) |
| currentHand | number | 现手 |
| turnover | string | 换手率(%) |
| amplitude | string | 振幅(%) |
| volumeRatio | number | 量比 |
| iopv | string | 基金净值(IOPV) |
| discountRate | string | 折价率 |
| fundScale | string | 基金规模 |
| change20 | string | 20日涨跌幅(%) |
| change60 | string | 60日涨跌幅(%) |
| change120 | string | 120日涨跌幅(%) |
| change250 | string | 250日涨跌幅(%) |
| change5 | string | 5日涨跌幅(%) |
| changeThisYear | string | 今年涨幅(%) |
| changeThisMonth | string | 本月涨幅(%) |
| changeThisWeek | string | 本周涨幅(%) |
| quickChangePercent | string | 快速涨跌幅(%) |
| date | string | 日期(YYYY-MM-DD) |
| time | string | 时间(HH:mm:ss) |
| suspFlag | string | 停牌状态 |

---

### 8. 健康检查

```
GET /health
```

**输出**:
```json
{
  "status": "ok"
}
```

---

## 股票代码格式

- 上海股票: `sh600000` 或 `600000`
- 深圳股票: `sz000001` 或 `000001`
- 北京股票: `bj920000` 或 `920000`
- 香港股票: `h00700` 或 `hk00700`

---

## 使用示例

> **注意**：以下示例需添加 API Key 请求头 `-H "X-API-Key: your_api_key"`

### 带APIKey请求示例

```bash
# 查询股票行情
curl -H "X-API-Key: gt_xxxxxxxxxxxxx" \
  "https://skills.sdicsc.com.cn/skill/hq/api/quote/sh600061"

# 批量查询
curl -X POST -H "X-API-Key: gt_xxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  "https://skills.sdicsc.com.cn/skill/hq/api/quote/batch" \
  -d '{"codes": ["sh600000", "sh600061"], "sort": "changePercent", "order": "desc"}'
```

### 查询国投资本当前行情

```bash
curl https://skills.sdicsc.com.cn/skill/hq/api/quote/sh600061
```

### 批量查询多只股票并按涨幅排序

```bash
curl -X POST https://skills.sdicsc.com.cn/skill/hq/api/quote/batch \
  -H "Content-Type: application/json" \
  -d '{"codes": ["sh600000", "sh600061", "sz000001"], "sort": "changePercent", "order": "desc"}'
```

### 获取股票分时数据

```bash
curl "https://skills.sdicsc.com.cn/skill/hq/api/trend/sh600061"
```

### 获取股票的日K线

```bash
curl "https://skills.sdicsc.com.cn/skill/hq/api/kline/sh600061?type=day&count=100"
```

### 获取股票的周K线

```bash
curl "https://skills.sdicsc.com.cn/skill/hq/api/kline/sh600061?type=week&count=50"
```

### 获取股票的月K线

```bash
curl "https://skills.sdicsc.com.cn/skill/hq/api/kline/sh600061?type=month&count=20"
```

### 获取股票的5分钟K线

```bash
curl "https://skills.sdicsc.com.cn/skill/hq/api/kline/sh600061?type=5min&count=100"
```

### 获取股票的60分钟K线

```bash
curl "https://skills.sdicsc.com.cn/skill/hq/api/kline/sh600061?type=60min&count=50"
```

### 获取今日涨幅前10的上海股票

```bash
curl "https://skills.sdicsc.com.cn/skill/hq/api/rank/stock?sort=changePercent&order=desc&market=sh&count=10"
```

### 获取今日成交量前10的深圳股票

```bash
curl "https://skills.sdicsc.com.cn/skill/hq/api/rank/stock?sort=volume&order=desc&market=sz&count=10"
```

### 获取本周涨幅前10的股票

```bash
curl "https://skills.sdicsc.com.cn/skill/hq/api/rank/stock?sort=changeThisWeek&order=desc&count=10"
```

### 获取光刻胶板块涨幅靠前的股票

```bash
curl "https://skills.sdicsc.com.cn/skill/hq/api/rank/stock?sector=光刻胶"
```

### 获取涨幅前10的板块

```bash
curl "https://skills.sdicsc.com.cn/skill/hq/api/rank/sector?sort=changePercent&order=desc&count=10"
```

### 获取今日涨幅前10的概念板块

```bash
curl "https://skills.sdicsc.com.cn/skill/hq/api/rank/sector?sort=changePercent&order=desc&category=concept&count=10"
```

### 获取今日涨幅前10的行业板块

```bash
curl "https://skills.sdicsc.com.cn/skill/hq/api/rank/sector?sort=changePercent&order=desc&category=industry&count=10"
```

### 健康检查

```bash
curl "https://skills.sdicsc.com.cn/skill/hq/health"
```

