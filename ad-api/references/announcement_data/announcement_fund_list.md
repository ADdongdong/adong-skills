## 公告明细数据（基金）

**接口**: InfoData.get_announcement_fund_list

**描述**: 获取指定基金列表的基金公告明细数据

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| code_list | list[str] | 是 | 支持沪深ETF的代码列表，可见示例 |
| local_path | str | 是 | 本地存储数据的路径，需绝对路径，格式类似"D://AmazingData_local_data//" |
| is_local | bool | 否 | 默认为True，本地数据缓存方案 |
| begin_date | int | 否 | 交易日，本地数据缓存方案 |
| end_date | int | 否 | 交易日，本地数据缓存方案 |

### 输出参数

返回DataFrame，主要字段包含：

| 字段 | 类型 | 说明 | 备注 |
|------|------|------|------|
| MARKET_CODE | string | 市场代码 | |
| SOURCE_ID | string | 资源ID | |
| TITLE | string | 标题 | |
| TAG_ID | string | 关联规则id | 详细说明见附录[关联规则id](../appendix.md#announcement-tag-id) |
| TAG_NAME | string | 分类名称 | |
| ONLINE_STATUS | int | 上线状态 | 0上线；1未上线 |
| PUBLISH_TIME | str | 发布时间 | |
| DATA_STATUS | int | 数据状态 | 0有效；1无效 |
| COMPANY | string | 基金名称 | |

### 示例代码

```python
import AmazingData as ad

ad.login(username='username', password='password', host='***.***.***.***', port=****)
info_data_object = ad.InfoData()
base_data_object = ad.BaseData()
calendar = base_data_object.get_calendar()
today = calendar[-1]
all_code_list = base_data_object.get_hist_code_list(
    security_type='EXTRA_ETF',
    start_date=20130101,
    end_date=today
)
announcement_fund_list_df = info_data_object.get_announcement_fund_list(
    all_code_list[:10], is_local=False)
```
