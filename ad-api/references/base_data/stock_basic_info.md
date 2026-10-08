## 证券基础信息

**接口**: get_stock_basic

**描述**: 获取指定股票列表的上市公司的证券基础数据，包含沪深北三个交易所，所有股票（包含已退市标的）的中英文名称、上市日期、退市日期、上市板块等信息

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| code_list | list[str] | 是 | 支持沪深北三个交易所的代码列表 |

### 输出参数

返回DataFrame，字段说明：

| 参数 | 数据类型 | 字段说明 |
|------|------|------|
| MARKET_CODE | string | 证券代码 |
| SECURITY_NAME | string | 证券简称 |
| COMP_NAME | string | 证券中文名称 |
| PINYIN | string | 中文拼音简称 |
| COMP_NAME_ENG | string | 证券英文名称 |
| LISTDATE | int | 上市日期 |
| DELISTDATE | int | 退市日期 |
| LISTPLATE_NAME | string | 上市板块名称 |
| COMP_SNAME_ENG | string | 英文名称缩写 |
| IS_LISTED | int | 上市状态，1：上市交易，3：终止上市 |

### 示例代码

```python
import AmazingData as ad

ad.login(username='username', password='password', host='***.***.***.***', port=****)
base_data_object = ad.BaseData()
code_list = base_data_object.get_code_list(security_type='EXTRA_STOCK_A_SH_SZ')
info_data_object = ad.InfoData()
stock_basic = info_data_object.get_stock_basic(code_list)
```
