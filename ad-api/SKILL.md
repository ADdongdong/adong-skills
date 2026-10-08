---
name: ad-api
description: 中国银河证券星耀数智金融数据API技能。当用户需要获取中国证券市场数据（股票、债券、基金、期货、期权、港股通等）、查询财务报表、分析历史行情时使用此技能。支持历史数据查询、财务数据分析、股东数据查询等场景。只要涉及中国A股、港股通、期货期权等金融数据查询和分析，都应该使用此技能。
---

## 概述

AmazingData是中国银河证券提供的金融数据接口包，拥有丰富的数据内容，包括股票、债券、基金、期货、期权、港股通等行情数据，以及公司财务、股东股本等基本面数据。通过API方式提供金融数据服务，以帮助用户简洁、轻量的使用相关数据。

## 快速上手

- 安装python运行环境(推荐python3.8/3.9/3.10/3.11/3.12/3.13环境)，并安装AmazingData依赖包。
从https://gitee.com/cgs2026/xysz clone整个项目，再用xysz_tools下的wheel文件安装tgw和AmazingData。
```bash
pip install tgw>=1.0.8.7
pip install AmazingData>=1.1.4
```
- 联系开户营业部申请账号、密码、服务器IP。
- 设置环境变量：
```bash
# Windows CMD
set AD_USERNAME=your_username
set AD_PASSWORD=your_password
set AD_HOST=server_ip
set AD_PORT=port

# Windows PowerShell
$env:AD_USERNAME="your_username"
$env:AD_PASSWORD="your_password"
$env:AD_HOST="server_ip"
$env:AD_PORT="port"
```
- 配置登录信息并初始化。
```python
import os
import AmazingData as ad

ad.login(
    username=os.environ['AD_USERNAME'],
    password=os.environ['AD_PASSWORD'],
    host=os.environ['AD_HOST'],
    port=int(os.environ['AD_PORT'])
)
```
- 查询AmazingData接口文档，找到对应的接口。
- 根据接口文档，使用python代码获取数据。

## 参数格式说明

- 日期：8位整型格式，如 20241231
- 股票代码：交易所代码格式（如 000***.SZ, 600***.SH）
- 返回格式：pandas DataFrame 或 dict（key为代码，value为DataFrame）

## 数据接口调用模式

AmazingData有三个核心数据对象：

| 对象 | 实例化方式 | 用途 |
|------|------|------|
| BaseData | `ad.BaseData()` | 基础数据（代码表、交易日历、复权因子、ETF申赎清单等） |
| MarketData | `ad.MarketData(calendar)` | 历史行情数据（K线、快照），需传入交易日历 |
| InfoData | `ad.InfoData()` | 信息数据（财务、股东、融资融券、龙虎榜、可转债、ETF份额/IOPV、期权、指数等） |

### 数据缓存方案

支持两种数据获取方式（二选一，不可混用）：

**方案1：本地缓存（推荐，速度快）**
- 参数：`local_path`（绝对路径） + `is_local`（True/False）
- is_local=True：优先从本地取数据；本地无数据时从服务端获取并缓存
- is_local=False：从服务端获取数据并更新本地缓存
- 文件格式：HDF5，建议本地存储空间500GB以上

**方案2：指定日期范围（不缓存）**
- 参数：`begin_date` + `end_date`
- 仅从服务器获取数据，不本地缓存

## python脚本示例

- [股票数据获取示例](scripts/stock_data_example.py)
- [ETF数据获取示例](scripts/etf_data_example.py)
- [可转债数据获取示例](scripts/convertible_bond_data_example.py)
- [期权数据获取示例](scripts/option_data_example.py)


## 数据接口列表

