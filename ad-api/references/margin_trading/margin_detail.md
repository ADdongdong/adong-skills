## 融资融券交易明细

**接口**: get_margin_detail

**描述**: 获取指定股票列表的上市公司的融资融券交易明细数据

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
| SECURITY_NAME | string | 证券简称 |
| TRADE_DATE | string | 交易日期 |
| PURCH_WITH_BORROW_MONEY | float | 融资买入额(元) |
| REPAYMENT_OF_BORROW_MONEY | float | 融资偿还额(元) |
| SEC_LENDING_BALANCE | float | 融券余额(元) |
| SALES_OF_BORROWED_SEC | int | 融券卖出量(股,份,手) |
| REPAYMENT_OF_BORROW_SEC | int | 融券偿还量(股,份,手) |
| SEC_LENDING_BALANCE_VOL | int | 融券余量(股,份,手) |
| MARGIN_TRADE_BALANCE | float | 融资融券余额(元) |
| BORROW_MONEY_BALANCE" | float | 融资余额(元) |

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
margin_detail = info_data_object.get_margin_detail(all_code_list, local_path='D://AmazingData_local_data//')
```
