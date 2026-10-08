## 可转债回售赎回条款

**接口**: get_kzz_put_call_item

**描述**: 获取指定可转债列表的可转债回售赎回条款数据

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
| MAND_PUT_PERIOD | string | 无条件回售期 |
| MAND_PUT_PRICE | float | 无条件回售价 |
| MAND_PUT_START_DATE | string | 无条件回售开始日期 |
| MAND_PUT_END_DATE | string | 无条件回售结束日期 |
| MAND_PUT_TEXT | string | 无条件回售文字条款 |
| IS_MAND_PUT_CONTAIN_CURRENT | int | 无条件回售是否含当期利息 |
| CON_PUT_START_DATE | string | 有条件回售起始日期 |
| CON_PUT_END_DATE | string | 有条件回售结束日期 |
| MAX_PUT_TRI_PER | float | 回售触发计算最大时间区间 |
| PUT_TRI_PERIOD | float | 回售触发计算时间区间 |
| ADD_PUT_CON | string | 附加回售条件 |
| ADD_PUT_PRICE_INS | string | 股价回售价格说明 |
| PUT_NUM_INS | string | 回售次数说明 |
| PUT_PRO_PERIOD | float | 相对回售期（月） |
| PUT_NO_PERY | float | 每年回售次数 |
| IS_PUT_ITEM | int | 是否有回售条款 |
| IS_TERM_PUT_ITEM | int | 是否有到期回售条款 |
| IS_MAND_PUT_ITEM | int | 是否有无条件回售条款 |
| IS_TIME_PUT_ITEM | int | 是否有时点回售条款 |
| TIME_PUT_NO | float | 时点回售数 |
| TIME_PUT_ITEM | string | 时点回售文字条款 |
| TERM_PUT_PRICE | float | 到期回售价 |
| CON_CALL_START_DATE | string | 有条件赎回起始日期 |
| CON_CALL_END_DATE | string | 有条件赎回结束日期 |
| CALL_TRI_CON_INS | string | 赎回触发条件说明 |
| MAX_CALL_TRI_PER | float | 赎回触发计算最大时间区间 |
| CALL_TRI_PER | float | 赎回触发计算时间区间 |
| CALL_NUM_BER_INS | string | 赎回次数说明 |
| IS_CALL_ITEM | int | 是否有赎回条款 |
| CALL_PRO_PERIOD | float | 相对赎回期（月） |
| CALL_NO_PERY | float | 每年赎回次数 |
| IS_TIME_CALL_ITEM | int | 是否有时点赎回条款 |
| TIME_CALL_NO | float | 时点赎回数 |
| TIME_CALL_TEXT | string | 时点赎回文字条款 |
| EXPIRED_REDEMPTION_PRICE | float | 到期赎回价 |
| PUT_TRI_CON_DESC | string | 回售触发条件说明 |

### 示例代码

```python
import AmazingData as ad

ad.login(username='username', password='password', host='***.***.***.***', port=****)
info_data_object = ad.InfoData()
base_data_object = ad.BaseData()
code_list = base_data_object.get_code_list('EXTRA_KZZ')
kzz_put_call_item = info_data_object.get_kzz_put_call_item(code_list, is_local=False)
```
