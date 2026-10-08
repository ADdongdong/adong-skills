## 现金流量表

**接口**: get_cash_flow

**描述**: 获取指定股票列表的上市公司的现金流量表数据

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
| IS_CALCULATION | int | 是否计算报表 | |
| ABSORB_CASH_RECP_INV | double | 吸收投资收到的现金 | |
| AMORT_INTAN_ASSETS | double | 无形资产摊销 | |
| AMORT_LT_DEFERRED_EXP | double | 长期待摊费用摊销 | |
| BEG_BAL_CASH_CASH_EQU | double | 期初现金及现金等价物余额 | |
| CASH_END_BAL | double | 现金的期末余额 | |
| CASH_FOR_CHARGE | double | 支付手续费的现金 | |
| CASH_PAID_INSUR_POLICY | double | 支付保单红利的现金 | |
| CASH_PAID_INV | double | 投资支付的现金 | |
| CASH_PAID_PUR_CONST_FIOLTA | double | 购建固定资产、无形资产和其他长期资产支付的现金 | |
| CASH_PAY_CLAIMS_OIC | double | 支付原保险合同赔付款项的现金 | |
| CASH_PAY_DIST_DIV_PRO_INT | double | 分配股利、利润或偿付利息支付的现金 | |
| CASH_PAY_EMPLOYEE | double | 支付给职工以及为职工支付的现金 | |
| CASH_PAY_FOR_DEBT | double | 偿还债务支付的现金 | |
| CASH_PAY_GOODS_SERVICES | double | 购买商品、接受劳务支付的现金 | |
| CASH_RECE_BORROW | double | 取得借款收到的现金 | |
| CASH_RECE_ISSUE_BONDS | double | 发行债券收到的现金 | |
| CASH_RECP_INV_INCOME | double | 取得投资收益收到的现金 | |
| CASH_RECP_PREM_OIC | double | 收到原保险合同保费取得的现金 | |
| CASH_RECP_RECOV_INV | double | 收回投资收到的现金 | |
| CASH_RECP_SG_AND_RS | double | 销售商品、提供劳务收到的现金 | |
| CONV_CORP_BONDS_DUE_WITHIN_1Y | double | 一年内到期的可转换公司债券 | |
| CONV_DEBT_INTO_CAP | double | 债务转为资本 | |
| CREDIT_IMPAIR_LOSS | double | 信用减值损失 | |
| DECR_DEFE_INC_TAX_ASSETS | double | 递延所得税资产减少 | |
| DECR_DEFERRED_EXPENSE | double | 待摊费用减少 | |
| DECR_INVENTORY | double | 存货的减少 | |
| DECR_OPERA_RECEIVABLE | double | 经营性应收项目的减少 | |
| DEPRE_FA_OGA_PBA | double | 固定资产折旧、油气资产折耗、生产性生物资产折旧 | |
| EFF_FX_FLUC_CASH | double | 汇率变动对现金的影响 | |
| END_BAL_CASH_CASH_EQU | double | 期末现金及现金等价物余额 | |
| FINANCIAL_EXP | double | 财务费用 | |
| FIXED_ASSETS_FIN_LEASE | double | 融资租入固定资产 | |
| FREE_CASH_FLOW | double | 企业自由现金流量 | |
| INCL_CASH_RECP_SAIMS | double | 其中:子公司吸收少数股东投资收到的现金 | |
| INCL_DIV_PRO_PAID_SMS | double | 其中:子公司支付给少数股东的股利、利润 | |
| INCR_ACCRUED_EXP | double | 预提费用增加 | |
| INCR_DEFE_INC_TAX_LIAB | double | 递延所得税负债增加 | |
| INCR_OPERA_PAYABLE | double | 经营性应付项目的增加 | |
| IND_NET_CASH_FLOWS_OPERA_ACT | double | 间接法-经营活动产生的现金流量净额 | |
| IND_NET_INCR_CASH_AND_EQU | double | 间接法-现金及现金等价物净增加额 | |
| INV_LOSS | double | 投资损失 | |
| LESS_OPEN_BAL_CASH | double | 减:现金的期初余额 | |
| LESS_OPEN_BAL_CASH_EQU | double | 减:现金等价物的期初余额 | |
| LOSS_DISP_FIOLTA | double | 处置固定、无形资产和其他长期资产的损失 | |
| LOSS_FAIRVALUE_CHG | double | 公允价值变动损失 | |
| LOSS_FIXED_ASSETS | double | 固定资产报废损失 | |
| NET_CASH_FLOWS_FIN_ACT | double | 筹资活动产生的现金流量净额 | |
| NET_CASH_FLOWS_INV_ACT | double | 投资活动产生的现金流量净额 | |
| NET_CASH_FLOWS_OPERA_ACT | double | 经营活动产生的现金流量净额 | |
| NET_CASH_PAID_SOBU | double | 取得子公司及其他营业单位支付的现金净额 | |
| NET_CASH_REC_SEC | double | 代理买卖证券收到的现金净额 | |
| NET_CASH_RECP_DISP_FIOLTA | double | 处置固定资产、无形资产和其他长期资产收回的现金净额 | |
| NET_CASH_RECP_DISP_SOBU | double | 处置子公司及其他营业单位收到的现金净额 | |
| NET_CASH_RECP_REINSU_BUS | double | 收到再保业务现金净额 | |
| NET_INCR_BORR_FUND | double | 拆入资金净增加额 | |
| NET_INCR_BORR_OFI | double | 向其他金融机构拆入资金净增加额 | |
| NET_INCR_CASH_AND_CASH_EQU | double | 现金及现金等价物净增加额 | |
| NET_INCR_CUS_LOAN_ADV | double | 客户贷款及垫款净增加额 | |
| NET_INCR_DEP_CB_IB | double | 存放央行和同业款项净增加额 | |
| NET_INCR_DEP_CUS_AND_IB | double | 客户存款和同业存放款项净增加额 | |
| NET_INCR_DISMANTLE_CAP | double | 拆出资金净增加额 | |
| NET_INCR_DISP_FAAS | double | 处置可供出售金融资产净增加额 | |
| NET_INCR_DISP_TFA | double | 处置交易性金融资产净增加额 | |
| NET_INCR_INSURED_SAVE | double | 保户储金净增加额 | |
| NET_INCR_INT_AND_CHARGE | double | 收取利息和手续费净增加额 | |
| NET_INCR_LOANS_CENTRAL_BANK | double | 向中央银行借款净增加额 | |
| NET_INCR_PLEDGE_LOAN | double | 质押贷款净增加额 | |
| NET_INCR_REPU_BUS_FUND | double | 回购业务资金净增加额 | |
| NET_PROFIT | double | 净利润 | |
| OTH_CASH_PAY_INV_ACT | double | 支付其他与投资活动有关的现金 | |
| OTH_CASH_PAY_OPERA_ACT | double | 支付其他与经营活动有关的现金 | |
| OTH_CASH_RECP_INV_ACT | double | 收到其他与投资活动有关的现金 | |
| OTHER_ASSETS_IMPAIR_LOSS | double | 其他资产减值损失 | |
| OTHER_CASH_PAY_FIN_ACT | double | 支付其他与筹资活动有关的现金 | |
| OTHER_CASH_RECP_FIN_ACT | double | 收到其他与筹资活动有关的现金 | |
| OTHER_CASH_RECP_OPER_ACT | double | 收到其他与经营活动有关的现金 | |
| OTHERS | double | 其他（废弃） | |
| PAY_ALL_TAX | double | 支付的各项税费 | |
| PLUS_ASSETS_DEPRE_PREP | double | 加:资产减值准备 | |
| PLUS_END_BAL_CASH_EQU | double | 加:现金等价物的期末余额 | |
| RECP_TAX_REFUND | double | 收到的税费返还 | |
| SPE_BAL_CASH_INFLOW_FIN_ACT | double | 筹资活动现金流入差额 | |
| SPE_BAL_CASH_INFLOW_INV_ACT | double | 投资活动现金流入差额 | |
| SPE_BAL_CASH_INFLOW_OPERA_ACT | double | 经营活动现金流入差额 | |
| SPE_BAL_CASH_OUTFLOW_FIN | double | 筹资活动现金流出差额 | |
| SPE_BAL_CASH_OUTFLOW_INV | double | 投资活动现金流出差额 | |
| SPE_BAL_CASH_OUTFLOW_OPERA | double | 经营活动现金流出差额 | |
| SPE_BAL_NETCASH_INC_DIFF_IND | double | 间接法-现金净增加额差额 | |
| SPE_BAL_NETCASH_INCR_DIFF | double | 现金净增加额差额 | |
| SPE_BAL_NETCASH_OPERA_IND | double | 间接法-经营活动现金流量净额差额 | |
| TOT_BAL_CASH_INFLOW_FIN_ACT | double | 筹资活动现金流入差额 | |
| TOT_BAL_CASH_INFLOW_INV_ACT | double | 投资活动现金流入差额 | |
| TOT_BAL_CASH_INFLOW_OPERA_ACT | double | 经营活动现金流入差额 | |
| TOT_BAL_CASH_OUTFLOW_FIN | double | 筹资活动现金流出差额 | |
| TOT_BAL_CASH_OUTFLOW_INV | double | 投资活动现金流出差额 | |
| TOT_BAL_CASH_OUTFLOW_OPERA | double | 经营活动现金流出差额 | |
| TOT_BAL_NETCASH_FLOW_FIN | double | 筹资活动产生的现金流量净额差额 | |
| TOT_BAL_NETCASH_FLOW_INV | double | 投资活动产生的现金流量净额差额 | |
| TOT_BAL_NETCASH_FLOW_OPERA | double | 经营活动产生的现金流量净额差额 | |
| TOT_BAL_NETCASH_INC_DIFF_IND | double | 间接法-现金净增加额差额 | |
| TOT_BAL_NETCASH_INCR_DIFF | double | 现金净增加额差额 | |
| TOT_BAL_NETCASH_OPERA_IND | double | 间接法-经营活动现金流量净额差额 | |
| TOT_CASH_INFLOW_FIN_ACT | double | 筹资活动现金流入小计 | |
| TOT_CASH_INFLOW_INV_ACT | double | 投资活动现金流入小计 | |
| TOT_CASH_INFLOW_OPER_ACT | double | 经营活动现金流入小计 | |
| TOT_CASH_OUTFLOW_FIN_ACT | double | 筹资活动现金流出小计 | |
| TOT_CASH_OUTFLOW_INV_ACT | double | 投资活动现金流出小计 | |
| TOT_CASH_OUTFLOW_OPERA_ACT | double | 经营活动现金流出小计 | |
| UNCONFIRMED_INV_LOSS | double | 未确认投资损失 | |
| USE_RIGHT_ASSET_DEP | double | 使用权资产折旧 | |

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
cash_flow = info_data_object.get_cash_flow(all_code_list, local_path='D://AmazingData_local_data//')
```
