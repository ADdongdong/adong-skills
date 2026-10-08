## 公告原文下载（基金）

**接口**: InfoData.get_announcement_fund

**描述**: 下载公告原文pdf，并返回pdf原文的本地路径

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| announcement_fund_list_df | dataframe | 是 | 公告明细数据，get_announcement_fund_list的返回值 |
| tag_id_list | list | 否 | 按照[关联规则id](../appendix.md#announcement-tag-id)对公告进行筛选，默认为空列表，表示不筛选 |
| begin_date | int | 否 | 对公告的发布时间做筛选，公告发布日期的起始日期，默认为19900101 |
| end_date | int | 否 | 对公告的发布时间做筛选，公告发布日期的结束日期，默认为20980101 |
| local_path | str | 是 | 本地存储数据的路径，需绝对路径，格式类似"D://AmazingData_local_data//" |

### 输出参数

| 参数 | 类型 | 说明 |
|------|------|------|
| announcement_fund_pdf_path | dict | key为公告的资源ID（SOURCE_ID），value为公告pdf的本地路径 |
| announcement_fund_list_tag_df | dataframe | 按照公告发布日期和关联规则，筛选后的announcement_fund_list_df |

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
announcement_fund_pdf_path, announcement_fund_list_tag_df = (
    info_data_object.get_announcement_fund(
        announcement_fund_list_df, begin_date=20260101, end_date=20260401))
```
