## 股本结构

**接口**: get_equity_structure

**描述**: 获取指定股票列表的上市公司的股本结构数据

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| code_list | list[str] | 是 | 支持沪深A的的代码列表，可见示例 |
| local_path | str | 是 | 本地存储数据的路径，需绝对路径，格式类似"'D://AmazingData_local_data//'" |
| is_local | bool | 否 | 默认为True，本地数据缓存方案 |
| begin_date | int | 否 | 变动日期，本地数据缓存方案 |
| end_date | int | 否 | 变动日期，本地数据缓存方案 |

### 输出参数

返回DataFrame，主要字段包含：

| 字段名称 | 类型 | 字段说明 | 备注 |
|------|------|------|------|
| MARKET_CODE | string | 证券代码 |
| ANN_DATE | string | 公告日期 |
| CHANGE_DATE | string | 变动日期 |
| SHARE_CHANGE_REASON_STR | string | 股本变动原因描述 |
| EX_CHANGE_DATE | string | 除权日期 |
| CURRENT_SIGN | int | 最新标志 |
| IS_VALID | int | 是否有效 |
| TOT_SHARE | float | 总股本(万股) |
| FLOAT_SHARE | float | 流通股(万股) |
| FLOAT_A_SHARE | float | 流通A股(万股) |
| FLOAT_B_SHARE | float | 流通B股(万股) |
| FLOAT_HK_SHARE | float | 香港流通股(万股) |
| FLOAT_OS_SHARE | float | 海外流通股(万股) |
| TOT_TRADABLE_SHARE | float | 流通股合计 |
| RTD_A_SHARE_INST | float | 限售A股(其他内资持股:机构配售股) |
| RTD_A_SHARE_DOMESNP | float | 限售A股(其他内资持股:境内自然人持股) |
| RTD_SHARE_SENIOR | float | 限售股份(高管持股)(万股) |
| RTD_A_SHARE_FOREIGN | float | 限售A股(外资持股) |
| RTD_A_SHARE_FORJUR | float | 限售A股(境外法人持股) |
| RTD_A_SHARE_FORNP | float | 限售A股(境外自然人持股) |
| RESTRICTED_B_SHARE | float | 限售B股(万股) |
| OTHER_RTD_SHARE | float | 其他限售股 |
| NON_TRADABLE_SHARE | float | 非流通股 |
| NTRD_SHARE_STATE_PCT | float | 非流通股(国有股) |
| NTRD_SHARE_STATE | float | 非流通股(国家股) |
| NTRD_SHARE_STATEJUR | float | 非流通股(国有法人股) |
| NTRD_SHARE_DOMESJUR | float | 非流通股(境内法人股) |
| NTRD_SHARE_DOMES_INITIATOR | float | 非流通股(境内法人股:境内发起人股) |
| NTRD_SHARE_IPOJURIS | float | 非流通股(境内法人股:募集法人股) |
| NTRD_SHARE_GENJURIS | float | 非流通股(境内法人股:一般法人股) |
| NTRD_SHARE_STRA_INVESTOR | float | 非流通股(境内法人股:战略投资者持股) |
| NTRD_SHARE_FUND | float | 非流通股(境内法人股:基金持股) |
| NTRD_SHARE_NAT | float | 非流通股(自然人股) |
| TRAN_SHARE | float | 转配股(万股) |
| FLOAT_SHARE_SENIOR | float | 流通股(高管持股) |
| SHARE_INEMP | float | 内部职工股(万股) |
| PREFERRED_SHARE | float | 优先股(万股) |
| NTRD_SHARE_NLIST_FRGN | float | 非流通股(非上市外资股) |
| STAQ_SHARE | float | STAQ股(万股) |
| NET_SHARE | float | NET股(万股) |
| SHARE_CHANGE_REASON | string | 股本变动原因 |
| TOT_A_SHARE | float | A股合计 |
| TOT_B_SHARE | float | B股合计 |
| OTCA_SHARE | float | 三板A股 |
| OTCB_SHARE | float | 三板B股 |
| TOT_OTC_SHARE | float | 三板合计 |
| SHARE_HK | float | 香港上市股 |
| PRE_NON_TRADABLE_SHARE | float | 股改前非流通股 |
| RESTRICTED_A_SHARE | float | 限售A股(万股) |
| RTD_A_SHARE_STATE | float | 限售A股(国家持股) |
| RTD_A_SHARE_STATEJUR | float | 限售A股(国有法人持股) |
| RTD_A_SHARE_OTHER_DOMES | float | 限售A股(其他内资持股) |
| RTD_A_SHARE_OTHER_DOMESJUR | float | 限售A股(其他内资持股:境内法人持股) |
| TOT_RESTRICTED_SHARE | float | 限售股合计 |

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
equity_structure = info_data_object.get_equity_structure(all_code_list, local_path='D://AmazingData_local_data//')
```
