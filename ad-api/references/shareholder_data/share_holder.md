## 十大股东数据

**接口**: get_share_holder

**描述**: 获取指定股票列表的上市公司的十大股东数据

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| code_list | list[str] | 是 | 支持沪深A的的代码列表，可见示例 |
| local_path | str | 是 | 本地存储数据的路径，需绝对路径，格式类似"'D://AmazingData_local_data//'" |
| is_local | bool | 否 | 默认为True，本地数据缓存方案 |
| begin_date | int | 否 | 到期日期，本地数据缓存方案 |
| end_date | int | 否 | 到期日期，本地数据缓存方案 |

### 输出参数

返回DataFrame，主要字段包含：

| 字段名称 | 类型 | 字段说明 |
|------|------|------|
| ANN_DATE | str | 公告日期 |
| MARKET_CODE | str | 证券代码 |
| HOLDER_ENDDATE | str | 到期日期 |
| HOLDER_TYPE | int | 股东类别 |
| QTY_NUM | int | 持股量序号 |
| HOLDER_NAME | str | 股东名称 |
| HOLDER_HOLDER_CATEGORY | int | 股东性质 |
| HOLDER_PCT | float | 持股比例(%) |
| HOLDER_SHARECATEGORYNAME | str | 股份类型 |
| FLOAT_QTY | float | 流通股数量 |
| HOLDER_QUANTITY, | float | 持股数（股） |  |

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
share_holder = info_data_object.get_share_holder(all_code_list, local_path='D://AmazingData_local_data//')
```
