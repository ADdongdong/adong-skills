## 历史快照

**接口**: query_snapshot

**描述**: 快照数据的历史数据查询接口

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| code_list | list:[str] | 是 | 可传入列表，支持北交所、上交所、深交所的可转债、股票、指数、ETF、港股通等、ETF期权等品种 |
| begin_date | int | 是 | 日期，填写8位的整型格式的日期，比如20240101 |
| end_date | int | 是 | 日期，填写8位的整型格式的日期，比如20240201 |
| begin_time | int | 否 | 时分秒毫秒的时间戳，填写8位或9位的整型格式的日期，时占一位或两位，分占两位，秒占两位，毫秒占三位，例如9点整为90000000, 17点25分为172500000 |
| end_time | int | 否 | 时分秒毫秒的时间戳，填写8位或9位的整型格式的日期，时占一位或两位，分占两位，秒占两位，毫秒占三位，例如9点整为90000000, 17点25分为172500000 |

### 输出参数

返回dict，字典的key为代码，value为DataFrame：
- column为快照数据（指数为[SnapshotIndex](../appendix.md#指数快照-snapshotindex)，股票/ETF/可转债为[Snapshot](../appendix.md#level-1快照-snapshot)，港股通为[SnapshotHKT](../appendix.md#港股通快照-snapshothkt)，ETF期权为[SnapshotOption](../appendix.md#etf期权快照-snapshotoption)）
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
snapshot_dict = market_data_object.query_snapshot(code_list, begin_date=20240530, end_date=20240530)
```
