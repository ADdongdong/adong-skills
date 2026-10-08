## 历史K线

**接口**: query_kline

**描述**: K线数据的历史数据查询接口，支持全部周期的K线数据查询

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| code_list | list:[str] | 是 | 可传入列表，支持北交所、上交所、深交所的可转债、股票、指数、ETF等品种，上交所、深交所的ETF期权；支持期货（中金所） |
| begin_date | int | 是 | 日期，填写8位的整型格式的日期，比如20240101 |
| end_date | int | 是 | 日期，填写8位的整型格式的日期，比如20240201 |
| period | Period | 是 | 数据周期Period（见附录） |
| begin_time | int | 否 | 时分的时间戳，填写3位或4位的整型格式的日期，时占一位或两位，分占两位，，例如9点整为900, 17点25分为1725 |
| end_time | int | 否 | 时分的时间戳，填写3位或4位的整型格式的日期，时占一位或两位，分占两位，，例如9点整为900, 17点25分为1725 |

### 输出参数

返回dict，字典的key为代码，value为DataFrame：
- column为[K线数据Kline（见附录）](../appendix.md#k线-kline)
- index为日期（datetime）

详细字段请参考[附录数据结构说明](../appendix.md#数据结构说明)

### 示例代码

```python
import AmazingData as ad

ad.login(username='username', password='password', host='***.***.***.***', port=****)
base_data_object = ad.BaseData()
code_list = base_data_object.get_code_list(security_type='EXTRA_STOCK_A')
calendar = base_data_object.get_calendar()
market_data_object = ad.MarketData(calendar)
kline_dict = market_data_object.query_kline(code_list, begin_date=20240530, end_date=20240530, period=ad.constant.Period.day.value)
```
