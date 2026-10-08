## 期权月合约属性变动

**接口**: get_option_mon_ctr_specs

**描述**: 获取指定期权月合约属性变动（沪深交易所的ETF期权）

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| code_list | list[str] | 是 | 支持沪深ETF期权的的代码列表，可见示例 |
| local_path | str | 是 | 本地存储数据的路径，需绝对路径，格式类似"'D://AmazingData_local_data//'" |
| is_local | bool | 否 | 默认为True，本地数据缓存方案 |

### 输出参数

返回DataFrame，主要字段包含：

| 字段 | 类型 | 说明 |
|------|------|------|
| CODE_OLD | string | 原交易代码 |
| CHANGE_DATE | string | 调整日期 |
| MARKET_CODE | string | 市场代码 |
| NAME_NEW | string | 新合约简称 |
| EXERCISE_PRICE_NEW | float | 新行权价(元) |
| NAME_OLD | string | 原合约简称 |
| CODE_NEW | string | 新交易代码 |
| EXERCISE_PRICE_OLD | float | 原行权价(元) |
| UNIT_OLD | float | 原合约单位(股) |
| UNIT_NEW | float | 新合约单位(股) |
| CHANGE_REASON | string | 调整原因 |

### 示例代码

```python
import AmazingData as ad

ad.login(username='username', password='password', host='***.***.***.***', port=****)
info_data_object = ad.InfoData()
base_data_object = ad.BaseData()
calendar = base_data_object.get_calendar()
today = calendar[-1]
code_list = base_data_object.get_option_code_list(security_type='EXTRA_ETF_OP')
option_mon_ctr_specs = info_data_object.get_option_mon_ctr_specs(code_list, is_local=False)
```
