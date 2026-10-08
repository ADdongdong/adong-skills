## 配股数据

**接口**: get_right_issue

**描述**: 获取指定股票列表的上市公司的配股数据

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| code_list | list[str] | 是 | 支持沪深A的的代码列表，可见示例 |
| local_path | str | 是 | 本地存储数据的路径，需绝对路径，格式类似"'D://AmazingData_local_data//'" |
| is_local | bool | 否 | 默认为True，本地数据缓存方案 |
| begin_date | int | 否 | 公告日期，本地数据缓存方案 |
| end_date | int | 否 | 公告日期，本地数据缓存方案 |

### 输出参数

返回DataFrame，主要字段包含：

| 字段名称 | 类型 | 字段说明 | 备注 |
|------|------|------|------|
| MARKET_CODE | string | 证券代码 |
| PROGRESS | int | 方案进度 |
| PRICE | double | 配股价格(元) |
| RATIO | double | 配股比例 |
| AMT_PLAN | double | 配股计划数量(万股) |
| AMT_REAL | double | 配股实际数量(万股) |
| COLLECTION_FUND | double | 募集资金(元) |
| SHAREB_REG_DATE | string | 股权登记日 |
| EX_DIVIDEND_DATE | string | 除权日 |
| LISTED_DATE | string | 配股上市日 |
| PAY_START_DATE | string | 缴款起始日 |
| PAY_END_DATE | string | 缴款终止日 |
| PREPLAN_DATE | string | 预案公告日 |
| SMTG_ANN_DATE | string | 股东大会公告日 |
| PASS_DATE | string | 发审委通过公告日 |
| APPROVED_DATE | string | 证监会核准公告日 |
| EXECUTE_DATE | string | 配股实施公告日 |
| RESULT_DATE | string | 配股结果公告日 |
| LIST_ANN_DATE | string | 上市公告日 |
| GUARANTOR | string | 基准年度 |
| GUARTYPE | double | 基准股本(万股) |
| RIGHTSISSUE_CODE | string | 配售代码 |
| ANN_DATE | string | 公告日期 |
| RIGHTSISSUE_YEAR | string | 配股年度 |
| RIGHTSISSUE_DESC | string | 配股说明 |
| RIGHTSISSUE_NAME | string | 配股简称 |
| RATIO_DENOMINATOR | double | 配股比例分母 |
| RATIO_MOLECULAR | double | 配股比例分子 |
| SUBS_METHOD | string | 认购方式 |
| EXPECTED_FUND_RAISING | double | 预计募集资金(元) |

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
right_issue = info_data_object.get_right_issue(all_code_list, local_path='D://AmazingData_local_data//')
```
