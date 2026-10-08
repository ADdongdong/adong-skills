## 期权标准合约属性

**接口**: get_option_std_ctr_specs

**描述**: 获取指定期权标准合约属性（沪深交易所的ETF期权）

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| code_list | list[str] | 是 | 支持沪深ETF的的代码列表，目前包含159919.SZ159915.SZ159922.SZ159901.SZ510300.SH588000.SH588080.SH510050.SH510500.SH |
| local_path | str | 是 | 本地存储数据的路径，需绝对路径，格式类似"'D://AmazingData_local_data//'" |
| is_local | bool | 否 | 默认为True，本地数据缓存方案 |

### 输出参数

返回DataFrame，column为option_std_ctr_specs的字段，index为序号。

| 字段 | 类型 | 说明 | 备注 |
|------|------|------|------|
| EXERCISE_DATE | string | 期权行权日 | |
| CONTRACT_UNIT | int | 合约单位 | |
| POSITION_DECLARE_MIN | string | 头寸申报下限 | |
| QUOTE_CURRENCY_UNIT | string | 报价货币单位 | |
| LAST_TRADING_DATE | string | 最后交易日 | |
| POSITION_LIMIT | string | 头寸限制 | |
| DELIST_DATE | string | 退市日期 | |
| NOTIONAL_VALUE | string | 立约价值 | |
| EXERCISE_METHOD | string | 行权方式 | |
| DELIVERY_METHOD | string | 交割方式 | |
| SETTLEMENT_MONTH | string | 合约结算月份 | |
| TRADING_FEE | string | 交易费用 | |
| EXCHANGE_NAME | string | 交易所名称 | |
| OPTION_EN_NAME | string | 期权英文名称 | |
| CONTRACT_VALUE | float | 合约价值 | |
| IS_SIMULATION | int | 是否仿真合约 | 0否 1是 |
| CONTRACT_UNIT_DIMENSION | string | 合约单位量纲 | |
| OPTION_STRIKE_PRICE | string | 期权行权价 | |
| IS_SIMULATION_TRADE | string | 是否仿真交易 0 否 1 是 | 0否 1是 |
| LISTED_DATE | string | 上市日期 | |
| OPTION_NAME | string | 期权名称 | |
| PREMIUM | string | 期权金 | |
| OPTION_TYPE | string | 期权类型 | ETF期权等 |
| TRADING_HOURS_DESC | string | 交易时间说明 | |
| FINAL_SETTLEMENT_DATE | string | 最后结算日 | |
| FINAL_SETTLEMENT_PRICE | string | 最后结算价 | |
| MIN_PRICE_UNIT | string | 最小报价单位 | |
| MARKET_CODE | string | 市场代码 | |
| CONTRACT_MULTIPLIER | int | 合约乘数 | |

### 示例代码

```python
import AmazingData as ad

ad.login(username='username', password='password', host='***.***.***.***', port=****)
info_data_object = ad.InfoData()
option_std_ctr_specs = info_data_object.get_option_std_ctr_specs(['510050.SH'], is_local=False)
```
