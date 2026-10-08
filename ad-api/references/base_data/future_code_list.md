## 交易日早上9点前更新

**接口**: get_future_code_list

**描述**: 获取期货代码表（每日最新）

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| security_type | str | 是 | 代码类型security_type(期货交易所)（见附录），默认为ZJ_FUTURE（期货, 中金所） |

### 输出参数

返回list，期货代码列表

### 示例代码

```python
import AmazingData as ad

ad.login(username='username', password='password', host='ip', port=port)
base_data = ad.BaseData()
future_codes = base_data.get_future_code_list(security_type='EXTRA_FUTURE')
```
