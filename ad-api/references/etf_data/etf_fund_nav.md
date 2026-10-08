## ETF基金净值

**接口**: get_fund_nav

**描述**: 获取指定ETF列表的基金净值数据

### 输入参数

| 参数 | 数据类型 | 必选 | 解释 |
| --- | --- | --- | --- |
| code_list | list[str] | 是 | 支持沪深ETF的的代码列表，可见示例 |
| local_path | str | 是 | 本地存储数据的路径，需绝对路径，格式类似“<br>'D://AmazingData_local_data//'<br>” |
| is_local | bool | 否 | 默认为True，本地数据缓存方案 |
| begin_date | int | 否 | 变动日期，本地数据缓存方案 |
| end_date | int | 否 | 变动日期，本地数据缓存方案 |

### 输出参数

| 参数 | 数据类型 | 解释 |
| --- | --- | --- |
| fund_nav | dict | key：code<br>value:dataframe<br>column为fund_nav的字段<br>index为日期 |

### 示例代码

```python
# 第一步 登录api
import AmazingData as ad
ad.login(username='username', password='password',host='***.***.***.***',port=****)
info_data_object = ad.InfoData()
base_data_object = ad.BaseData()
etf_code_list = base_data_object.get_code_list(security_type='EXTRA_ETF')
# ETF份额
fund_nav = info_data_object.get_fund_nav(etf_code_list, is_local=False)
```

### fund_nav 的字段说明：

| 字段名称 | 类型 | 字段说明 |
| --- | --- | --- |
| MARKET_CODE | string | 市场代码 |
| ANN_DATE | string | 公告日期 |
| PRICE_DATE | string | 截止日期：估算基金净值的交易日 |
| UNIT_NAV | float | 单位净值 |
| ACCUM_NAV | float | 累计净值 |
| ACCUM_DIV | float | 累计分红 |
| NAV_ADJ_FACTOR | float | 复权因子 |
| IS_EX_DIVIDEND_DATE | int | 是否净值除权日 |
| ACCUM_UNIT_DIST | float | 累计单位分配 |
| TOTAL_NET_ASSET_VALUE | float | 合计资产净值 |
| ADJ_UNIT_NAV | float | 复权单位净值 |
| IS_MERGED_DATA | int | 是否合计数据 |
| NET_ASSET_VALUE | float | 资产净值 |
| INNER_CODE | string | 基金场内代码 |
| OUTER_CODE | string | 基金场外代码 |
| ACCUM_UNIT_NAV | float | 累计单位净值 |