| 分类 | 接口 | 函数名 | 说明 |
|------|------|------|------|
| 基础数据 | [每日最新代码表](references/base_data/daily_code_list.md) | get_code_list | 获取最新证券代码列表 |
| 基础数据 | [每日最新证券信息](references/base_data/daily_code_info.md) | get_code_info | 获取证券基本信息 |
| 基础数据 | [证券基础信息](references/base_data/stock_basic_info.md) | InfoData.get_stock_basic | 获取证券详细信息 |
| 基础数据 | [交易日历](references/base_data/trading_calendar.md) | get_calendar | 获取交易日历 |
| 基础数据 | [复权因子](references/base_data/adj_factor.md) | get_backward_factor / get_adj_factor | 获取后复权/单次复权因子 |
| 基础数据 | [历史代码表](references/base_data/hist_code_list.md) | get_hist_code_list | 获取历史代码表 |
| 基础数据 | [期货代码表](references/base_data/future_code_list.md) | get_future_code_list | 获取期货代码表 |
| 基础数据 | [期权代码表](references/base_data/option_code_list.md) | get_option_code_list | 获取期权代码表 |
| 基础数据 | [历史证券信息](references/base_data/history_stock_status.md) | InfoData.get_history_stock_status | 获取历史证券信息 |
| 基础数据 | [北交所代码对照](references/base_data/bj_code_mapping.md) | InfoData.get_bj_code_mapping | 获取北交所新旧代码对照 |
| 行情数据 | [历史K线](references/market_data/kline.md) | query_kline | 获取历史K线数据 |
| 行情数据 | [历史快照](references/market_data/snapshot.md) | query_snapshot | 获取历史快照数据 |
| 财务数据 | [资产负债表](references/financial_data/balance_sheet.md) | get_balance_sheet | 获取资产负债表 |
| 财务数据 | [现金流量表](references/financial_data/cash_flow.md) | get_cash_flow | 获取现金流量表 |
| 财务数据 | [利润表](references/financial_data/income.md) | get_income | 获取利润表 |
| 财务数据 | [业绩快报](references/financial_data/profit_express.md) | get_profit_express | 获取业绩快报 |
| 财务数据 | [业绩预告](references/financial_data/profit_notice.md) | get_profit_notice | 获取业绩预告 |
| 股东数据 | [十大股东](references/shareholder_data/share_holder.md) | get_share_holder | 获取十大股东数据 |
| 股东数据 | [股东户数](references/shareholder_data/holder_num.md) | get_holder_num | 获取股东户数 |
| 股东数据 | [股本结构](references/shareholder_data/equity_structure.md) | get_equity_structure | 获取股本结构 |
| 股东数据 | [分红数据](references/shareholder_data/dividend.md) | get_dividend | 获取分红数据 |
| 股东数据 | [配股数据](references/shareholder_data/right_issue.md) | get_right_issue | 获取配股数据 |
| 股东数据 | [股权冻结质押](references/shareholder_data/equity_pledge_freeze.md) | get_equity_pledge_freeze | 获取股权冻结质押 |
| 股东数据 | [限售股解禁](references/shareholder_data/equity_restricted.md) | get_equity_restricted | 获取限售股解禁 |
| 融资融券 | [融资融券汇总](references/margin_trading/margin_summary.md) | get_margin_summary | 获取融资融券汇总 |
| 融资融券 | [融资融券明细](references/margin_trading/margin_detail.md) | get_margin_detail | 获取融资融券明细 |
| 交易数据 | [龙虎榜](references/trading_data/long_hu_bang.md) | get_long_hu_bang | 获取龙虎榜数据 |
| 交易数据 | [大宗交易](references/trading_data/block_trading.md) | get_block_trading | 获取大宗交易数据 |
| 期权数据 | [期权基本资料](references/option_data/option_basic_info.md) | get_option_basic_info | 获取期权基本资料 |
| 期权数据 | [期权标准合约属性](references/option_data/option_std_ctr_specs.md) | get_option_std_ctr_specs | 获取期权标准合约属性 |
| 期权数据 | [期权月合约属性变动](references/option_data/option_mon_ctr_specs.md) | get_option_mon_ctr_specs | 获取期权月合约属性变动 |
| ETF数据 | [ETF申赎清单](references/etf_data/etf_pcf.md) | BaseData.get_etf_pcf | 获取ETF申赎清单 |
| ETF数据 | [ETF基金份额](references/etf_data/etf_fund_share.md) | get_fund_share | 获取ETF基金份额 |
| ETF数据 | [ETF每日收盘IOPV](references/etf_data/etf_daily_iopv.md) | get_fund_iopv | 获取ETF每日收盘IOPV |
| 交易所指数 | [交易所指数成分股](references/exchange_index_data/exchange_index_constituent.md) | get_index_constituent | 获取交易所指数成分股 |
| 交易所指数 | [交易所指数成分股日权重](references/exchange_index_data/exchange_index_weight.md) | get_index_weight | 获取交易所指数成分股日权重 |
| 行业指数 | [行业指数基本信息](references/index_data/industry_base_info.md) | get_industry_base_info | 获取行业指数基本信息 |
| 行业指数 | [行业指数成分股](references/index_data/industry_constituent.md) | get_industry_constituent | 获取行业指数成分股 |
| 行业指数 | [行业指数成分股日权重](references/index_data/industry_weight.md) | get_industry_weight | 获取行业指数成分股日权重 |
| 行业指数 | [行业指数日行情](references/index_data/industry_daily.md) | get_industry_daily | 获取行业指数日行情 |
| 可转债数据 | [可转债发行](references/convertible_bond_data/kzz_issuance.md) | get_kzz_issuance | 获取可转债发行数据 |
| 可转债数据 | [可转债份额](references/convertible_bond_data/kzz_share.md) | get_kzz_share | 获取可转债份额 |
| 可转债数据 | [可转债转股](references/convertible_bond_data/kzz_conv.md) | get_kzz_conv | 获取可转债转股数据 |
| 可转债数据 | [可转债转股变动](references/convertible_bond_data/kzz_conv_change.md) | get_kzz_conv_change | 获取转股变动数据 |
| 可转债数据 | [可转债修正](references/convertible_bond_data/kzz_corr.md) | get_kzz_corr | 获取可转债修正 |
| 可转债数据 | [可转债赎回](references/convertible_bond_data/kzz_call.md) | get_kzz_call | 获取可转债赎回 |
| 可转债数据 | [可转债回售](references/convertible_bond_data/kzz_put.md) | get_kzz_put | 获取可转债回售 |
| 可转债数据 | [可转债回售赎回条款](references/convertible_bond_data/kzz_put_call_item.md) | get_kzz_put_call_item | 获取回售赎回条款 |
| 可转债数据 | [可转债赎回条款执行说明](references/convertible_bond_data/kzz_call_explanation.md) | get_kzz_call_explanation | 获取赎回条款执行说明 |
| 可转债数据 | [可转债回售条款执行说明](references/convertible_bond_data/kzz_put_explanation.md) | get_kzz_put_explanation | 获取回售条款执行说明 |
| 可转债数据 | [可转债停复牌](references/convertible_bond_data/kzz_suspend.md) | get_kzz_suspend | 获取可转债停复牌 |
| 债券数据 | [国债收益率](references/bond_data/treasury_yield.md) | get_treasury_yield | 获取国债收益率 |
| 公告数据 | [公告明细数据（上市公司）](references/announcement_data/announcement_stock_list.md) | InfoData.get_announcement_stock_list | 获取上市公司公告明细 |
| 公告数据 | [公告原文下载（上市公司）](references/announcement_data/announcement_stock.md) | InfoData.get_announcement_stock | 下载上市公司公告PDF原文 |
| 公告数据 | [公告明细数据（基金）](references/announcement_data/announcement_fund_list.md) | InfoData.get_announcement_fund_list | 获取基金公告明细 |
| 公告数据 | [公告原文下载（基金）](references/announcement_data/announcement_fund.md) | InfoData.get_announcement_fund | 下载基金公告PDF原文 |
| 公告数据 | [公告明细数据（债券）](references/announcement_data/announcement_bond_list.md) | InfoData.get_announcement_bond_list | 获取可转债公告明细 |
| 公告数据 | [公告原文下载（债券）](references/announcement_data/announcement_bond.md) | InfoData.get_announcement_bond | 下载可转债公告PDF原文 |

