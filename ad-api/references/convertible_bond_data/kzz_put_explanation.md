## 可转债回售条款执行说明

**接口**: get_kzz_put_explanation

**描述**: 获取指定可转债列表的可转债回售条款执行说明数据

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
| PUT_FUND_ARRIVAL_DATE | string | 回售资金到账日 |
| PUT_PRICE | float | 每百元面值回收价格（元） |
| PUT_ANNOUNCEMENT_DATE | string | 回售公告日 |
| PUT_EX_DATE | string | 回售履行结果公告日 |
| PUT_AMOUNT | float | 回售总面额（亿元） |
| PUT_OUTSTANDING | float | 继续托管总面额（亿元） |
| REPURCHASE_START_DATE | string | 回售行使开始日 |
| REPURCHASE_END_DATE | string | 回售行使截止日 |
| RESALE_START_DATE | string | 转售开始日 |
| FUND_END_DATE | string | 回售日 |
| REPURCHASE_CODE | string | 回售代码 |
| RESALE_AMOUNT | float | 转售总面额（亿元） |
| RESALE_IMP_AMOUNT | float | 实施转售总面额（亿元） |
| RESALE_END_DATE | string | 转售截止日 |

### 示例代码

```python
import AmazingData as ad

ad.login(username='username', password='password', host='***.***.***.***', port=****)
info_data_object = ad.InfoData()
base_data_object = ad.BaseData()
code_list = base_data_object.get_code_list('EXTRA_KZZ')
kzz_put_explanation = info_data_object.get_kzz_put_explanation(code_list, is_local=False)
```
