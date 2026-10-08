## 龙虎榜

**接口**: get_long_hu_bang

**描述**: 获取指定股票列表的上市公司的龙虎榜数据

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| code_list | list[str] | 是 | 支持沪深A的的代码列表，可见示例 |
| local_path | str | 是 | 本地存储数据的路径，需绝对路径，格式类似"'D://AmazingData_local_data//'" |
| is_local | bool | 否 | 默认为True，本地数据缓存方案 |
| begin_date | int | 否 | 交易日，本地数据缓存方案 |
| end_date | int | 否 | 交易日，本地数据缓存方案 |

### 输出参数

返回DataFrame，主要字段包含：

| 字段 | 类型 | 说明 | 备注 |
|------|------|------|------|
| MARKET_CODE | string | 证券代码 | |
| TRADE_DATE | string | 交易日期 | |
| SECURITY_NAME | string | 证券名称 | |
| REASON_TYPE | string | 上榜原因类型 | |
| REASON_TYPE_NAME | string | 上榜原因 | |
| CHANGE_RANGE | float | 涨跌幅(%) | |
| TRADER_NAME | string | 营业部名称 | |
| BUY_AMOUNT | float | 买入金额(元) | |
| SELL_AMOUNT | float | 卖出金额(元) | |
| FLOW_MARK | int | 买卖表示 | 1表示买入，2表示卖出 |
| TOTAL_AMOUNT | float | 实际交易金额(元) | |
| TOTAL_VOLUME | float | 实际交易量(万股) | |

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
long_hu_bang = info_data_object.get_long_hu_bang(all_code_list, local_path='D://AmazingData_local_data//')
```
