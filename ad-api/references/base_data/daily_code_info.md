## 每日最新证券信息

**接口**: get_code_info

**描述**: 获取每日最新证券信息，交易日早上9点前更新当日最新

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| security_type | str | 否 | 代码类型security_type（见附录），默认为EXTRA_STOCK_A（上交所A股、深交所A股和北交所的股票列表） |

### 输出参数

返回DataFrame，包含：
- symbol: 证券简称
- security_status: 产品状态标志
- pre_close: 昨收价
- high_limited: 涨停价
- low_limited: 跌停价
- price_tick: 最小价格变动单位

### 示例代码

```python
import AmazingData as ad

ad.login(username='username', password='password', host='ip', port=port)
base_data = ad.BaseData()
code_info = base_data.get_code_info(security_type='EXTRA_ETF')
print(code_info)
```
