## 可转债转股数据

**接口**: get_kzz_conv

**描述**: 获取指定可转债列表的可转债转股数据

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
| ANN_DATE | string | 公告日期 |
| CONV_CODE | string | 转股申报代码 |
| CONV_NAME | string | 转股简称 |
| CONV_PRICE | float | 股转价格 |
| CURRENCY_CODE | string | 股转申报代码 |
| CONV_START_DATE | string | 自愿转换期起始日 |
| CONV_END_DATE | string | 自愿转换期截止日 |
| TRADE_DATE_LAST | string | 可转换债停止交易日 |
| FORCED_CONV_DATE | string | 强制转换日 |
| FORCED_CONV_PRICE | float | 强制转换价格 |
| REL_CONV_MONTH | float | 相对转换期(月) |
| IS_FORCED | float | 是否强制转股 |
| FORCED_CONV_REASON | string | 强制转换原因 |

### 示例代码

```python
import AmazingData as ad

ad.login(username='username', password='password', host='***.***.***.***', port=****)
info_data_object = ad.InfoData()
base_data_object = ad.BaseData()
code_list = base_data_object.get_code_list('EXTRA_KZZ')
kzz_conv = info_data_object.get_kzz_conv(code_list, is_local=False)
```
