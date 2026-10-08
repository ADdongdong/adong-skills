## 可转债赎回条款执行说明

**接口**: get_kzz_call_explanation

**描述**: 获取指定可转债列表的可转债赎回条款执行说明数据

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
| CALL_PRICE | float | 每百元面值赎回价格(元) |
| CALL_ANNOUNCEMENT_DATE | string | 赎回公告日 |
| CALL_FUL_RES_ANN_DATE | string | 赎回履行结果公告日 |
| CALL_AMOUNT | float | 赎回总面额(亿元) |
| CALL_OUTSTANDING_AMOUNT | float | 继续托管总面额（亿元） |
| CALL_DATE_PUB | string | 赎回日（公布） |
| CALL_FUND_ARRIVAL_DATE | string | 赎回资金到账日 |
| CALL_RECORD_DAY | string | 赎回登记日 |
| CALL_REASON | string | 赎回原因 |
| CALL_DATE​ | string | 赎回日 |

### 示例代码

```python
import AmazingData as ad

ad.login(username='username', password='password', host='***.***.***.***', port=****)
info_data_object = ad.InfoData()
base_data_object = ad.BaseData()
code_list = base_data_object.get_code_list('EXTRA_KZZ')
kzz_call_explanation = info_data_object.get_kzz_call_explanation(code_list, is_local=False)
```
