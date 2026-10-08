## 融资融券成交汇总

**接口**: get_margin_summary

**描述**: 获取指定日期的上市公司的融资融券成交汇总数据

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| local_path | str | 是 | 本地存储数据的路径，需绝对路径，格式类似"'D://AmazingData_local_data//'" |
| is_local | bool | 否 | 默认为True，本地数据缓存方案 |
| begin_date | int | 否 | 交易日，本地数据缓存方案 |
| end_date | int | 否 | 交易日，本地数据缓存方案 |

### 输出参数

返回DataFrame，主要字段包含：

| 字段名称 | 类型 | 字段说明 |
|------|------|------|
| TRADE_DATE | string | 交易日期 |
| SUM_BORROW_MONEY_BALANCE | float | 融资余额(元) |
| SUM_PURCH_WITH_BORROW_MONEY | float | 融资买入额(元) |
| SUM_REPAYMENT_OF_BORROW_MONEY | float | 融资偿还额(元) |
| SUM_SEC_LENDING_BALANCE | float | 融券余额(元) |
| SUM_SALES_OF_BORROWED_SEC | int | 融券卖出量(股,份,手) |
| SUM_MARGIN_TRADE_BALANCE | float | 融资融券余额(元) |

### 示例代码

```python
import AmazingData as ad

ad.login(username='username', password='password', host='***.***.***.***', port=****)
info_data_object = ad.InfoData()
margin_summary = info_data_object.get_margin_summary()
```
