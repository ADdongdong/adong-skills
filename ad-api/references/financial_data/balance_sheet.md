## 资产负债表

**接口**: get_balance_sheet

**描述**: 获取指定股票列表的上市公司的资产负债表数据

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
| COMP_TYPE_CODE | int | 公司类型代码 | |
| CURRENCY_CODE | float | 货币代码 | |
| ACC_PAYABLE | float | 应付票据及应付账款 | |
| ACC_RECEIVABLE | float | 应收票据及应收账款 | |
| ACC_RECEIVABLES | float | 应收款项 | |
| ACCRUED_EXP | float | 预提费用 | |
| ACCT_PAYABLE | float | 应付账款 | |
| ACCT_RECEIVABLE | float | 应收账款 | |
| ACT_TRADING_SEC | float | 代理买卖证券款 | |
| ACT_UW_SEC | float | 代理承销证券款 | |
| ADV_PREM | float | 预收保费 | |
| ADV_RECEIPT | float | 预收款项 | |
| AGENCY_ASSETS | float | 代理业务资产 | |
| AGENCY_BUSINESS_LIAB | float | 代理业务负债 | |
| ANTICIPATION_LIAB | float | 预计负债 | |
| BONDS_PAYABLE | float | 应付债券 | |
| CAP_RESV | float | 资本公积金 | |
| CAP_STOCK | float | 股本 | |
| CLAIMS_PAYABLE | float | 应付赔付款 | |
| CLIENTS_RESERVES | float | 客户备付金 | |
| CONST_IN_PROC | float | 在建工程 | |
| CONT_ASSETS | float | 合同资产 | |
| CONT_LIABILITIES | float | 合同负债 | |
| CURRENCY_CAP | float | 货币资金 | |
| DEBT_INV | float | 债权投资(元) |  |
| DEFERRED_INCOME | float | 递延收益 | |
| DEFERRED_TAX_ASSETS | float | 递延所得税资产 | |
| DEFERRED_TAX_LIAB | float | 递延所得税负债 | |
| DEPOSIT_CAP_RECOG | float | 存出资本保证金 | |
| DEPOSIT_TAKING | float | 吸收存款 | |
| DEPOSITS_RECEIVED | float | 存入保证金 | |
| DER_FIN_ASSETS | float | 衍生金融资产 | |
| DERI_FIN_LIAB | float | 衍生金融负债 | |
| DEVELOP_EXP | float | 开发支出 | |
| DIV_PAYABLE | float | 应付股利 | |
| DIV_RECEIVABLE | float | 应收股利 | |
| EMPL_PAY_PAYABLE | float | 应付职工薪酬 | |
| ENGIN_MAT | float | 工程物资 | |
| FIXED_ASSETS | float | 固定资产 | |
| FIXED_ASSETS_TOTAL | float | 固定资产(合计)(元) |  |
| GOODWILL | float | 商誉 | |
| GUA_DEPOSITS_PAID | float | 存出保证金 | |
| GUA_PLEDGE_LOANS | float | 保户质押贷款 | |
| HOLD_TO_MTY_INV | float | 持有至到期投资 | |
| INC_PLEDGE_LOAN | float | 其中:质押借款 | |
| IND_ACCT_ASSETS | float | 独立账户资产 | |
| IND_ACCT_LIAB | float | 独立账户负债 | |
| INT_RECEIVABLE | float | 应收利息 | |
| INTANGIBLE_ASSETS | float | 无形资产 | |
| INTEREST_PAYABLE | float | 应付利息 | |
| INV | float | 存货 | |
| INV_REALESTATE | float | 投资性房地产 | |
| LEASE_LIABILITY | float | 租赁负债 | |
| LEND_FUNDS | float | 融出资金 | |
| LENDING_FUNDS | float | 拆出资金 | |
| LESS_TREASURY_STK | float | 减:库存股 | |
| LIA_HFS | float | 持有待售的负债 | |
| LIFE_INSUR_RESV | float | 寿险责任准备金 | |
| LT_DEFERRED_EXP | float | 长期待摊费用 | |
| LT_EMP_COMP_PAY | float | 长期应付职工薪酬 | |
| LT_EQUITY_INV | float | 长期股权投资 | |
| LT_LOAN | float | 长期借款 | |
| LT_PAYABLE | float | 长期应付款 | |
| LT_PAYABLE_TOTAL | float | 长期应付款(合计)(元) |  |
| LT_RECEIVABLES | float | 长期应收款 | |
| MINORITY_EQUITY | float | 少数股东权益 | |
| NOM_RISKS_PREP | float | 一般风险准备 | |
| NOTES_PAYABLE | float | 应付票据 | |
| NOTES_RECEIVABLE | float | 应收票据 | |
| OTH_COMP_INCOME | float | 其他综合收益 | |
| OTH_EQUITY_TOOLS | float | 其他权益工具 | |
| OTH_NONCUR_ASSETS | float | 其他非流动资产 | |
| OTHER_ASSETS | float | 其他资产 | |
| OTHER_CUR_ASSETS | float | 其他流动资产 | |
| OTHER_CUR_LIAB | float | 其他流动负债 | |
| OTHER_DEBT_INV | float | 其他债权投资(元) |  |
| OTHER_EQUITY_INV | float | 其他权益工具投资(元) |  |
| OTHER_LIAB | float | 其他负债 | |
| OTHER_NONCUR_LIAB | float | 其他非流动负债 | |
| OTHER_PAYABLE | float | 其他应付款 | |
| OTHER_RCV_TOTAL | float | 其他应收款(合计)（元） |  |
| OTHER_RECEIVABLE | float | 其他应收款 | |
| OUT_LOSS_RESV | float | 未决赔款准备金 | |
| PAYABLE | float | 应付款项 | |
| PRECIOUS_METAL | float | 贵金属 | |
| PREPAYMENT | float | 预付款项 | |
| PROD_BIO_ASSETS | float | 生产性生物资产 | |
| RCV_FINANCING | float | 应收款项融资 | |
| RCV_INV | float | 应收款项类投资 | |
| RECEIVABLE_PREM | float | 应收保费 | |
| SETTLE_FUNDS | float | 结算备付金 | |
| SPE_CUR_LIAB_DIFF | float | 流动负债差额(特殊报表科目) |  |
| SPE_LIAB_BAL_DIFF | float | 负债差额(特殊报表科目) |  |
| SPECIAL_PAYABLE | float | 专项应付款 | |
| SPECIAL_RESV | float | 专项储备 | |
| ST_BONDS_PAYABLE | float | 应付短期债券 | |
| ST_BORROWING | float | 短期借款 | |
| ST_FIN_PAYABLE | float | 应付短期融资款 | |
| SUBR_RCV | float | 应收代位追偿款 | |
| SURPLUS_RESV | float | 盈余公积金 | |
| TAX_PAYABLE | float | 应交税费 | |
| TOT_CUR_LIAB_DIFF | float | 流动负债差额(合计平衡项目) |  |
| TOT_LIAB_BAL_DIFF | float | 负债差额(合计平衡项目) |  |
| TOT_NONCUR_ASSETS | float | 非流动资产合计 | |
| TOT_SHARE | float | 期末总股本 | |
| TOTAL_ASSETS | float | 资产总计 | |
| TOTAL_CUR_ASSETS | float | 流动资产合计 | |
| TOTAL_CUR_LIAB | float | 流动负债合计 | |
| TOTAL_LIAB | float | 负债合计 | |
| TOTAL_NONCUR_LIAB | float | 非流动负债合计 | |
| TRADING_FIN_LIAB | float | 交易性金融负债 | |
| TRADING_FINASSETS | float | 交易性金融资产 | |
| UNAMORTIZED_EXP | float | 待摊费用 | |
| UNDISTRIBUTED_PRO | float | 未分配利润 | |
| UNEARNED_PREM_RESV | float | 未到期责任准备金 | |
| USE_RIGHT_ASSETS | float | 使用权资产 | |
| ASSET_DEP_FUNDS_OTH_FIN_INST | float | 存放同业和其它金融机构款项 |  |
| CASH_CENTRAL_BANK_DEPOSITS | float | 现金及存放中央银行款项 |  |
| CED_INSUR_CONT_RESERVES_RCV | float | 应收分保合同准备金 |  |
| CLIENTS_FUND_DEPOSIT | float | 客户资金存款 |  |
| CNVD_DIFF_FOREIGN_CURR_STAT | float | 外币报表折算差额 |  |
| CONST_IN_PROC_TOTAL | float | 在建工程(合计)(元) |  |
| CONSUMP_BIO_ASSETS | float | 消耗性生物资产 |  |
| DEFERRED_INC_NONCUR_LIAB | float | 递延收益-非流动负债 |  |
| DEP_RECEIVED_IB_DEP | float | 吸收存款及同业存放 |  |
| DISPOSAL_FIX_ASSETS | float | 固定资产清理 |  |
| FIN_ASSETS_AVA_FOR_SALE | float | 可供出售金融资产 |  |
| FIN_ASSETS_COST_SHARING | float | 以摊余成本计量的金融资产 |  |
| FIN_ASSETS_FAIR_VALUE | float | 以公允价值计量且其变动计入其他综合收益的金融资产 |  |
| FIXED_TERM_DEPOSITS | float | 定期存款 |  |
| HOLD_ASSETS_FOR_SALE | float | 持有待售的资产 |  |
| INCL_TRADING_SEAT_FEES | float | 其中:交易席位费 |  |
| INSURED_DEPOSIT_INV | float | 保户储金及投资款 |  |
| INSURED_DIV_PAYABLE | float | 应付保单红利 |  |
| LIAB_DEP_FUNDS_OTH_FIN_INST | float | 同业和其它金融机构存放款项 |  |
| LOANS_AND_ADVANCES | float | 发放贷款及垫款 |  |
| LOANS_FROM_OTH_BANKS | float | 拆入资金 |  |
| LOAN_CENTRAL_BANK | float | 向中央银行借款 |  |
| LT_HEALTH_INSUR_RESV | float | 长期健康险责任准备金 |  |
| NONCUR_ASSETS_DUE_WITHIN_1Y | float | 一年内到期的非流动资产 |  |
| NONCUR_LIAB_DUE_WITHIN_1Y | float | 一年内到期的非流动负债 |  |
| OIL_AND_GAS_ASSETS | float | 油气资产 |  |
| OTHER_NONCUR_FIN_ASSETS | float | 其他非流动金融资产(元) |  |
| OTHER_PAYABLE_TOTAL | float | 其他应付款(合计)(元) |  |
| OTHER_SUSTAIN_BOND | float | 其他权益工具:永续债(元) |  |
| OTH_EQUITY_TOOLS_PRE_SHR | float | 其他权益工具:优先股 |  |
| PAYABLE_FOR_REINSURER | float | 应付分保账款 |  |
| RCV_CED_CLAIM_RESV | float | 应收分保未决赔款准备金 |  |
| RCV_CED_LIFE_INSUR_RESV | float | 应收分保寿险责任准备金 |  |
| RCV_CED_LT_HEALTH_INSUR_RESV | float | 应收分保长期健康险责任准备金 |  |
| RCV_CED_UNEARNED_PREM_RESV | float | 应收分保未到期责任准备金 |  |
| RED_MON_CAP_FOR_SALE | float | 买入返售金融资产 |  |
| REINSURANCE_ACC_RCV | float | 应收分保账款 |  |
| RSRV_FUND_INSUR_CONT | float | 保险合同准备金 |  |
| SELL_REPO_FIN_ASSETS | float | 卖出回购金融资产款 |  |
| SERVICE_CHARGE_COMM_PAYABLE | float | 应付手续费及佣金 |  |
| SPE_ASSETS_BAL_DIFF | float | 资产差额(特殊报表科目) |  |
| SPE_CUR_ASSETS_DIFF | float | 流动资产差额(特殊报表科目) |  |
| SPE_LIAB_EQUITY_BAL_DIFF | float | 负债及股东权益差额(特殊报表项目) |  |
| SPE_NONCUR_ASSETS_DIFF | float | 非流动资产差额(特殊报表科目) |  |
| SPE_NONCUR_LIAB_DIFF | float | 非流动负债差额(特殊报表科目) |  |
| SPE_SHARE_EQUITY_BAL_DIFF | float | 股东权益差额(特殊报表科目) |  |
| TOTAL_LIAB_SHARE_EQUITY | float | 负债及股东权益总计 |  |
| TOT_ASSETS_BAL_DIFF | float | 资产差额(合计平衡项目) |  |
| TOT_CUR_ASSETS_DIFF | float | 流动资产差额(合计平衡项目) |  |
| TOT_LIAB_EQUITY_BAL_DIFF | float | 负债及股东权益差额(合计平衡项目) |  |
| TOT_NONCUR_ASSETS_DIFF | float | 非流动资产差额(合计平衡项目) |  |
| TOT_NONCUR_LIAB_DIFF | float | 非流动负债差额(合计平衡项目) |  |
| TOT_SHARE_EQUITY_BAL_DIFF | float | 股东权益差额(合计平衡项目) |  |
| TOT_SHARE_EQUITY_EXCL_MIN_INT | float | 股东权益合计(不含少数股东权益) |  |
| TOT_SHARE_EQUITY_INCL_MIN_INT | float | 股东权益合计(含少数股东权益) |  |
| UNCONFIRMED_INV_LOSS | float | 未确认的投资损失 |  |

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
balance_sheet = info_data_object.get_balance_sheet(all_code_list, local_path='D://AmazingData_local_data//')
```
