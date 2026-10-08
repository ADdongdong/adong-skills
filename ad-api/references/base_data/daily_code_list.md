## 交易日早上9点前更新

**接口**: get_code_list

**描述**: 获取代码表（每日最新），此接口无法获取历史代码表

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| security_type | str | 否 | 代码类型security_type（见附录），默认为EXTRA_STOCK_A（上交所A股、深交所A股和北交所的股票列表） |

### 输出参数

返回list，证券代码列表

### 示例代码

```python
import AmazingData as ad

ad.login(username='username', password='password', host='ip', port=port)
base_data = ad.BaseData()
code_list = base_data.get_code_list(security_type='EXTRA_STOCK_A')
print(code_list)
```
