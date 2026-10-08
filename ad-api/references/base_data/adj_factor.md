## 复权因子

**接口**: get_backward_factor

**描述**: 获取后复权因子数据并本地存储

### 输入参数

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| code_list | list[str] | 是 | 代码列表，支持股票、ETF |
| local_path | str | 是 | 本地存储路径 |
| is_local | Bool | 是 | 是否使用本地数据，默认True |

### 输出参数

返回DataFrame，index为交易日期，column为股票代码

### 示例代码

```python
import AmazingData as ad

ad.login(username='username', password='password', host='ip', port=port)
base_data = ad.BaseData()
code_list = base_data.get_code_list(security_type='EXTRA_STOCK_A')
backward_factor = base_data.get_backward_factor(
    code_list,
    local_path='D://AmazingData_local_data//',
    is_local=False
)
```

---

## 复权因子（单次复权因子）

**接口**: BaseData.get_adj_factor

**描述**: 获取复权因子数据并本地存储，复权因子为根据交易所行情数据计算得出的单次复权因子；

### 输入参数

| 参数 | 数据类型 | 必选 | 解释 |
| --- | --- | --- | --- |
| code_list | list[str] | 是 | 代码列表，支持股票、ETF |
| local_path | str | 是 | 本地存储复权因子数据的文件夹地址 |
| is_local | Bool | 是 | 是否使用本地存储的数据，默认为True |

### 说明

- （1）local_path

- 类似'D://AmazingData_local_data//'，只写文件夹的绝对路径即可

- （2）is_local

- True:

- 本地local_path有数据的情况下，从本地取数据，但有可能无法获取最新的数据

- 本地local_path无数据的情况下，从互联网取数据，并更新本地local_path的数据

- False:从互联网取数据，并更新本地local_path的数据

### 输出参数

| 参数 | 数据类型 | 解释 |
| --- | --- | --- |
| adj_factor | dataframe | index为交易日期<br>column为股票代码 |

### 示例代码

```python
# 第一步 登录api
import AmazingData as ad
ad.login(username='username', password='password',host='***.***.***.***',port=****)
base_data_object = ad.BaseData()
code_list = base_data_object.get_code_list(security_type='EXTRA_STOCK_A')
adj_factor = base_data_object.get_adj_factor(code_list, local_path='D://AmazingData_local_data//', is_local=False)
```
