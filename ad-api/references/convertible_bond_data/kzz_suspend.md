## 可转债停复牌信息

**接口**: get_kzz_suspend

**描述**: 获取指定可转债列表的可转债停复牌信息数据

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| code_list | list[str] | 是 | 支持可转债的代码列表 |
| local_path | str | 是 | 本地存储数据的路径，需绝对路径，格式类似"'D://AmazingData_local_data//'" |
| is_local | bool | 否 | 默认为True，本地数据缓存方案 |

### 输出参数

返回dict，key为code，value为DataFrame，主要字段包含：

| 字段 | 类型 | 说明 | 备注 |
|------|------|------|------|
| MARKET_CODE | string | 市场代码 | |
| SUSPEND_DATE | string | 停牌日期 | |
| SUSPEND_TYPE | int | 停牌类型代码001-上午停牌002-下午停牌003-今起停牌004-盘中停牌007-停牌1小时016-停牌1天 | 001:上午停牌 002:下午停牌 003:今起停牌 004:盘中停牌 007:停牌1小时 016:停牌1天 |
| RESUMP_DATE | string | 复牌日期 | |
| CHANGE_REASON | string | 停牌原因 | |
| CHANGE_REASON_CODE | int | 停牌原因代码 | |
| RESUMP_TIME | string | 停复牌时间 | |

### 示例代码

```python
import AmazingData as ad

ad.login(username='username', password='password', host='***.***.***.***', port=****)
info_data_object = ad.InfoData()
base_data_object = ad.BaseData()
code_list = base_data_object.get_code_list('EXTRA_KZZ')
kzz_suspend = info_data_object.get_kzz_suspend(code_list, is_local=False)
```
