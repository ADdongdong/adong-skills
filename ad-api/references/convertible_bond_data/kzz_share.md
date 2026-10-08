## 可转债份额

**接口**: get_kzz_share

**描述**: 获取指定可转债列表的可转债份额数据

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
| CHANGE_DATE | string | 变动日期 | |
| ANN_DATE | string | 公告日期 | |
| MARKET_CODE | string | 市场代码 | |
| BOND_SHARE | float | 债券份额(万元) | |
| CONV_SHARE | float | 已转成股份数 | |
| CHANGE_REASON | string | 变动原因代码，目前包含的枚举类型:ZZG转债转股SH赎回KZZS可转债上市HS回售DQ到期QLXQ权利行权TQDF本金提前兑付GH购回HSZG 回售转股HGZG 回购转股 | ZZG:转债转股 SH:赎回 KZZS:可转债上市 HS:回售 DQ:到期 QLXQ:权利行权 TQDF:本金提前兑付 GH:购回 HSZG:回售转股 HGZG:回购转股 |

### 示例代码

```python
import AmazingData as ad

ad.login(username='username', password='password', host='***.***.***.***', port=****)
info_data_object = ad.InfoData()
base_data_object = ad.BaseData()
code_list = base_data_object.get_code_list('EXTRA_KZZ')
kzz_share = info_data_object.get_kzz_share(code_list, is_local=False)
```
