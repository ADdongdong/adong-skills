# pytdx 使用示例与最佳实践

## 目录
- [基础用法](#基础用法)
- [常用场景示例](#常用场景示例)
- [最佳实践](#最佳实践)
- [常见问题](#常见问题)

---

## 基础用法

### 安装与导入

```python
# 安装
pip install pytdx==1.72

# 导入标准市场API
from pytdx.hq import TdxHq_API

# 导入扩展市场API
from pytdx.exhq import TdxExHq_API
```

### 连接服务器

#### 方式1：手动管理连接
```python
from pytdx.hq import TdxHq_API

api = TdxHq_API()

# 连接服务器
if api.connect('119.147.212.81', 7709):
    print("连接成功")
    
    # 执行查询操作
    data = api.get_security_bars(4, 0, '000001', 0, 100)
    
    # 断开连接
    api.disconnect()
else:
    print("连接失败")
```

#### 方式2：自动管理连接（推荐）
```python
from pytdx.hq import TdxHq_API

# 使用with语句自动管理连接
with TdxHq_API() as api:
    if api.connect('119.147.212.81', 7709):
        data = api.get_security_bars(4, 0, '000001', 0, 100)
        # 离开with块时自动断开连接
```

### 常用通达信服务器地址

```
标准市场服务器：
- 119.147.212.81:7709
- 218.75.126.9:7709
- 115.238.56.198:7709
- 124.160.88.183:7709
- 60.12.136.250:7709
- 218.108.50.178:7709

扩展市场服务器：
- 61.152.107.171:7727
```

---

## 常用场景示例

### 场景1：获取股票实时行情

```python
from pytdx.hq import TdxHq_API

with TdxHq_API() as api:
    if api.connect('119.147.212.81', 7709):
        # 查询单个股票
        data = api.get_security_quotes([(0, '000001')])
        df = api.to_df(data)
        print(df[['code', 'price', 'open', 'high', 'low', 'vol']])
        
        # 批量查询多只股票
        stocks = [
            (0, '000001'),  # 平安银行
            (1, '600000'),  # 浦发银行
            (0, '000002'),  # 万科A
            (1, '600519'),  # 茅台
        ]
        data = api.get_security_quotes(stocks)
        df = api.to_df(data)
        print(df)
```

### 场景2：获取股票K线数据

```python
from pytdx.hq import TdxHq_API
import matplotlib.pyplot as plt

with TdxHq_API() as api:
    if api.connect('119.147.212.81', 7709):
        # 获取日K线数据（最近100根）
        data = api.get_security_bars(4, 0, '000001', 0, 100)
        df = api.to_df(data)
        
        # 数据处理
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.sort_values('datetime')
        
        print(df.head())
        
        # 可视化
        plt.figure(figsize=(12, 6))
        plt.plot(df['datetime'], df['close'])
        plt.title('Stock Price Trend')
        plt.xlabel('Date')
        plt.ylabel('Close Price')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
```

### 场景3：获取不同周期的K线

```python
from pytdx.hq import TdxHq_API

# K线类别映射
KLINE_TYPE = {
    0: '5分钟K线',
    1: '15分钟K线',
    2: '30分钟K线',
    3: '1小时K线',
    4: '日K线',
    5: '周K线',
    6: '月K线',
    7: '1分钟K线',
    9: '日K线',
    10: '季K线',
    11: '年K线',
}

with TdxHq_API() as api:
    if api.connect('119.147.212.81', 7709):
        # 获取不同周期K线
        for category, name in [(4, '日K'), (5, '周K'), (6, '月K')]:
            data = api.get_security_bars(category, 0, '000001', 0, 50)
            df = api.to_df(data)
            print(f"\n{name}线数据：")
            print(df.tail())
```

### 场景4：获取指数数据

```python
from pytdx.hq import TdxHq_API

with TdxHq_API() as api:
    if api.connect('119.147.212.81', 7709):
        # 获取上证指数日K线
        # 指数代码：000001（上证）、399001（深成指）、399006（创业板指）
        data = api.get_index_bars(4, 1, '000001', 0, 100)
        df = api.to_df(data)
        print("上证指数：")
        print(df.tail())
        
        # 获取深成指
        data = api.get_index_bars(4, 0, '399001', 0, 100)
        df = api.to_df(data)
        print("\n深成指：")
        print(df.tail())
```

### 场景5：获取分时数据

```python
from pytdx.hq import TdxHq_API

with TdxHq_API() as api:
    if api.connect('119.147.212.81', 7709):
        # 获取当日分时数据
        data = api.get_minute_time_data(0, '000001')
        df = api.to_df(data)
        print("今日分时数据：")
        print(df.head(20))
        
        # 获取历史分时数据（例如：2024年1月15日）
        data = api.get_history_minute_time_data(0, '000001', 20240115)
        df = api.to_df(data)
        print("\n历史分时数据：")
        print(df.head(20))
```

### 场景6：获取成交明细

```python
from pytdx.hq import TdxHq_API

with TdxHq_API() as api:
    if api.connect('119.147.212.81', 7709):
        # 获取当日成交明细（最近1800条）
        data = api.get_transaction_data(0, '000001', 0, 1800)
        df = api.to_df(data)
        
        # 分析买卖盘力量
        buy_vol = df[df['buyorsell'] == 0]['vol'].sum()
        sell_vol = df[df['buyorsell'] == 1]['vol'].sum()
        
        print(f"买盘成交量: {buy_vol}手")
        print(f"卖盘成交量: {sell_vol}手")
        print(f"买卖比: {buy_vol/sell_vol:.2f}")
        
        print("\n成交明细：")
        print(df.head(20))
```

### 场景7：获取股票列表

```python
from pytdx.hq import TdxHq_API

with TdxHq_API() as api:
    if api.connect('119.147.212.81', 7709):
        # 获取深圳市场股票数量
        count = api.get_security_count(0)
        print(f"深圳市场股票数量: {count}")
        
        # 获取股票列表（每次最多1000条）
        data = api.get_security_list(0, 0)
        df = api.to_df(data)
        print("\n股票列表（前100条）：")
        print(df.head())
        
        # 过滤条件示例
        # 获取价格大于10元的股票
        stocks = []
        for i in range(0, count, 1000):
            data = api.get_security_list(0, i)
            df = api.to_df(data)
            stocks.append(df)
        
        all_stocks = pd.concat(stocks, ignore_index=True)
        print(f"\n总计股票数: {len(all_stocks)}")
```

### 场景8：获取财务数据

```python
from pytdx.hq import TdxHq_API

with TdxHq_API() as api:
    if api.connect('119.147.212.81', 7709):
        # 获取财务信息
        data = api.get_finance_info(0, '000001')
        print("财务数据：")
        for key, value in data.items():
            print(f"{key}: {value}")
```

### 场景9：获取除权除息信息

```python
from pytdx.hq import TdxHq_API

with TdxHq_API() as api:
    if api.connect('119.147.212.81', 7709):
        # 获取除权除息信息
        data = api.get_xdxr_info(0, '000001')
        df = api.to_df(data)
        
        print("除权除息历史：")
        print(df)
        
        # 计算复权因子
        # 例如：2023年每10股派发现金红利2.5元
        # 复权因子 = 1 - 派息金额/10/收盘价
```

### 场景10：获取公司信息

```python
from pytdx.hq import TdxHq_API

with TdxHq_API() as api:
    if api.connect('119.147.212.81', 7709):
        # 获取公司信息分类
        categories = api.get_company_info_category(0, '000001')
        print("公司信息分类：")
        for cat in categories:
            print(f"文件名: {cat['filename']}, 长度: {cat['length']}")
        
        # 获取具体内容（例如：公司简介）
        if categories:
            cat = categories[0]
            content = api.get_company_info_content(
                0, '000001', 
                cat['filename'], 
                cat['start'], 
                cat['length']
            )
            print(f"\n内容：\n{content}")
```

### 场景11：扩展市场（期货）数据

```python
from pytdx.exhq import TdxExHq_API

with TdxExHq_API() as api:
    if api.connect('61.152.107.171', 7727):
        # 获取市场列表
        markets = api.get_markets()
        print("支持的市场：")
        for m in markets:
            print(f"市场代码: {m['market']}, 名称: {m['name']}")
        
        # 获取期货合约信息
        # 例如：沪深300股指期货IF主力合约
        data = api.get_instrument_quote(1, 'IF0')  # 市场代码需根据实际情况
        df = api.to_df(data)
        print("\n期货行情：")
        print(df)
        
        # 获取期货K线
        data = api.get_instrument_bars(4, 1, 'IF0', 0, 100)
        df = api.to_df(data)
        print("\n期货K线：")
        print(df.tail())
```

---

## 最佳实践

### 1. 使用with语句管理连接

```python
# ✅ 推荐：自动管理连接
with TdxHq_API() as api:
    if api.connect('119.147.212.81', 7709):
        # 执行操作
        pass

# ❌ 不推荐：手动管理容易遗漏
api = TdxHq_API()
api.connect('119.147.212.81', 7709)
# 可能忘记disconnect
```

### 2. 批量查询提高效率

```python
# ✅ 推荐：批量查询
stocks = [(0, '000001'), (0, '000002'), (1, '600000')]
data = api.get_security_quotes(stocks)

# ❌ 不推荐：逐个查询
for market, code in stocks:
    data = api.get_security_quotes([(market, code)])
```

### 3. 异常处理

```python
from pytdx.hq import TdxHq_API
import time

def safe_query(api, func, *args, max_retries=3, **kwargs):
    """安全的查询函数，带重试机制"""
    for i in range(max_retries):
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            print(f"查询失败（第{i+1}次）: {e}")
            if i < max_retries - 1:
                time.sleep(1)
            else:
                raise

with TdxHq_API() as api:
    if api.connect('119.147.212.81', 7709):
        data = safe_query(api, api.get_security_bars, 4, 0, '000001', 0, 100)
```

### 4. 数据转换为DataFrame

```python
# pytdx提供了to_df方法，方便数据处理
data = api.get_security_bars(4, 0, '000001', 0, 100)
df = api.to_df(data)

# 转换时间格式
df['datetime'] = pd.to_datetime(df['datetime'])

# 计算技术指标
df['ma5'] = df['close'].rolling(5).mean()
df['ma10'] = df['close'].rolling(10).mean()
df['ma20'] = df['close'].rolling(20).mean()
```

### 5. 分页获取大量数据

```python
def get_all_klines(api, market, code, category, total_count):
    """分页获取K线数据"""
    all_data = []
    page_size = 800  # 单次最大获取数量
    
    for start in range(0, total_count, page_size):
        count = min(page_size, total_count - start)
        data = api.get_security_bars(category, market, code, start, count)
        all_data.extend(data)
    
    return all_data

with TdxHq_API() as api:
    if api.connect('119.147.212.81', 7709):
        # 获取最近5000根K线
        data = get_all_klines(api, 0, '000001', 4, 5000)
        df = api.to_df(data)
        print(f"获取到{len(df)}根K线")
```

### 6. 保持连接活跃

```python
import time
from pytdx.hq import TdxHq_API

with TdxHq_API() as api:
    if api.connect('119.147.212.81', 7709):
        # 长时间操作时定期发送心跳
        for i in range(10):
            data = api.get_security_quotes([(0, '000001')])
            # 处理数据...
            time.sleep(30)
            api.do_heartbeat()  # 保持连接
```

---

## 常见问题

### Q1: 连接超时怎么办？

**A:** 尝试以下方法：
1. 更换服务器地址
2. 增加超时时间：`api.connect(ip, port, time_out=10)`
3. 检查网络连接和防火墙设置

```python
servers = [
    ('119.147.212.81', 7709),
    ('218.75.126.9', 7709),
    ('115.238.56.198', 7709),
]

for ip, port in servers:
    try:
        api = TdxHq_API()
        if api.connect(ip, port, time_out=10):
            print(f"成功连接到 {ip}:{port}")
            break
    except:
        continue
```

### Q2: 返回的数据为空？

**A:** 检查以下项：
1. 市场代码是否正确（0:深圳, 1:上海）
2. 股票代码是否正确（格式：6位数字字符串）
3. K线类别参数是否有效
4. start和count参数是否合理

```python
# 验证股票代码
data = api.get_security_quotes([(0, '000001')])
if not data:
    print("未获取到数据，请检查参数")
```

### Q3: 如何判断买卖盘？

**A:** 成交明细中的buyorsell字段：
- 0: 买盘（主动性买入）
- 1: 卖盘（主动性卖出）

```python
data = api.get_transaction_data(0, '000001', 0, 100)
df = api.to_df(data)

buy_count = len(df[df['buyorsell'] == 0])
sell_count = len(df[df['buyorsell'] == 1])

print(f"买盘: {buy_count}笔, 卖盘: {sell_count}笔")
```

### Q4: 如何计算复权价格？

**A:** 使用除权除息信息进行计算：

```python
def calculate_adjusted_price(close_price, xdxr_info):
    """
    计算后复权价格
    close_price: 收盘价
    xdxr_info: 除权除息信息
    """
    adjusted_price = close_price
    
    for info in xdxr_info:
        # 送股、转增
        if info['songgu'] > 0 or info['zhuanzeng'] > 0:
            ratio = 1 + (info['songgu'] + info['zhuanzeng']) / 10
            adjusted_price = adjusted_price / ratio
        
        # 配股
        if info['peigu'] > 0:
            # 需要更复杂的计算
            pass
        
        # 分红
        if info['fenghong'] > 0:
            adjusted_price = adjusted_price + info['fenghong'] / 10
    
    return adjusted_price
```

### Q5: 如何获取所有A股列表？

**A:** 分页获取：

```python
def get_all_stocks(api, market):
    """获取市场所有股票"""
    count = api.get_security_count(market)
    all_stocks = []
    
    for start in range(0, count, 1000):
        data = api.get_security_list(market, start)
        all_stocks.extend(data)
    
    return all_stocks

with TdxHq_API() as api:
    if api.connect('119.147.212.81', 7709):
        # 获取沪深全部股票
        sz_stocks = get_all_stocks(api, 0)  # 深圳
        sh_stocks = get_all_stocks(api, 1)  # 上海
        
        print(f"深圳股票: {len(sz_stocks)}只")
        print(f"上海股票: {len(sh_stocks)}只")
```

### Q6: 数据时间戳如何处理？

**A:** 使用pandas进行时间处理：

```python
import pandas as pd

data = api.get_security_bars(4, 0, '000001', 0, 100)
df = api.to_df(data)

# 转换时间格式
df['datetime'] = pd.to_datetime(df['datetime'])

# 提取日期和时间
df['date'] = df['datetime'].dt.date
df['time'] = df['datetime'].dt.time

# 设置时间索引
df = df.set_index('datetime')

print(df.head())
```

### Q7: 如何监控实时行情？

**A:** 定时轮询：

```python
import time
from datetime import datetime

def monitor_stock(api, market, code, interval=3):
    """监控股票实时行情"""
    while True:
        now = datetime.now()
        # 只在交易时间监控（9:30-11:30, 13:00-15:00）
        if (9 <= now.hour < 12) or (13 <= now.hour < 15):
            data = api.get_security_quotes([(market, code)])
            if data:
                quote = data[0]
                print(f"{now.strftime('%H:%M:%S')} - {quote['code']}: "
                      f"价格{quote['price']:.2f} "
                      f"涨幅{((quote['price']/quote['last_close']-1)*100):.2f}%")
        
        time.sleep(interval)

with TdxHq_API() as api:
    if api.connect('119.147.212.81', 7709):
        monitor_stock(api, 0, '000001')
```

### Q8: 如何保存数据到文件？

**A:** 使用pandas的保存功能：

```python
import pandas as pd

# 获取数据
data = api.get_security_bars(4, 0, '000001', 0, 100)
df = api.to_df(data)

# 保存为CSV
df.to_csv('000001_daily.csv', index=False)

# 保存为Excel
df.to_excel('000001_daily.xlsx', index=False)

# 保存为HDF5（适合大数据量）
df.to_hdf('stock_data.h5', key='000001', mode='a')

# 读取数据
df_csv = pd.read_csv('000001_daily.csv')
df_excel = pd.read_excel('000001_daily.xlsx')
df_hdf = pd.read_hdf('stock_data.h5', key='000001')
```
