## 期权基本资料

**接口**: get_option_basic_info

**描述**: 获取指定期权的基本资料（沪深交易所的ETF期权）

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| code_list | list[str] | 是 | 支持沪深ETF期权的的代码列表，可见示例 |
| local_path | str | 是 | 本地存储数据的路径，需绝对路径，格式类似"'D://AmazingData_local_data//'" |
| is_local | bool | 否 | 默认为True，本地数据缓存方案 |

### 输出参数

返回DataFrame，column为option_basic_info的字段，index为序号。

| 字段 | 类型 | 说明 | 备注 |
|------|------|------|------|
| CONTRACT_FULL_NAME | string | 合约全称 | |
| CONTRACT_TYPE | string | 合约类别 | C表示认购，P表示认沽 |
| DELIVERY_MONTH | string | 交割月份 | |
| EXPIRY_DATE | string | 到期日 | |
| EXERCISE_PRICE | float | 行权价格 | |
| EXERCISE_END_DATE | string | 最后行权日 | |
| START_TRADE_DATE | string | 开始交易日 | |
| LISTING_REF_PRICE | float | 挂牌基准价 | |
| LAST_TRADE_DATE | string | 最后交易日 | |
| EXCHANGE_CODE | string | 合约交易所代码 | |
| DELIVERY_DATE | string | 最后交割日 | |
| CONTRACT_UNIT | Int | 合约单位 |  |
| IS_TRADE | string | 是否交易 | |
| EXCHANGE_SHORT_NAME | string | 合约交易所简称 | |
| CONTRACT_ADJUST_FLAG | string | 合约调整标志 | |
| MARKET_CODE | string | 合约代码 | |

### 示例代码

```python
import AmazingData as ad

ad.login(username='username', password='password', host='***.***.***.***', port=****)
info_data_object = ad.InfoData()
base_data_object = ad.BaseData()
calendar = base_data_object.get_calendar()
today = calendar[-1]
code_list = base_data_object.get_option_code_list(security_type='EXTRA_ETF_OP')
option_basic_info = info_data_object.get_option_basic_info(code_list, is_local=False)
```
