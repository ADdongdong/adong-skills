## 业绩快报

**接口**: get_profit_express

**描述**: 获取指定股票列表的上市公司的业绩快报数据

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| code_list | list[str] | 是 | 支持沪深A的的代码列表，可见示例 |
| local_path | str | 是 | 本地存储数据的路径，需绝对路径，格式类似"'D://AmazingData_local_data//'" |
| is_local | bool | 否 | 默认为True，本地数据缓存方案 |
| begin_date | int | 否 | 报告期，本地数据缓存方案 |
| end_date | int | 否 | 报告期，本地数据缓存方案 |

### 输出参数

返回DataFrame，主要字段包含：

| 字段名称 | 类型 | 字段说明 |
|------|------|------|
| MARKET_CODE | str | 证券代码 |
| REPORTING_PERIOD | str | 报告期 |
| ANN_DATE | str | 公告日期 |
| ACTUAL_ANN_DATE | str | 实际公告日期 |
| TOTAL_ASSETS | float64 | 总资产(元) |
| NET_PRO_EXCL_MIN_INT_INC | float64 | 净利润(元) |
| TOT_OPERA_REV | float64 | 营业总收入(元) |
| TOTAL_PROFIT | float64 | 利润总额(元) |
| OPERA_PROFIT | float64 | 营业利润(元) |
| EPS_BASIC | float64 | 每股收益-基本(元) |
| TOT_SHARE_EQU_EXCL_MIN_INT | float64 | 股东权益合计(不含少数股东权益)(元) |
| IS_AUDIT | float64 | 是否审计 |
| ROE_WEIGHTED | float64 | 净资产收益率-加权(%) |
| LAST_YEAR_REVISED_NET_PRO | float64 | 去年同期修正后净利润 |
| PERFORMANCE_SUMMARY | str | 业绩简要说明 |
| NET_ASSET_PS | float64 | 每股净资产 |
| MEMO | str | 备注 |
| YOY_GR_GROSS_PRO | float64 | 同比增长率:营业利润 |
| YOY_GR_GROSS_REV | float64 | 同比增长率:营业总收入 |
| YOY_GR_NET_PROFIT_PARENT | float64 | 同比增长率:归属母公司股东的净利润 |
| YOY_GR_TOT_PRO | float64 | 同比增长率:利润总额 |
| YOY_ID_WAROE | float64 | 同比增减:加权平均净资产收益率 |
| YOY_GR_EPS_BASIC | float64 | 同比增长率:基本每股收益 |
| GROWTH_RATE_EQUITY | float64 | 比年初增长率:归属母公司的股东权益 |
| GROWTH_RATE_ASSETS | float64 | 比年初增长率:总资产 |
| GROWTH_RATE_NAPS | float64 | 比年初增长率:归属于母公司股东的每股净资产 |
| LAST_YEAR_TOT_OPERA_REV | float64 | 去年同期营业总收入 |
| LAST_YEAR_TOTAL_PROFIT | float64 | 去年同期利润总额 |
| LAST_YEAR_OPERA_PRO | float64 | 去年同期营业利润 |
| LAST_YEAR_EPS_DILUTED | float64 | 去年同期每股收益 |
| LAST_YEAR_NET_PROFIT | float64 | 去年同期净利润 |
| INITIAL_NET_ASSET_PS | float64 | 期初每股净资产 |
| INITIAL_NET_ASSETS | float64 | 期初净资产 |

### 示例代码

```python
import AmazingData as ad

ad.login(username='username', password='password', host='***.***.***.***', port=****)
info_data_object = ad.InfoData()
base_data_object = ad.BaseData()
calendar = base_data_object.get_calendar()
today = calendar[-1]
all_code_list = base_data_object.get_hist_code_list(
    security_type='EXTRA_STOCK_A_SH_SZ',
    start_date=20130101,
    end_date=today,
    local_path='D://AmazingData_local_data//'
)
profit_express = info_data_object.get_profit_express(all_code_list, local_path='D://AmazingData_local_data//')
```
