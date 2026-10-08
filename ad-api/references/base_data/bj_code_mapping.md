## 北交所代码对照

**接口**: get_bj_code_mapping

**描述**: 获取北交所的存量上市公司股票新旧代码对照表

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| local_path | str | 是 | 本地存储数据的路径，需绝对路径，格式类似"'D://AmazingData_local_data//'" |
| is_local | bool | 否 | 默认为True，首选从本地读取，读取失败再从服务器取数据False，以本地数据为基础，增量从服务器取数据 |

### 输出参数

返回DataFrame，字段说明：

| 字段名称 | 类型 | 字段说明 |
|------|------|------|
| OLD_CODE | string | 旧代码 |
| NEW_CODE | string | 新代码 |
| LISTING_DATE | int | 上市日期 |
| SECURITY_NAME | string | 证券简称 |

### 示例代码

```python
import AmazingData as ad

ad.login(username='username', password='password', host='***.***.***.***', port=****)
info_data_object = ad.InfoData()
bj_code_mapping = info_data_object.get_bj_code_mapping(
    local_path='D://AmazingData_local_data//',
    is_local=True
)
```
