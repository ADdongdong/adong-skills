## 交易所指数成分股

**接口**: get_index_constituent

**描述**: 获取指定交易所指数列表的成分股数据

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| code_list | list[str] | 是 | 支持沪深指数的的代码列表，可见示例，仅支持常用指数，约600多只，无返回数据则不支持。 |
| local_path | str | 是 | 本地存储数据的路径，需绝对路径，格式类似"'D://AmazingData_local_data//'" |
| is_local | bool | 否 | 默认为True，仅从本地获取，不从服务器获取数据；False ，仅从服务器获取，不从本地获取数据；因为原始数据的剔除日期会根据最新数据修改，所以第一次运行is_local 需要设置成 False 才会从服务器获取数据。 |

### 输出参数

返回dict，key为code，value为DataFrame，index为日期。

| 字段 | 类型 | 说明 | 备注 |
|------|------|------|------|
| INDEX_CODE | string | 指数代码 | |
| CON_CODE | string | 成份股代码 | |
| INDATE | string | 纳入日期 | |
| OUTDATE | string | 剔除日期 | 未剔除时为nan |
| INDEX_NAME | string | 指数名称 | |

### 示例代码

```python
import AmazingData as ad

ad.login(username='username', password='password', host='***.***.***.***', port=****)
info_data_object = ad.InfoData()
base_data_object = ad.BaseData()
code_list = base_data_object.get_code_list(security_type='EXTRA_INDEX_A')
index_constituent = info_data_object.get_index_constituent(code_list, is_local=False)
```