## 数据类型代码

详见 [附录](references/appendix.md)

### security_type（沪深北）
- `EXTRA_STOCK_A`: A股（上交所、深交所、北交所）
- `EXTRA_STOCK_A_SH_SZ`: 沪深A股
- `SH_A` / `SZ_A` / `BJ_A`: 单市场A股
- `EXTRA_ETF`: ETF基金
- `EXTRA_KZZ`: 可转债
- `EXTRA_INDEX_A`: 指数（沪深北）
- `EXTRA_HKT`: 港股通
- `EXTRA_GLRA`: 逆回购

### security_type（期货）
- `ZJ_FUTURE`: 中金所期货
- `EXTRA_FUTURE`: 所有期货

### security_type（期权）
- `EXTRA_ETF_OP`: ETF期权（上交所、深交所）

### 周期类型 Period
- `Period.min1.value` ~ `Period.min120.value`: 分钟线
- `Period.day.value`: 日线
- `Period.week.value`: 周线
- `Period.month.value`: 月线
- `Period.season.value`: 季度线
- `Period.year.value`: 年线

## 使用示例

### 获取股票代码列表
```python
import os
import AmazingData as ad

ad.login(
    username=os.environ['AMAZINGDATA_USER'],
    password=os.environ['AMAZINGDATA_PASSWORD'],
    host=os.environ['AMAZINGDATA_HOST'],
    port=int(os.environ['AMAZINGDATA_PORT'])
)
base_data = ad.BaseData()
code_list = base_data.get_code_list(security_type='EXTRA_STOCK_A')
```

## 注意事项

1. 所有数据接口调用前必须先通过环境变量配置认证信息，然后调用`ad.login()`登录
2. 必须设置以下4个环境变量：`AD_USERNAME`、`AD_PASSWORD`、`AD_HOST`、`AD_PORT`
3. 账号、密码、IP和端口需联系开户营业部申请
4. `MarketData`实例化时必须传入交易日历：`ad.MarketData(base_data.get_calendar())`
5. 支持本地数据缓存（local_path + is_local）和指定日期范围（begin_date + end_date）两种模式，二选一
6. 股票数据最早可追溯至2013年，期货数据至2010年，期权数据至2015年
7. AmazingData限制单点登录，所以同一时间只能有一个AmazingData的登录链接

## Python环境要求

- Python版本: 3.8-3.14
- 操作系统: Linux/Windows
- 依赖包: tgw>=1.0.8.5, AmazingData>=1.0.24
