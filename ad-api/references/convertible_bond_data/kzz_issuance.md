## 可转债发行

**接口**: get_kzz_issuance

**描述**: 获取指定可转债列表的可转债发行数据

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| code_list | list[str] | 是 | 支持可转债的代码列表 |
| local_path | str | 是 | 本地存储数据的路径，需绝对路径，格式类似"'D://AmazingData_local_data//'" |
| is_local | bool | 否 | 默认为True，本地数据缓存方案 |

### 输出参数

返回dict，key为code，value为DataFrame，主要字段包含：

| 字段 | 类型 | 说明 | 备注 |
|------|------|------|------|
| MARKET_CODE | string | 市场代码 | |
| STOCK_CODE | string | 正股代码 | |
| CRNCY_CODE | string | 货币代码 | |
| ANN_DT | string | 公告日期 | |
| PRE_PLAN_DATE | string | 预案公告日 | |
| LISTED_ANN_DATE | string | 上市公告日 | |
| LISTED_DATE | string | 上市日期 | |
| PLAN_SCHEDULE | string | 方案进度1: 董事会预案2: 股东大会通过3: 实施4: 未通过5: 证监会通过6: 达成转让意向7: 签署转让协议8: 国资委批准9: 商务部批准10: 过户11: 延期实施12: 停止实施13: 分红方案待定 | 1:董事会预案 2:股东大会通过 3:实施 4:未通过 5:证监会通过 6:达成转让意向 7:签署转让协议 8:国资委批准 9:商务部批准 10:过户 11:延期实施 12:停止实施 13:分红方案待定 |
| IS_SEPARATION | int | 是否分离交易可转债 | |
| RECOMMENDER | string | 上市推荐人 | |
| CLAUSE_IS_INT_CHA_DEPO_RATE | int | 利率是否随存款利率调整 | |
| CLAUSE_IS_COM_INT | int | 是否有利息补偿条款 | |
| CLAUSE_COM_INT_RATE | float | 补偿利率(%) | |
| CLAUSE_COM_INT_DESC | string | 补偿利率说明 | |
| CLAUSE_INIT_CONV_PRICE_ITEM | string | 初始转股价条款 | |
| CLAUSE_CONV_ADJ_ITEM | string | 转股价格调整条款 | |
| CLAUSE_CONV_PERIOD_ITEM | string | 转换期条款 | |
| CLAUSE_INI_CONV_PRICE | float | 初始转换价格 | |
| CLAUSE_PUT_ITEM | string | 回售条款 | |
| CLAUSE_CALL_ITEM | string | 赎回条款 | |
| CLAUSE_SPEC_DOWN_ADJ | string | 特别向下修正条款 | |
| CLAUSE_ORIG_RATION_ARR_ITEM | string | 向原股东配售安排条款 | |
| LIST_PASS_DATE | string | 发审通过公告日 | |
| LIST_PERMIT_DATE | string | 证监会核准公告日 | |
| LIST_ANN_DATE | string | 发行公告日 | |
| LIST_RESULT_ANN_DATE | string | 发行结果公告日 | |
| LIST_TYPE | string | 发行方式 | |
| LIST_FEE | float | 发行费用 | |
| LIST_RATION_DATE | string | 老股东配售日期 | |
| LIST_RATION_REG_DATE | string | 老股东配售股权登记日 | |
| LIST_RATION_PAYMT_DATE | string | 老股东配售缴款日 | |
| LIST_RATION_CODE | string | 老股东配售代码 | |
| LIST_RATION_NAME | string | 老股东配售简称 | |
| LIST_RATION_PRICE | float | 老股东配售价格 | |
| LIST_RATION_RATIO_DE | float | 老股东配售比例分母 | |
| LIST_RATION_RATIO_MO | float | 老股东配售比例分子 | |
| LIST_RATION_VOL | float | 向老股东配售数量(张)） |  |
| LIST_HOUSEHOLD | float | 老股东配售户数 | |
| LIST_ONL_DATE | string | 上网发行日期 | |
| LIST_PCHASE_CODE_ONL | string | 上网发行申购代码 | |
| LIST_PCH_NAME_ONL | string | 上网发行申购名称 | |
| LIST_PCH_PRICE_ONL | float | 上网发行申购价格 | |
| LIST_ISSUE_VOL_ONL | float | 上网发行数量(不含优先配售)(张) | |
| LIST_CODE_ONL | float | 上网发行配号总数 | |
| LIST_EXCESS_PCH_ONL | float | 上网发行超额认购倍数(不含优先配售) | |
| RESULT_EF_SUBSCR_P_OFF | float | 网上有效申购户数(不含优先配售) | |
| RESULT_SUC_RATE_OFF | float | 网上有效申购手数(不含优先配售) | |
| LIST_DATE_INST_OFF | string | 网下向机构投资者发行日期 | |
| LIST_VOL_INST_OFF | float | 网下向机构投资者发行数量(不含优先配售)(张) | |
| RESULT_SUC_RATE_ON | float | 网上中签率(不含优先配售)(%) | |
| LIST_EFFECT_PC_HVOL_OFF | float | 网下有效申购手数(不含优先配售) | |
| LIST_EFF_PC_H_OF | float | 网下有效申购户数(不含优先配售) | |
| LIST_SUC_RATE_OFF | float | 网下中签率(不含优先配售)(%) | |
| PRE_RATION_VOL | float | 网下优先配售数量(张) | |
| LIST_ISSUE_SIZE | float | 发行规模(万元) | |
| LIST_ISSUE_QUANTITY | float | 发行数量(万张) | |
| MIN_OFF_INST_SUBSCR_QTY | float | 网下最小申购数量(机构) | |
| OFF_INST_DEP_RATIO | string | 网下定金比例(机构) | |
| MAX_OFF_INST_SUBSCR_QTY | float | 网下最大申购数量(机构) | |
| OFF_SUBSCR_UNIT_INC_DESC | string | 网下申购累进单位说明 | |
| IS_CONV_BONDS | int | 是否可转债 | |
| MIN_UNLINE_PUBLIC | float | 网下最小申购数量(公众)(元) | |
| MAX_UNLINE_PUBLIC | float | 网上最大申购数量(公众)(元) | |
| TERM_YEAR | float | 借款期限(年) | |
| INTEREST_TYPE | string | 利率类型 | |
| COUPON_RATE | float | 利率(%) | |
| INTEREST_FRE_QUENCY | string | 付息频率 | |
| RESULT_SUC_RATE_ON2 | float | 网上中签率(不含优先配售)(%) | |
| COUPON_TXT | string | 利率说明 | |
| RATIO_ANNCE_DATE | string | 网上中签率公告日 | |
| RATIO_DATE | string | 网上中签结果公告日 | |
| CLAUSE_INI_CONV_PREMIUM_RATIO​ | float | 初始转股价溢价比例（%） |
| SMTG_ANN_DATE​ | string | 股东大会公告日 |

### 示例代码

```python
import AmazingData as ad

ad.login(username='username', password='password', host='***.***.***.***', port=****)
info_data_object = ad.InfoData()
base_data_object = ad.BaseData()
code_list = base_data_object.get_code_list('EXTRA_KZZ')
kzz_issuance = info_data_object.get_kzz_issuance(code_list, is_local=False)
```
