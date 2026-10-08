## 分红数据

**接口**: get_dividend

**描述**: 获取指定股票列表的上市公司的分红数据

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| code_list | list[str] | 是 | 支持沪深A的的代码列表，可见示例 |
| local_path | str | 是 | 本地存储数据的路径，需绝对路径，格式类似"'D://AmazingData_local_data//'" |
| is_local | bool | 否 | 默认为True，本地数据缓存方案 |
| begin_date | int | 否 | 公告日期，本地数据缓存方案 |
| end_date | int | 否 | 公告日期，本地数据缓存方案 |

### 输出参数

返回DataFrame，主要字段包含：

| 字段名称 | 类型 | 字段说明 | 备注 |
|------|------|------|------|
| MARKET_CODE | string | 证券代码 |
| DIV_PROGRESS | string | 方案进度 |
| DVD_PER_SHARE_STK | float | 每股送转 |
| DVD_PER_SHARE_PRE_TAX_CASH | float | 每股派息(税前)(元) |
| DVD_PER_SHARE_AFTER_TAX_CASH | float | 每股派息(税后)(元) |
| DATE_EQY_RECORD | string | 股权登记日 |
| DATE_EX | string | 除权除息日 |
| DATE_DVD_PAYOUT | string | 派息日 |
| LISTINGDATE_OF_DVD_SHR | string | 红股上市日 |
| DIV_PRELANDATE | string | 预案公告日 |
| DIV_SMTGDATE | string | 股东大会公告日 |
| DATE_DVD_ANN | string | 分红实施公告日 |
| DIV_BASEDATE | string | 基准日期 |
| DIV_BASESHARE | float | 基准股本(万股) |
| CURRENCY_CODE | string | 货币代码 |
| ANN_DATE | string | 公告日期 |
| IS_CHANGED | int | 方案是否变更 |
| REPORT_PERIOD | string | 分红年度 |
| DIV_CHANGE | string | 方案变更说明 |
| DIV_BONUSRATE | float | 每股送股比例 |
| DIV_CONVERSEDRATE | float | 每股转增比例 |
| REMARK | string | 备注 |
| DIV_PREANN_DATE | string | 预案预披露公告日 |
| DIV_TARGET | string | 分红对象 |

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
dividend = info_data_object.get_dividend(all_code_list, local_path='D://AmazingData_local_data//')
```
