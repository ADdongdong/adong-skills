## 业绩预告

**接口**: get_profit_notice

**描述**: 获取指定股票列表的上市公司的业绩预告数据

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| code_list | list[str] | 是 | 支持沪深A的的代码列表，可见示例 |
| local_path | str | 是 | 本地存储数据的路径，需绝对路径，格式类似"'D://AmazingData_local_data//'" |
| is_local | bool | 否 | 默认为True，本地数据缓存方案 |
| begin_date | int | 否 | 报告期，本地数据缓存方案 |
| end_date | int | 否 | 报告期，本地数据缓存方案 |

### 输出参数

返回DataFrame，主要字段包含：

| 字段名称 | 类型 | 字段说明 |
|------|------|------|
| MARKET_CODE | str | 证券代码 |
| SECURITY_NAME | str | 证券简称 |
| P_TYPECODE | str | 业绩预告类型代码 |
| REPORTING_PERIOD | str | 报告期 |
| ANN_DATE | str | 公告日期 |
| P_CHANGE_MAX | float64 | 预告净利润变动幅度上限(%) |
| P_CHANGE_MIN | float64 | 预告净利润变动幅度下限(%) |
| NET_PROFIT_MAX | float64 | 预告净利润上限(万元) |
| NET_PROFIT_MIN | float64 | 预告净利润下限(万元) |
| FIRST_ANN_DATE | str | 首次公告日 |
| P_NUMBER | float64 | 公布次数 |
| P_REASON | str | 业绩变动原因 |
| P_SUMMARY | str | 业绩预告摘要 |
| P_NET_PARENT_FIRM | float64 | 上年同期归母净利润 |
| REPORT_TYPE | str | 报告期名称 |

### 示例代码

```python
import AmazingData as ad

ad.login(username='username', password='password', host='***.***.***.***', port=****)
info_data_object = ad.InfoData()
base_data_object = ad.BaseData()
calendar = base_data_object.get_calendar()
today = calendar[-1]
all_code_list = base_data_object.get_hist_code_list(
    security_type='EXTRA_STOCK_A_SH_SZ',
    start_date=20130101,
    end_date=today,
    local_path='D://AmazingData_local_data//'
)
profit_notice = info_data_object.get_profit_notice(all_code_list, local_path='D://AmazingData_local_data//')
```
