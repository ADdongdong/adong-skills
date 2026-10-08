## ETF每日最新申赎数据

**接口**: get_etf_pcf

**描述**: 获取指定ETF的申赎和成分股数据（沪深交易所的ETF）

### 输入参数

| 参数 | 数据类型 | 必选 | 解释 |
| --- | --- | --- | --- |
| code_list | list[str] | 是 | 支持沪深ETF的的代码列表，可见示例 |

### 输出参数

| 参数 | 数据类型 | 解释 |
| --- | --- | --- |
| etf_pcf_info | dataframe | column为etf_pcf_info的字段<br>index为ETF代码 |
| etf_pcf_constituent | dict | 字典的key：ETF代码<br>字典的value：dataframe，<br>column为etf_pcf_constituent的字段，<br>index为序号 |

### 示例代码

```python
# 第一步 登录api
import AmazingData as ad
ad.login(username='username', password='password',host='***.***.***.***',port=****)
base_data_object = ad.BaseData()
code_list = base_data_object.get_hist_code_list(security_type='EXTRA_ETF')
etf_pcf_info, etf_pcf_constituent = base_data_object.get_etf_pcf(code_list)
```

### etf_pcf_info的字段说明：

| 参数 | 数据类型 | 字段说明 | 备注 |
| --- | --- | --- | --- |
| creation_redemption_unit | int | 每个篮子对应的ETF份数 |  |
| max_cash_ratio | string | 最大现金替代比例 |  |
| publish | string | 是否发布IOPV | Y=是,N=否 |
| creation | string | 是否允许申购 | Y=是,N=否(仅深圳有效) |
| redemption | string | 是否允许赎回 | Y=是,N=否(仅深圳有效) |
| creation_redemption_switch | string | 申购赎回切换 | (仅上海有效,0-不允许申购/赎回,1-申购和赎回皆允许,2-仅允许申购,3-仅允许赎回) |
| record_num | int | 深市成份证券数目 |  |
| total_record_num | int | 所有成份证券数量 |  |
| estimate_cash_component | int | 预估现金差额 |  |
| trading_day | int | 当前交易日 | (格式:YYYYMMDD) |
| pre_trading_day | int | 前一交易日 | (格式:YYYYMMDD) |
| cash_component | int | 前一日现金差额 |  |
| nav_per_cu | int | 前一日最小申赎单位净值 |  |
| nav | int | 前一日基金份额净值 |  |
| symbol | string | 基金名称 | 仅深圳有效 |
| fund_management_company | string | 基金公司名称 | 仅深圳有效 |
| underlying_security_id | string | 拟合指数代码 | 仅深圳有效 |
| underlying_security_id_source | string | 拟合指数市场 | 参考Market，仅深圳有效 |
| dividend_per_cu | int | 红利金额 |  |
| creation_limit | int | 累计申购总额限制 | 为0表示没有限制(仅深圳有效) |
| redemption_limit | int | 累计赎回总额限制 | 0表示没有限制(仅深圳有效) |
| creation_limit_per_user | int | 单个账户累计申购总额限制 | 0表示没有限制(仅深圳有效) |
| redemption_limit_per_user | int | 单个账户累计赎回总额限制 | 0表示没有限制(仅深圳有效) |
| net_creation_limit | int | 净申购总额限制 | 0表示没有限制(仅深圳有效) |
| net_redemption_limit | int | 净赎回总额限制 | 0表示没有限制(仅深圳有效) |
| net_creation_limit_per_user | int | 单个账户净申购总额限制 | 0表示没有限制(仅深圳有效) |
| net_redemption_limit_per_user | int | 单个账户净赎回总额限制 | 0表示没有限制(仅深圳有效) |

### etf_pcf_constituent的字段说明：

| 参数 | 数据类型 | 字段说明 | 备注 |
| --- | --- | --- | --- |
| underlying_symbol | string | 成份证券简称 |  |
| component_share | int | 成份证券数量 |  |
| substitute_flag | string | 现金替代标志 | //**深圳现金替代标志*        //0=禁止现金替代(必须有证券),1=可以进行现金替代(先用证券,证券不足时差额部分用现金替代),2=必须用现金替代<br>//**上海现金替代标志*<br><br>//ETF 公告文件 1.0 版格式<br><br>//0 –沪市不可被替代, 1 – 沪市可以被替代, 2 – 沪市必须被替代, 3 – 深市退补现金替代, 4 – 深市必须现金替代<br>//5 – 非沪深市场成份证券退补现金替代(不适用于跨沪深港 ETF 产品), 6 – 非沪深市场成份证券必须现金替代(不适用于跨沪深港 ETF 产品)<br><br>//ETF 公告文件 2.1 版格式<br><br>//0 –沪市不可被替代, 1 – 沪市可以被替代, 2 – 沪市必须被替代, 3 – 深市退补现金替代, 4 – 深市必须现金替代<br>//5 – 非沪深市场成份证券退补现金替代(不适用于跨沪深港 ETF 产品), 6 – 非沪深市场成份证券必须现金替代(不适用于跨沪深港 ETF 产品)<br>//7 – 港市退补现金替代(仅适用于跨沪深港ETF 产品),<br>//8 – 港市必须现金替代(仅适用于跨沪深港 ETF 产品) |
| premium_ratio | int | 溢价比例 |  |
| discount_ratio | int | 折价比例 |  |
| creation_cash_substitute | int | 申购替代金额 | 仅深圳有效 |
| redemption_cash_substitute | int | 赎回替代金额 | 仅深圳有效 |
| substitution_cash_amount | int | 替代总金额 | 仅上海有效 |
| underlying_security_id | string | 成份证券所属市场ID | 仅对跨市场债券(银行间)ETF启用 |
