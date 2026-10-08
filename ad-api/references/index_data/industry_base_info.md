## 行业指数基本信息

**接口**: get_industry_base_info

**描述**: 获取行业指数的基本信息数据

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| local_path | str | 是 | 本地存储数据的路径，需绝对路径，格式类似"'D://AmazingData_local_data//'" |
| is_local | bool | 否 | 默认为True，仅从本地获取，不从服务器获取数据；False ，仅从服务器获取，不从本地获取数据；因为原始数据的剔除日期会根据最新数据修改，所以第一次运行is_local 需要设置成 False 才会从服务器获取数据。 |

### 输出参数

返回dict，key为code，value为DataFrame，index为日期。

| 字段 | 类型 | 说明 | 备注 |
|------|------|------|------|
| INDEX_CODE | string | 指数代码 | |
| INDUSTRY_CODE | string | 行业代码 | |
| LEVEL_TYPE | int | 指数类别1:一级行业2:二级行业3:三级行业 | 1:一级行业, 2:二级行业, 3:三级行业 |
| LEVEL1_NAME | string | 一级行业 | |
| LEVEL2_NAME | string | 二级行业 | |
| LEVEL3_NAME | string | 三级行业 | |
| IS_PUB | int | 是否发布 | 1:已发布, 2:未发布 |
| CHANGE_REASON | string | 变动原因 | |

### 示例代码

```python
import AmazingData as ad

ad.login(username='username', password='password', host='***.***.***.***', port=****)
info_data_object = ad.InfoData()
industry_base_info = info_data_object.get_industry_base_info()
```
