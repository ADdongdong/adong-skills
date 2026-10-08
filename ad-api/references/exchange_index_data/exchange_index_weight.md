## 交易所指数成分股日权重

**接口**: get_index_weight

**描述**: 获取指定交易所指数列表的成分股日权重数据

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| code_list | list[str] | 是 | 支持指数列表；指数代码:支持以下5个指数上证50: 000016.SH沪深300: 000300.SH中证500: 000905.SH中证800: 000906.SH中证1000: 000852.SH |
| local_path | str | 是 | 本地存储数据的路径，需绝对路径，格式类似"'D://AmazingData_local_data//'" |
| is_local | bool | 否 | 默认为True，本地数据缓存方案 |
| begin_date | int | 否 | 变动日期，本地数据缓存方案 |
| end_date | int | 否 | 变动日期，本地数据缓存方案 |

### 输出参数

返回dict，key为code，value为DataFrame，index为日期。

| 字段 | 类型 | 说明 |
|------|------|------|
| INDEX_CODE | string | 指数代码 |
| CON_CODE | string | 标的代码 |
| TRADE_DATE | string | 生效日期 |
| TOTAL_SHARE | float | 总股本（股） |
| FREE_SHARE_RATIO | float | 自由流通比例（%）（归档后） |
| CALC_SHARE | float | 计算用股本（股） |
| WEIGHT_FACTOR | float | 权重因子 |
| WEIGHT | float | 权重（%） |
| CLOSE | float | 收盘价 |

### 示例代码

```python
import AmazingData as ad

ad.login(username='username', password='password', host='***.***.***.***', port=****)
info_data_object = ad.InfoData()
index_weight = info_data_object.get_index_weight(
    ['000016.SH', '000300.SH', '000905.SH', '000906.SH', '000852.SH'],
    is_local=False
)
```
