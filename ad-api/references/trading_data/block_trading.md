## 大宗交易

**接口**: get_block_trading

**描述**: 获取指定股票列表的大宗交易数据

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

| 字段名称 | 类型 | 字段说明 |
|------|------|------|
| MARKET_CODE | string | 证券代码 |
| TRADE_DATE | string | 交易日期 |
| B_SHARE_PRICE | float | 成交价(元) |
| B_SHARE_VOLUME | float | 成交量(万股) |
| B_FREQUENCY | int | 笔数 |
| BLOCK_AVG_VOLUME | float | 每笔成交数量(万股份) |
| B_SHARE_AMOUNT | float | 成交金额(万元) |
| B_BUYER_NAME | string | 买方营业部名称 |
| B_SELLER_NAME | string | 卖方营业部名称 |

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
block_trading = info_data_object.get_block_trading(all_code_list, local_path='D://AmazingData_local_data//')
```
