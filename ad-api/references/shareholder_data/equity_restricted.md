## 限售股解禁

**接口**: get_equity_restricted

**描述**: 获取指定股票列表的上市公司的限售股解禁数据

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| code_list | list[str] | 是 | 支持沪深A的的代码列表，可见示例 |
| local_path | str | 是 | 本地存储数据的路径，需绝对路径，格式类似"'D://AmazingData_local_data//'" |
| is_local | bool | 否 | 默认为True，本地数据缓存方案 |
| begin_date | int | 否 | 解禁日期，本地数据缓存方案 |
| end_date | int | 否 | 解禁日期，本地数据缓存方案 |

### 输出参数

返回dict，key为code，value为DataFrame，主要字段包含：

| 字段名称 | 类型 | 字段说明 | 备注 |
|------|------|------|------|
| MARKET_CODE | string | 证券代码 |
| LIST_DATE | string | 解禁日期 |
| SHARE_RATIO | float | 解禁股占总股本比(%) |
| SHARE_LST_TYPE_NAME | string | 解禁股份类型名称 |
| SHARE_LST | int | 解禁数量(股) |
| SHARE_LST_IS_ANN | int | 上市数量是否公布值 |
| CLOSE_PRICE | float | 前日收盘价(元) |
| SHARE_LST_MARKET_VALUE | float | 解禁市值(元) |

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
equity_restricted = info_data_object.get_equity_restricted(all_code_list, local_path='D://AmazingData_local_data//')
```
