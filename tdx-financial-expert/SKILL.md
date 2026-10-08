---
name: tdx-financial-expert
description: 提供A股/指数/期货的实时行情与历史K线数据获取，支持财务数据解析；当用户需要查询股票行情、获取历史K线、分析财务数据或读取本地通达信数据时使用
dependency:
  python:
    - mootdx[all]>=1.2.0
    - pandas>=1.3.0
    - retry>=0.9.2
---

# 通达信金融数据专家

## 任务目标
本 Skill 用于通过通达信数据接口获取金融市场的实时行情、历史K线数据及财务报表信息，支持A股、指数、期货等市场。

## 能力包含
- 实时行情快照：获取股票、指数、期货的实时价格、成交量等数据
- 历史K线数据：支持多种时间周期（日线、分钟线）的历史数据查询
- 财务数据解析：资产负债表、利润表、现金流量表数据获取
- 本地数据读取：直接读取通达信客户端本地存储的数据

## 触发条件
- 用户请求查询股票或指数的实时行情（如"查看600519的当前价格"）
- 用户请求获取历史K线数据（如"获取贵州茅台最近30天的日线"）
- 用户需要分析财务数据（如"查看600519的资产负债表"）
- 用户需要读取本地通达信数据（如"读取本地日线数据"）

## 前置准备

### 依赖安装
确保 Python 版本为 3.8 或以上，建议使用虚拟环境：

```bash
# 直接PIP安装
pip install mootdx[all]>=1.2.0 pandas>=1.3.0 retry>=0.9.2
```

### 服务器配置优化
技能初始化时会自动执行 `mootdx bestip -v` 测试并选择最快的行情服务器，将最快IP写入配置文件以提升连接稳定性。若自动优选失败，将回退至默认配置。

## 操作步骤

### 1. 获取实时行情快照
调用 `scripts/quotes_client.py` 的 `get_quotes` 方法：

```python
from tdx_financial_expert.scripts.quotes_client import get_quotes

result = get_quotes(symbol="600519")  # 贵州茅台
```

- 智能体解析用户自然语言中的股票代码
- 调用脚本获取实时数据
- 提取关键字段：代码、名称、开盘价、收盘价、最高价、最低价、成交量
- 返回 Markdown 表格格式，附带摘要信息

### 2. 获取历史K线数据
调用 `scripts/quotes_client.py` 的 `get_kline` 方法：

```python
from tdx_financial_expert.scripts.quotes_client import get_kline

result = get_kline(symbol="600519", frequency=9, offset=0, count=10)
```

- frequency 参数映射见 [references/frequency-mapping.md](references/frequency-mapping.md)
- 支持分页查询：通过 offset 和 count 控制数据范围
- 返回带时间索引的 Markdown 表格

### 3. 获取指数和分钟数据
调用相应方法获取指数数据或分钟线数据：

```python
# 获取指数数据
from tdx_financial_expert.scripts.quotes_client import get_index
index_data = get_index(symbol="000001")  # 上证指数

# 获取分钟数据
from tdx_financial_expert.scripts.quotes_client import get_minute
minute_data = get_minute(symbol="600519")
```

### 4. 解析财务数据
调用 `scripts/financial_parser.py` 获取财务报表：

```python
from tdx_financial_expert.scripts.financial_parser import (
    get_balance_sheet,
    get_profit_statement,
    get_cash_flow
)

# 资产负债表
balance_sheet = get_balance_sheet(symbol="600519")

# 利润表
profit_statement = get_profit_statement(symbol="600519")

# 现金流量表
cash_flow = get_cash_flow(symbol="600519")
```

### 5. 读取本地通达信数据
调用 `scripts/offline_reader.py` 读取本地数据：

```python
from tdx_financial_expert.scripts.offline_reader import (
    get_daily,
    get_minute as get_offline_minute
)

# 读取日线数据（需提供正确的通达信安装路径）
daily_data = get_daily(
    tdx_path="D:/new_tdx",
    symbol="600519"
)

# 读取分钟线数据
minute_data = get_offline_minute(
    tdx_path="D:/new_tdx",
    symbol="600519",
    suffix="1min"
)
```

## 资源索引

### 必要脚本
- [scripts/quotes_client.py](scripts/quotes_client.py)：行情客户端封装，提供实时行情、K线数据、指数数据、分钟数据获取功能
- [scripts/offline_reader.py](scripts/offline_reader.py)：本地数据读取器，支持从通达信安装目录读取日线和分钟线数据
- [scripts/financial_parser.py](scripts/financial_parser.py)：财务数据解析器，提供资产负债表、利润表、现金流量表数据获取

### 领域参考
- [references/frequency-mapping.md](references/frequency-mapping.md)：频率参数映射表，定义K线数据的frequency参数取值
- [references/error-handling.md](references/error-handling.md)：错误处理指南，常见错误及解决方案

### 输出资产
- [assets/config-template.txt](assets/config-template.txt)：配置文件模板，用于参考服务器IP配置格式

## 注意事项

### 异常处理
- 所有网络请求均包含 `try...except` 异常捕获，并返回友好的错误提示
- 自动重试机制：单次请求失败后最多重试3次，采用指数退避策略
- 出现连接超时时，建议用户手动运行 `mootdx bestip -v` 更新服务器列表

### 资源管理
- 所有脚本在使用完 Quotes 客户端后会自动调用 `client.close()` 释放连接
- 确保每次请求后资源被正确释放

### 数据质量
- 所有返回的数据都转换为 Pandas DataFrame 格式后，再转换为 Markdown 表格或 JSON 输出
- 时间列自动设置为索引，方便后续量化分析
- 数据格式验证确保后续处理的稳定性

### 服务器列表更新
技能初始化时会自动执行服务器优选；若仍遇到连接失败，用户可手动从通达信官方客户端的 `connect.cfg` 文件中提取最新服务器IP，更新到 mootdx 配置文件中。

## 使用示例

### 示例1：查询实时行情
**用户请求**："查看贵州茅台的当前行情"
**执行方式**：智能体解析股票代码 → 调用 `get_quotes("600519")` → 返回 Markdown 表格

### 示例2：获取历史K线
**用户请求**："获取600519最近20天的日线数据"
**执行方式**：智能体解析参数 → 调用 `get_kline("600519", frequency=9, offset=0, count=20)` → 返回带摘要的数据

### 示例3：分析财务数据
**用户请求**："查看600519的最新资产负债表"
**执行方式**：智能体识别需求 → 调用 `get_balance_sheet("600519")` → 解析并展示关键指标
