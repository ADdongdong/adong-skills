## 交易日历

**接口**: get_calendar

**描述**: 获取交易所的交易日历

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| data_type | str | 否 | 选择返回数据的类型，默认为str ，可选datetime 或 str |
| market | str | 否 | 选择市场market（见附录），默认为SH（上海） |

### 输出参数

返回List[int]，日期列表

### 示例代码

```python
import AmazingData as ad

ad.login(username='username', password='password', host='ip', port=port)
base_data = ad.BaseData()
calendar = base_data.get_calendar()
print(calendar)
```
