# 基金分析数据获取指引

## 查询优先级策略

遵循 wb-finance-skill 的优先级策略：

1. **首选：neodata-financial-search** — 自然语言金融数据搜索，覆盖面广，适合基金净值、业绩、持仓、评级、经理、指数估值、行业基本面、市场环境、新闻舆情等查询
2. **补充：westock-data** — 结构化行情查询，适合 ETF 详情/持仓/跟踪误差、指数行情/K 线、个股行情/新闻公告、热搜、资金流向等精确字段
3. **选基/排行专用：westock-tool** — ETF 主题池筛选、ETF 排行（规模榜/涨幅榜/估值榜）、热门基金扫描
4. **分析方法论：wb-finance-skill** — 估值建模、回本测算、情景推演、策略框架、仓位决策等分析框架

## 基金相关查询

### 基本信息与业绩

```bash
# neodata-financial-search（推荐，自然语言一站式查询）
python3 scripts/query.py --query "{基金名称} {基金代码} 最新净值 累计净值 近期业绩 规模 费率 基金经理 评级"

# westock-data ETF 详情（结构化字段，指数基金/ETF 专用）
westock-data etf detail <基金代码>
```

### 净值历史

```bash
# neodata-financial-search 自然语言查询
python3 scripts/query.py --query "{基金名称} {基金代码} 历史净值走势 成立以来回报"

# westock-data K 线数据
westock-data kline <基金代码> --period day --limit 250
```

### 持仓明细

```bash
# neodata-financial-search 自然语言查询
python3 scripts/query.py --query "{基金名称} {基金代码} 前十大重仓股 持仓明细"

# westock-data ETF 持仓明细
westock-data etf holdings <基金代码>
```

### 评级与经理信息

```bash
python3 scripts/query.py --query "{基金名称} {基金代码} 基金评级 基金经理 从业年限 在管规模"
```

## 指数相关查询

### 行情与估值

```bash
# neodata-financial-search 自然语言查询
python3 scripts/query.py --query "{指数名称} 当前点位 历史高点 PE-TTM PB 股息率 历史估值分位"

# westock-data 指数 K 线
westock-data kline <指数代码> --period day --limit 250
```

### 成份股

```bash
westock-data index constituent <指数代码>
```

## 市场环境与资金流向

### 市场整体概况

```bash
python3 scripts/query.py --query "今日A股市场整体走势 主要指数涨跌 板块轮动 资金流向 市场情绪"
```

### 资金流向

```bash
# 个股资金流向
westock-data asfund <个股代码>

# 宏观数据
westock-data macro indicator core_indicators_cur
```

### 热门基金/热搜

```bash
# 热搜 ETF
westock-data hot etf

# 热搜股票
westock-data hot stock
```

## ETF 选基与排行

### 主题池筛选

```bash
westock-tool label --asset etf --list                    # 查看所有主题池
westock-tool label high_dividend --asset etf --limit 20  # 高股息 ETF
westock-tool label low_valuation --asset etf --limit 20  # 低估值 ETF
westock-tool label size_100 --asset etf --limit 20       # 百亿规模 ETF
```

### 排行查询

```bash
westock-tool ranking --asset etf --list                       # 查看所有排行指标
westock-tool ranking qt_daily --asset etf --limit 10          # 单日涨跌幅排行
westock-tool ranking qt_chg_interval --asset etf --limit 10   # 区间涨跌排行
westock-tool ranking size --asset etf --limit 20              # 规模排行
westock-tool ranking valuation --asset etf --limit 10         # 估值排行
```

## 个股新闻舆情

### 自然语言新闻搜索

```bash
python3 scripts/query.py --query "{股票名称} {股票代码} 最新新闻 重大公告 舆情动态" --data-type doc
```

### 结构化新闻与公告

```bash
westock-data news article <个股代码> --limit 10
westock-data notice list <个股代码> --limit 5
```

## 股票代码格式说明

| 市场 | 格式 | 示例 |
|------|------|------|
| 沪市/科创板 | sh + 6 位数字 | `sh600519`、`sh688981` |
| 深市 | sz + 6 位数字 | `sz000001` |
| 港股 | hk + 5 位数字 | `hk00700` |
| 美股 | us + 代码 | `usAAPL` |
| 指数 | sh/sz + 6 位数字 | `sh000300`（沪深 300） |

## 重要声明

> 以上命令均基于可信 skill（neodata-financial-search / westock-data / westock-tool / wb-finance-skill）。禁止使用 WebSearch / WebFetch / clawhub / 第三方 API 替代拉行情。报告正文用中性表述，不暴露具体数据源品牌。
