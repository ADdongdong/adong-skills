## ETF基金份额

**接口**: get_fund_share

**描述**: 获取指定ETF列表的基金份额数据

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
| fund_share | dict | key：code<br>value:dataframe<br>column为fund_share的字段<br>index为日期 |

### 示例代码

```python
# 第一步 登录api
import AmazingData as ad
ad.login(username='username', password='password',host='***.***.***.***',port=****)
info_data_object = ad.InfoData()
base_data_object = ad.BaseData()
etf_code_list = base_data_object.get_code_list(security_type='EXTRA_ETF')
# ETF份额
fund_share = info_data_object.get_fund_share(etf_code_list, is_local=False)
```

### fund_share 的字段说明：

| 字段名称 | 类型 | 字段说明 | 备注 |
| --- | --- | --- | --- |
| FUND_SHARE | float | 基金份额(万份) | |
| CHANGE_REASON | string | 份额变动原因 | |
| IS_CONSOLIDATED_DATA | int | 是否合并数据 | 0：非合并数据<br>1：合并数据<br>2：合并数据，但该基金代码属于不实际交易基金 |
| MARKET_CODE | string | 市场代码 | |
| ANN_DATE | string | 公告日期 | |
| TOTAL_SHARE | float | 基金总份额(万份) | |
| CHANGE_DATE | string | 变动日期 | |
| FLOAT_SHARE | float | 流通份额(万份) | |
