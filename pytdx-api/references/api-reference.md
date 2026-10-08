# pytdx API 完整参考

## 目录
- [标准市场 API (TdxHq_API)](#标准市场-api-tdxhq_api)
- [扩展市场 API (TdxExHq_API)](#扩展市场-api-tdxexhq_api)
- [数据字段说明](#数据字段说明)

---

## 标准市场 API (TdxHq_API)

### 连接管理

#### connect(self, ip='101.227.73.20', port=7709, time_out=5.0, bindport=None, bindip='0.0.0.0')
连接到通达信服务器

**参数：**
- `ip` (str): 服务器IP地址，默认为'101.227.73.20'
- `port` (int): 服务器端口，默认为7709
- `time_out` (float): 连接超时时间（秒），默认5.0
- `bindport` (int): 绑定的本地端口，可选
- `bindip` (str): 绑定的本地IP，默认'0.0.0.0'

**返回：**
- bool: 是否连接成功

**示例：**
```python
api = TdxHq_API()
if api.connect('119.147.212.81', 7709):
    print("连接成功")
    api.disconnect()
```

#### disconnect(self)
断开与通达信服务器的连接

#### close(self)
disconnect的别名，支持with语句

---

### 行情数据查询

#### get_security_quotes(self, all_stock, code=None)
获取股票实时行情报价

**参数形式：**
1. `get_security_quotes(market, code)` - 单个股票
2. `get_security_quotes((market, code))` - 元组形式
3. `get_security_quotes([(market1, code1), (market2, code2)])` - 批量查询

**参数：**
- `all_stock`: 股票标识，可以是单个(market, code)或列表
- `code` (str, optional): 股票代码

**返回：**
- list: 行情数据列表，每个元素为包含以下字段的字典：
  - `market`: 市场代码
  - `code`: 股票代码
  - `active1`: 激活状态
  - `price`: 当前价格
  - `last_close`: 昨收价
  - `open`: 开盘价
  - `high`: 最高价
  - `low`: 最低价
  - `servertime`: 服务器时间
  - `reversed_bytes0`: 保留字段
  - `reversed_bytes1`: 保留字段
  - `vol`: 成交量（手）
  - `cur_vol`: 当前成交量
  - `amount`: 成交金额
  - `s_vol`: 内盘
  - `b_vol`: 外盘
  - `reversed_bytes2`: 保留字段
  - `reversed_bytes3`: 保留字段
  - `bid1-10`: 买一至买十价
  - `ask1-10`: 卖一至卖十价
  - `bid_vol1-10`: 买一至买十量
  - `ask_vol1-10`: 卖一至卖十量

**示例：**
```python
# 查询单个股票
data = api.get_security_quotes([(0, '000001')])

# 批量查询
stocks = [(0, '000001'), (1, '600000'), (0, '000002')]
data = api.get_security_quotes(stocks)
```

---

### K线数据

#### get_security_bars(self, category, market, code, start, count)
获取股票K线数据

**参数：**
- `category` (int): K线类别（见核心概念-K线类别）
- `market` (int): 市场代码（0:深圳, 1:上海）
- `code` (str): 股票代码
- `start` (int): 起始位置（0表示最新数据）
- `count` (int): 获取数量（最大800）

**返回：**
- list: K线数据列表，每个元素包含：
  - `datetime`: 时间
  - `open`: 开盘价
  - `close`: 收盘价
  - `high`: 最高价
  - `low`: 最低价
  - `vol`: 成交量
  - `amount`: 成交金额

**示例：**
```python
# 获取000001最近100根日K线
data = api.get_security_bars(4, 0, '000001', 0, 100)
df = api.to_df(data)
```

#### get_index_bars(self, category, market, code, start, count)
获取指数K线数据（参数和返回值与get_security_bars相同）

**示例：**
```python
# 获取上证指数日K线
data = api.get_index_bars(4, 1, '000001', 0, 100)
```

#### get_k_data(self, code, start_date, end_date)
获取指定日期范围的K线数据

**参数：**
- `code` (str): 股票代码
- `start_date` (str): 开始日期，格式'YYYY-MM-DD'
- `end_date` (str): 结束日期，格式'YYYY-MM-DD'

**返回：**
- list: K线数据列表

---

### 分时数据

#### get_minute_time_data(self, market, code)
获取当日分时数据

**参数：**
- `market` (int): 市场代码
- `code` (str): 股票代码

**返回：**
- list: 分时数据列表，每个元素包含：
  - `datetime`: 时间
  - `price`: 价格
  - `vol`: 成交量

#### get_history_minute_time_data(self, market, code, date)
获取历史分时数据

**参数：**
- `market` (int): 市场代码
- `code` (str): 股票代码
- `date` (int): 日期，格式YYYYMMDD

**返回：**
- list: 分时数据列表

---

### 成交明细

#### get_transaction_data(self, market, code, start, count)
获取当日成交明细

**参数：**
- `market` (int): 市场代码
- `code` (str): 股票代码
- `start` (int): 起始位置
- `count` (int): 获取数量（最大1800）

**返回：**
- list: 成交明细列表，每个元素包含：
  - `time`: 成交时间
  - `price`: 成交价格
  - `vol`: 成交量
  - `num`: 成交笔数
  - `buyorsell`: 买卖方向（0:买, 1:卖）

#### get_history_transaction_data(self, market, code, start, count, date)
获取历史成交明细

**参数：**
- `date` (int): 日期，格式YYYYMMDD

---

### 股票列表

#### get_security_count(self, market)
获取市场股票数量

**参数：**
- `market` (int): 市场代码

**返回：**
- int: 股票数量

#### get_security_list(self, market, start)
获取股票列表

**参数：**
- `market` (int): 市场代码
- `start` (int): 起始位置

**返回：**
- list: 股票列表，每个元素包含：
  - `code`: 股票代码
  - `volunit`: 交易单位
  - `decimal_point`: 小数点
  - `name`: 股票名称
  - `pre_close`: 昨收价

---

### 财务数据

#### get_finance_info(self, market, code)
获取财务信息

**参数：**
- `market` (int): 市场代码
- `code` (str): 股票代码

**返回：**
- dict: 财务数据字典，包含：
  - `code`: 股票代码
  - `name`: 股票名称
  - `liutongguben`: 流通股本
  - `guojiagugu`: 国家持股
  - `faqirenfarengu`: 发起人法人股
  - `farengu`: 法人股
  - `bgugu`: B股
  - `hgugu`: H股
  - `zhigonggu`: 职工股
  - `zongguben`: 总股本
  - `weiguoyoufarengu`: 未流通股份
  - `weiliutongfarengu`: 未流通法人股
  - `payout`: 派息率
  - `pubdate`: 发布日期

---

### 公司信息

#### get_company_info_category(self, market, code)
获取公司信息分类

**参数：**
- `market` (int): 市场代码
- `code` (str): 股票代码

**返回：**
- list: 公司信息分类列表，每个元素包含：
  - `filename`: 文件名
  - `start`: 起始位置
  - `length`: 长度

#### get_company_info_content(self, market, code, filename, start, length)
获取公司信息内容

**参数：**
- `filename` (str): 文件名（从get_company_info_category获取）
- `start` (int): 起始位置
- `length` (int): 内容长度

**返回：**
- str: 公司信息内容

---

### 复权因子

#### get_xdxr_info(self, market, code)
获取除权除息信息

**参数：**
- `market` (int): 市场代码
- `code` (str): 股票代码

**返回：**
- list: 除权除息信息列表，每个元素包含：
  - `year`: 年份
  - `month`: 月份
  - `day`: 日期
  - `category`: 类别（1:除权, 2:除息, 3:除权除息）
  - `fenghong`: 分红（每股）
  - `peigu`: 配股（每股）
  - `peigujia`: 配股价
  - `songgu`: 送股（每股）
  - `zhuanzeng`: 转增（每股）
  - `suogu`: 缩股（每股）

---

### 板块信息

#### get_block_info(self, blockfile, start, size)
获取板块信息

**参数：**
- `blockfile` (str): 板块文件名
- `start` (int): 起始位置
- `size` (int): 获取数量

**返回：**
- list: 板块信息列表

#### get_block_info_meta(self, blockfile)
获取板块信息元数据

#### get_and_parse_block_info(self, blockfile)
获取并解析板块信息

---

### 其他功能

#### do_heartbeat(self)
发送心跳包保持连接

#### get_traffic_stats(self)
获取流量统计信息

**返回：**
- dict: 包含发送和接收字节数

#### to_df(self, v)
将返回数据转换为DataFrame

**参数：**
- `v`: API返回的数据

**返回：**
- DataFrame: pandas DataFrame对象

---

## 扩展市场 API (TdxExHq_API)

扩展市场API用于获取期货、期权、港股、美股等扩展市场数据。使用方法与标准市场API类似。

### 连接管理
- `connect()`: 连接扩展市场服务器
- `disconnect()`: 断开连接
- `close()`: 别名

### 市场信息

#### get_markets(self)
获取支持的市场列表

**返回：**
- list: 市场列表，每个元素包含：
  - `market`: 市场代码
  - `name`: 市场名称

---

### 行情数据

#### get_instrument_quote(self, market, code)
获取合约行情

**参数：**
- `market` (int): 市场代码
- `code` (str): 合约代码

**返回：**
- list: 行情数据

#### get_instrument_quote_list(self, market, category, start=0, count=80)
获取合约行情列表

**参数：**
- `market` (int): 市场代码
- `category` (int): 类别
- `start` (int): 起始位置
- `count` (int): 获取数量

---

### K线数据

#### get_instrument_bars(self, category, market, code, start=0, count=700)
获取合约K线数据

**参数：**
- `category` (int): K线类别
- `market` (int): 市场代码
- `code` (str): 合约代码
- `start` (int): 起始位置
- `count` (int): 获取数量

**返回：**
- list: K线数据列表

#### get_history_instrument_bars_range(self, market, code, start, end)
获取历史K线数据（指定时间范围）

**参数：**
- `market` (int): 市场代码
- `code` (str): 合约代码
- `start` (int): 开始时间
- `end` (int): 结束时间

---

### 分时数据

#### get_minute_time_data(self, market, code)
获取当日分时数据

#### get_history_minute_time_data(self, market, code, date)
获取历史分时数据

---

### 成交明细

#### get_transaction_data(self, market, code, start=0, count=1800)
获取当日成交明细

#### get_history_transaction_data(self, market, code, date, start=0, count=1800)
获取历史成交明细

---

### 合约信息

#### get_instrument_count(self)
获取合约数量

#### get_instrument_info(self, start, count=100)
获取合约信息

**参数：**
- `start` (int): 起始位置
- `count` (int): 获取数量

**返回：**
- list: 合约信息列表

---

## 数据字段说明

### K线数据字段
- `datetime`: 时间戳
- `open`: 开盘价
- `close`: 收盘价
- `high`: 最高价
- `low`: 最低价
- `vol`: 成交量
- `amount`: 成交金额

### 行情数据字段
- `price`: 当前价
- `open`: 开盘价
- `high`: 最高价
- `low`: 最低价
- `last_close`: 昨收价
- `vol`: 成交量
- `amount`: 成交金额
- `bid1-10`: 买价（买一至买十）
- `ask1-10`: 卖价（卖一至卖十）
- `bid_vol1-10`: 买量
- `ask_vol1-10`: 卖量

### 成交明细字段
- `time`: 成交时间
- `price`: 成交价格
- `vol`: 成交量
- `num`: 成交笔数
- `buyorsell`: 买卖方向（0:买, 1:卖）
