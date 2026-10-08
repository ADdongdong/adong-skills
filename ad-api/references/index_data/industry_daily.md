## 行业指数日行情

**接口**: get_industry_daily

**描述**: 获取指定行业指数列表的日行情数据

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| code_list | list[str] | 是 | 支持行业指数的的代码列表，可见示例，仅从get_industry_base_info取到的指数代码。 |
| local_path | str | 是 | 本地存储数据的路径，需绝对路径，格式类似"'D://AmazingData_local_data//'" |
| is_local | bool | 否 | 默认为True，本地数据缓存方案 |
| begin_date | int | 否 | 交易日期，本地数据缓存方案 |
| end_date | int | 否 | 交易日期，本地数据缓存方案 |

### 输出参数

返回dict，key为code，value为DataFrame，主要字段包含：

| 字段 | 类型 | 说明 |
|------|------|------|
| OPEN | float | 开盘价 |
| HIGH | float | 最高价 |
| CLOSE | float | 收盘价 |
| LOW | float | 最低价 |
| AMOUNT | float | 成交金额(元) |
| VOLUME | float | 成交量(股) |
| PB | float | 指数市净率 |
| PE | float | 指数市盈率 |
| TOTAL_CAP | float | 总市值(万元) |
| A_FLOAT_CAP | float | A股流通市值(万元) |
| INDEX_CODE | string | 指数代码 |
| PRE_CLOSE | float | 昨收盘价 |
| TRADE_DATE | string | 交易日期 |

### 示例代码

```python
import AmazingData as ad

ad.login(username='username', password='password', host='***.***.***.***', port=****)
info_data_object = ad.InfoData()
industry_base_info = info_data_object.get_industry_base_info()
industry_base_list = list(industry_base_info['INDEX_CODE'])
industry_daily = info_data_object.get_industry_daily(industry_base_list, is_local=False)
```
