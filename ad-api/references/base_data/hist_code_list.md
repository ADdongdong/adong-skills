## 历史代码表

**接口**: get_hist_code_list

**描述**: 获取历史代码表

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| security_type | str | 是 | 默认为"EXTRA_STOCK_A_SH_SZ" 沪深A股，支持附录security_type(沪深北)和security_type(期货交易所)， |
| start_date | int | 是 | 开始时间，闭区间 |
| end_date | int | 是 | 结束时间，闭区间 |
| local_path | str | 是 | 本地存储数据的路径，需绝对路径，格式类似"'D://AmazingData_local_data//'" |

### 输出参数

返回List[str]，证券代码列表

### 示例代码

```python
import AmazingData as ad

ad.login(username='username', password='password', host='ip', port=port)
base_data = ad.BaseData()
hist_codes = base_data.get_hist_code_list(
    security_type='EXTRA_STOCK_A_SH_SZ',
    start_date=20240101,
    end_date=20240701,
    local_path='D://data//'
)
```
