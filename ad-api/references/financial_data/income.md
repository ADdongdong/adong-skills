## 利润表

**接口**: get_income

**描述**: 获取指定股票列表的上市公司的利润表数据

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| code_list | list[str] | 是 | 支持沪深A的的代码列表，可见示例 |
| local_path | str | 是 | 本地存储数据的路径，需绝对路径，格式类似"'D://AmazingData_local_data//'" |
| is_local | bool | 否 | 默认为True，本地数据缓存方案 |
| begin_date | int | 否 | 报告期，本地数据缓存方案 |
| end_date | int | 否 | 报告期，本地数据缓存方案 |

### 输出参数

返回dict，key为code，value为DataFrame，主要字段包含：

| 字段名称 | 类型 | 字段说明 | 备注 |
|------|------|------|------|
| MARKET_CODE | str | 证券代码 | |
| SECURITY_NAME | str | 证券简称 | |
| STATEMENT_TYPE | str | 报表类型 | [参看报表类型代码表](../appendix.md#报表类型代码表-statement_type) |
| REPORT_TYPE | str | 报告期名称 | [参看报告期名称](../appendix.md#报告期名称-report_type) |
| REPORTING_PERIOD | str | 报告期 | |
| ANN_DATE | str | 公告日期 | |
| ACTUAL_ANN_DATE | str | 实际公告日期 | |
| COMP_TYPE_CODE | str | 公司类型代码 | |
| CURRENCY_CODE | str | 货币代码 | |
| COMMENTS | str | 备注 | |
| IS_CALCULATION | float | 是否计算报表 | |
| AMORT_COST_FIN_ASSETS_EAR | float | 以摊余成本计量的金融资产终止确认收益 | |
| BASIC_EPS | float | 基本每股收益 | |
| BEG_UNDISTRIBUTED_PRO | float | 年初未分配利润 | |
| CAPITALIZED_COM_STOCK_DIV | float | 转作股本的普通股股利 | |
| COMMON_STOCK_DIV_PAYABLE | float | 应付普通股股利 | |
| CONTINUED_NET_OPERA_PRO | float | 持续经营净利润 | |
| CREDIT_IMPAIR_LOSS | float | 信用减值损失 | |
| DILUTED_EPS | float | 稀释每股收益 | |
| DISTRIBUTIVE_PRO | float | 可分配利润 | |
| DISTRIBUTIVE_PRO_SHAREHOLDER | float | 可供股东分配的利润 | |
| DIV_EXP_INSUR | float | 保户红利支出 | |
| EBIT | float | 息税前利润 | |
| EBITDA | float | 息税折旧摊销前利润 | |
| EMPLOYEE_WELFARE | float | 职工奖金福利 | |
| END_NET_OPERA_PRO | float | 终止经营净利润 | |
| EXT_INSUR_CONT_RSRV | float | 提取保险责任准备金 | |
| EXT_UNEARNED_PREM_RES | float | 提取未到期责任准备金 | |
| FIN_EXP_INT_EXP | float | 财务费用:利息费用 | |
| FIN_EXP_INT_INC | float | 财务费用:利息收入 | |
| GAIN_DISPOSAL_ASSETS | float | 资产处置收益 | |
| HANDLING_CHRG_COMM_FEE | float | 手续费及佣金收入 | |
| INCL_INC_INV_JV_ENTP | float | 其中:对联营企业和合营企业的投资收益 | |
| INCL_LESS_LOSS_DISP_NCUR_ASSET | float | 其中:减:非流动资产处置净损失 | |
| INCL_REINSUR_PREM_INC | float | 其中:分保费收入 | |
| INCOME_TAX | float | 所得税 | |
| INSUR_EXP | float | 保险业务支出 | |
| INSUR_PREM | float | 已赚保费 | |
| INTEREST_INC | float | 利息收入 | |
| LESS_ADMIN_EXP | float | 减:管理费用 | |
| LESS_AMORT_COMPEN_EXP | float | 减:摊回赔付支出 | |
| LESS_AMORT_INSUR_CONT_RSRV | float | 减:摊回保险责任准备金 | |
| LESS_AMORT_REINSUR_EXP | float | 减:摊回分保费用 | |
| LESS_ASSETS_IMPAIR_LOSS | float | 减:资产减值损失 | |
| LESS_BUS_TAX_SURCHARGE | float | 减:营业税金及附加 | |
| LESS_FIN_EXP | float | 减:财务费用 | |
| LESS_HANDLING_CHRG_COMM_FEE | float | 减:手续费及佣金支出 | |
| LESS_INTEREST_EXP | float | 减:利息支出 | |
| LESS_NON_OPERA_EXP | float | 减:营业外支出 | |
| LESS_OPERA_COST | float | 减:营业成本 | |
| LESS_REINSUR_PREM | float | 减:分出保费 | |
| LESS_SELLING_EXP | float | 减:销售费用 | |
| MIN_INT_INC | float | 少数股东损益 | |
| NET_EXPOSURE_HEDGING_GAIN | float | 净敞口套期收益 | |
| NET_HANDLING_CHRG_COMM_FEE | float | 手续费及佣金净收入 | |
| NET_INC_EC_ASSET_MGMT_BUS | float | 受托客户资产管理业务净收入 | |
| NET_INC_SEC_BROK_BUS | float | 代理买卖证券业务净收入 | |
| NET_INC_SEC_UW_BUS | float | 证券承销业务净收入 | |
| NET_INTEREST_INC | float | 利息净收入 | |
| NET_PRO_AFTER_DED_NR_GL | float | 扣除非经常性损益后净利润（扣除少数股东损益） |  |
| NET_PRO_AFTER_DED_NR_GL_COR | float | 扣除非经常性损益后的净利润(财务重要指标(更正前)) |  |
| NET_PRO_EXCL_MIN_INT_INC | float | 净利润(不含少数股东损益) | |
| NET_PRO_INCL_MIN_INT_INC | float | 净利润(含少数股东损益) | |
| NET_PRO_UNDER_INT_ACC_STA | float | 国际会计准则净利润 | |
| OPERA_EXP | float | 营业支出 | |
| OPERA_PROFIT | float | 营业利润 | |
| OPERA_REV | float | 营业收入 | |
| OTH_ASSETS_IMPAIR_LOSS | float | 其他资产减值损失 | |
| OTH_BUS_COST | float | 其他业务成本 | |
| OTH_BUS_INC | float | 其他业务收入 | |
| OTH_COMPRE_INC | float | 其他综合收益 | |
| OTH_INCOME | float | 其他收益 | |
| OTH_NET_OPERA_INC | float | 其他经营净收益 | |
| PLUS_NET_FX_INC | float | 加:汇兑净收益 | |
| PLUS_NET_GAIN_CHG_FV | float | 加:公允价值变动净收益 | |
| PLUS_NET_INV_INC | float | 加:投资净收益 | |
| PLUS_NON_OPERA_REV | float | 加:营业外收入 | |
| PLUS_OTH_NET_BUS_INC | float | 加:其他业务净收益 | |
| PREFERRED_SHARE_DIV_PAYABLE | float | 应付优先股股利 | |
| PREM_BUS_INC | float | 保费业务收入 | |
| RD_EXP | float | 研发费用 | |
| REINSURANCE_EXP | float | 分保费用 | |
| SPE_BAL_NET_PRO_MARG | float | 净利润差额(特殊报表科目) | |
| SPE_BAL_OPERA_PRO_MARG | float | 营业利润差额(特殊报表科目) | |
| SPE_BAL_TOT_OPERA_COST_DIF | float | 营业总成本差额(特殊报表科目) | |
| SPE_BAL_TOT_OPERA_INC_DIF | float | 营业总收入差额(特殊报表科目) | |
| SPE_BAL_TOT_PRO_MARG | float | 利润总额差额(特殊报表科目) | |
| SPE_TOT_OPERA_COST_DIF_STATE | str | 营业总成本差额说明(特殊报表科目) |  |
| SPE_TOT_OPERA_INC_DIF_STATE | str | 营业总收入差额说明(特殊报表科目) |  |
| SURR_VALUE | float | 退保金 |  |
| TOTAL_PROFIT | float | 利润总额 |  |
| TOT_BAL_NET_PRO_MARG | float | 净利润差额(合计平衡项目) |  |
| TOT_BAL_OPERA_PRO_MARG | float | 营业利润差额(合计平衡项目) |  |
| TOT_BAL_TOT_PRO_MARG | float | 利润总额差额(合计平衡项目) |  |
| TOT_COMPEN_EXP | float | 赔付总支出 |  |
| TOT_COMPRE_INC | float | 综合收益总额 |  |
| TOT_COMPRE_INC_MIN_SHARE | float | 综合收益总额(少数股东) |  |
| TOT_COMPRE_INC_PARENT_COMP | float | 综合收益总额(母公司) |  |
| TOT_OPERA_COST | float | 营业总成本 |  |
| TOT_OPERA_COST2 | float | 营业总成本2 |  |
| TOT_OPERA_REV | float | 营业总收入 |  |
| TRANSFER_HOUSING_REVO_FUNDS | float | 住房周转金转入 |  |
| TRANSFER_OTHERS | float | 其他转入 |  |
| TRANSFER_SURPLUS_RESERVE | float | 盈余公积转入 |  |
| UNCONFIRMED_INV_LOSS | float | 未确认投资损失 |  |
| WITHDRAW_ANY_SURPLUS_RESV | float | 提取任意盈余公积金 |  |
| WITHDRAW_ENT_DEVELOP_FUND | float | 提取企业发展基金 |  |
| WITHDRAW_LEG_PUB_WEL_FUND | float | 提取法定公益金 |  |
| WITHDRAW_LEG_SURPLUS | float | 提取法定盈余公积 |  |
| WITHDRAW_RESV_FUND | float | 提取储备基金 |  |

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
income = info_data_object.get_income(all_code_list, local_path='D://AmazingData_local_data//')
```
