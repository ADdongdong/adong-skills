## 历史证券信息

**接口**: get_history_stock_status

**描述**: 获取指定股票列表的上市公司的历史证券数据，以日度为频率，包含历史的涨跌停、st、除权除息等信息

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| code_list | list[str] | 是 | 支持沪深A的的代码列表，可见示例 |
| local_path | str | 是 | 本地存储数据的路径，需绝对路径，格式类似"D://AmazingData_local_data//" |
| is_local | bool | 否 | 默认为True，本地数据缓存方案 |
| begin_date | int | 否 | 交易日，本地数据缓存方案 |
| end_date | int | 否 | 交易日，本地数据缓存方案 |

### 输出参数

返回DataFrame，字段说明：

| 参数 | 数据类型 | 字段说明 |
|------|------|------|
| MARKET_CODE | string | 证券代码 |
| TRADE_DATE | string | 日期 |
| PRECLOSE | float | 前收价 |
| HIGH_LIMITED | float | 涨停价 |
| LOW_LIMITED | float | 跌停价 |
| PRICE_HIGH_LMT_RATE | float | 涨停价上限 |
| PRICE_LOW_LMT_RATE | float | 跌停价下限 |
| IS_ST_SEC | string | 是否ST，1表示是，0表示否 |
| IS_SUSP_SEC | string | 是否停牌，1表示是，0表示否 |
| IS_WD_SEC | string | 是否除息，1表示是，0表示否 |
| IS_XR_SEC | string | 是否除权，1表示是，0表示否 |

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
history_stock_status = info_data_object.get_history_stock_status(all_code_list)
```
