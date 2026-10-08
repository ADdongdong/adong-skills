## 可转债赎回数据

**接口**: get_kzz_call

**描述**: 获取指定可转债列表的可转债赎回数据

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| code_list | list[str] | 是 | 支持可转债的代码列表 |
| local_path | str | 是 | 本地存储数据的路径，需绝对路径，格式类似"'D://AmazingData_local_data//'" |
| is_local | bool | 否 | 默认为True，本地数据缓存方案 |

### 输出参数

返回dict，key为code，value为DataFrame，主要字段包含：

| 字段 | 类型 | 说明 |
|------|------|------|
| MARKET_CODE | string | 市场代码 |
| CALL_PRICE | float | 赎回价 |
| BEGIN_DATE | string | 起始日期 |
| END_DATE | string | 截止日期 |
| TRI_RATIO | float | 触发比例(%) |

### 示例代码

```python
import AmazingData as ad

ad.login(username='username', password='password', host='***.***.***.***', port=****)
info_data_object = ad.InfoData()
base_data_object = ad.BaseData()
code_list = base_data_object.get_code_list('EXTRA_KZZ')
kzz_call = info_data_object.get_kzz_call(code_list, is_local=False)
```
