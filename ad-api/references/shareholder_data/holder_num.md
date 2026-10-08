## 股东户数

**接口**: get_holder_num

**描述**: 获取指定股票列表的上市公司的股东户数数据

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| code_list | list[str] | 是 | 支持沪深A的的代码列表，可见示例 |
| local_path | str | 是 | 本地存储数据的路径，需绝对路径，格式类似"'D://AmazingData_local_data//'" |
| is_local | bool | 否 | 默认为True，本地数据缓存方案 |
| begin_date | int | 否 | 股东户数统计的截止日期，本地数据缓存方案 |
| end_date | int | 否 | 股东户数统计的截止日期，本地数据缓存方案 |

### 输出参数

返回DataFrame，主要字段包含：

| 字段名称 | 类型 | 字段说明 |
|------|------|------|
| MARKET_CODE | string | 证券代码 |
| ANN_DT | string | 公告日期 |
| HOLDER_ENDDATE | string | 股东户数统计的截止日期 |
| HOLDER_TOTAL_NUM | float | A股、B股、H股、境外股的总户数 |
| HOLDER_NUM | float | A股股东户数 |

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
holder_num = info_data_object.get_holder_num(all_code_list, local_path='D://AmazingData_local_data//')
```
