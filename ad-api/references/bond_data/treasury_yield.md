## 国债收益率

**接口**: get_treasury_yield

**描述**: 获取指定期限的国债收益率数据

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| term_list | list[str] | 是 | 支持不同期限的国债收益率'm3':3个月,'m6':6个月, 'y1':1年, 'y2':2年, 'y3':3年, 'y5':5年, 'y7':7年, 'y10':10年, 'y30':30年 |
| local_path | str | 是 | 本地存储数据的路径，需绝对路径，格式类似"'D://AmazingData_local_data//'" |
| is_local | bool | 否 | 默认为True，本地数据缓存方案 |
| begin_date | int | 否 | 变动日期，本地数据缓存方案 |
| end_date | int | 否 | 变动日期，本地数据缓存方案 |

### 输出参数

返回dict，key为期限，value为DataFrame，主要字段包含：

| 字段 | 类型 | 说明 |
|------|------|------|
| datetime | trade_time | 交易所行情数据时间 |
| float | pre_close | 昨收价 |
| int | volume | 成交总量 |
| str | code | 证券代码+市场 |

### 示例代码

```python
import AmazingData as ad

ad.login(username='username', password='password', host='***.***.***.***', port=****)
info_data_object = ad.InfoData()
treasury_yield = info_data_object.get_treasury_yield(['m3', 'm6', 'y1', 'y2', 'y3', 'y5', 'y7', 'y10', 'y30'])
```
