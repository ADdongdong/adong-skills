## 股权冻结/质押

**接口**: get_equity_pledge_freeze

**描述**: 获取指定股票列表的上市公司的股权冻结/质押数据

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| code_list | list[str] | 是 | 支持沪深A的的代码列表，可见示例 |
| local_path | str | 是 | 本地存储数据的路径，需绝对路径，格式类似"'D://AmazingData_local_data//'" |
| is_local | bool | 否 | 默认为True，本地数据缓存方案 |
| begin_date | int | 否 | 公告日期，本地数据缓存方案 |
| end_date | int | 否 | 公告日期，本地数据缓存方案 |

### 输出参数

返回dict，key为code，value为DataFrame，主要字段包含：

| 字段名称 | 类型 | 字段说明 | 备注 |
|------|------|------|------|
| MARKET_CODE | string | 证券代码 |
| ANN_DATE | string | 公告日期 |
| HOLDER_NAME | string | 股东名称 |
| HOLDER_TYPE_CODE | int | 股东类型代码 |
| TOTAL_HOLDING_SHR_RATIO | float | 持股总数占公司总股本比例 |
| FRO_SHARES | float | 本次冻结/质押股数 |
| FRO_SHR_TO_TOTAL_HOLDING_RATIO | float | 本次冻结/质押占所持股比例 |
| FRO_SHR_TO_TOTAL_RATIO | float | 本次冻结/质押占总股本比例 |
| TOTAL_PLEDGE_SHR | float | 累计冻结/质押股数 |
| IS_EQUITY_PLEDGE_REPO | int | 是否股权质押回购 |
| BEGIN_DATE | string | 冻结/质押起始日 |
| END_DATE | string | 解冻/解押日期 |
| IS_DISFROZEN | int | 是否质押或解冻 |
| FROZEN_INSTITUTION | string | 执行冻结机构/质权方 |
| DISFROZEN_TIME | string | 解压或解冻日期 |
| SHR_CATEGORY_CODE | int | 股份性质类别代码 |
| FREEZE_TYPE | int | 冻结/质押类型 |
| TOTAL_HOLDING_SHR" | float | 持股总数（万股） |  |

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
equity_pledge_freeze = info_data_object.get_equity_pledge_freeze(all_code_list, local_path='D://AmazingData_local_data//')
```
