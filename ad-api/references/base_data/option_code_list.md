## 交易日早上9点前更新

**接口**: get_option_code_list

**描述**: 获取期权代码表（每日最新）

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| security_type | str | 是 | 代码类型security_type期权)（见附录），默认为EXTRA_ETF_OP（ETF期权, 包含上交所和深交所） |

### 输出参数

返回list，期权代码列表

### 示例代码

```python
import AmazingData as ad

ad.login(username='username', password='password', host='ip', port=port)
base_data = ad.BaseData()
option_codes = base_data.get_option_code_list(security_type='EXTRA_ETF_OP')
```
