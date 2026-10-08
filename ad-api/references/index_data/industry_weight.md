## 行业指数成分股日权重

**接口**: get_industry_weight

**描述**: 获取指定行业指数列表的成分股日权重数据

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
| WEIGHT | float | 权重 |
| CON_CODE | string | 成份股代码 |
| TRADE_DATE | string | 交易日期 |
| INDEX_CODE | string | 指数代码 |

### 示例代码

```python
import AmazingData as ad

ad.login(username='username', password='password', host='***.***.***.***', port=****)
info_data_object = ad.InfoData()
industry_base_info = info_data_object.get_industry_base_info()
industry_base_list = list(industry_base_info['INDEX_CODE'])
industry_weight = info_data_object.get_industry_weight(industry_base_list)
```
