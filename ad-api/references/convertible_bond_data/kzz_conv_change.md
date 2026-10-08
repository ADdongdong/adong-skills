## 可转债转股变动数据

**接口**: get_kzz_conv_change

**描述**: 获取指定可转债列表的可转债转股变动数据

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
| CHANGE_DATE | string | 变动日期 | |
| ANN_DATE | string | 公告日期 | |
| CONV_PRICE | float | 转股价格 | |
| CHANGE_REASON | string | 变动原因，变动原因变动原因名称1发行2换股吸收合并3派息4配股5上市6送股7送转股8送转股,派息9修正10增发11转增,派息12送股,派息13公司选择不行使赎回权14回购注销15回购注销,派息16增发,回购注销17增发,回购注销,派息18增发,派息19换股20派息,转增21派息,转增,增发22派息,送转股24调整25转增26除息 | 1:发行 2:换股吸收合并 3:派息 4:配股 5:上市 6:送股 7:送转股 8:送转股,派息 9:修正 10:增发 11:转增,派息 12:送股,派息 13:公司选择不行使赎回权 14:回购注销 15:回购注销,派息 16:增发,回购注销 17:增发,回购注销,派息 18:增发,派息 19:换股 20:派息,转增 21:派息,转增,增发 22:派息,送转股 24:调整 25:转增 26:除息 |

### 示例代码

```python
import AmazingData as ad

ad.login(username='username', password='password', host='***.***.***.***', port=****)
info_data_object = ad.InfoData()
base_data_object = ad.BaseData()
code_list = base_data_object.get_code_list('EXTRA_KZZ')
kzz_conv_change = info_data_object.get_kzz_conv_change(code_list, is_local=False)
```
