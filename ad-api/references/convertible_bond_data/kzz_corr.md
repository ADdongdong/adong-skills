## 可转债修正数据

**接口**: get_kzz_corr

**描述**: 获取指定可转债列表的可转债修正数据

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| code_list | list[str] | 是 | 支持可转债的代码列表 |
| local_path | str | 是 | 本地存储数据的路径，需绝对路径，格式类似"'D://AmazingData_local_data//'" |
| is_local | bool | 否 | 默认为True，本地数据缓存方案 |

### 输出参数

返回dict，key为code，value为DataFrame，主要字段包含：

| 字段 | 类型 | 说明 |
|------|------|------|
| MARKET_CODE | string | 市场代码 |
| START_DATE | string | 特别修正起始时间 |
| END_DATE | string | 特别修正结束时间 |
| CORR_CONV_PRICE_FLOOR_DESC​ | string | 修正后转股价格底线说明 |
| CORR_TIMES_LIMIT​ | string | 修正次数限制 |
| CORR_TRIG_CALC_MAX_PERIOD​ | float | 修正触发计算最大时间区间（天） |
| CORR_TRIG_CALC_PERIOD​ | float | 修正触发计算时间区间（天） |
| IS_SPEC_DOWN_CORR_CLAUSE_FLAG​ | int | 是否有特别向下修正条款 |
| IS_TIMEPOINT_CORR_CLAUSE_FLAG​ | int | 是否有时点修正条款 |
| REF_PRICE_IS_AVG_PRICE​ | int | 参考价格是否为算术平均价 |
| SPEC_CORR_RANGE​ | float | 特别修正幅度 |
| SPEC_CORR_TRIG_RATIO​ | float | 特别修正触发比例（%） |
| TIMEPOINT_CORR_TEXT_CLAUSE​ | string | 时点修正文字条款 |
| TIMEPOINT_COUNT​ | float | 时点数 |

### 示例代码

```python
import AmazingData as ad

ad.login(username='username', password='password', host='***.***.***.***', port=****)
info_data_object = ad.InfoData()
base_data_object = ad.BaseData()
code_list = base_data_object.get_code_list('EXTRA_KZZ')
kzz_corr = info_data_object.get_kzz_corr(code_list, is_local=False)
```
