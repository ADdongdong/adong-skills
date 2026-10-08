---
name: pytdx-api
description: 提供通达信pytdx库的完整API接口参考与使用指导，当用户需要获取A股行情、期货行情、K线数据、分时数据、成交明细、财务数据或板块信息时使用
dependency:
  python:
    - pytdx==1.72
---

# 通达信 pytdx API 参考 Skill

## 任务目标
- 本 Skill 用于：提供通达信pytdx库的完整API接口参考和使用指导
- 能力包含：标准市场行情查询、扩展市场行情查询、K线数据获取、分时数据获取、财务数据查询、板块信息获取
- 触发条件：用户需要获取股票行情数据、期货期权数据、技术分析指标、财务数据或板块分类信息

## 前置准备
- 依赖说明：pytdx库及版本要求
  ```
  pytdx==1.72
  ```

## 快速使用（推荐）

### 导入方式
```python
import sys
sys.path.insert(0, r'C:\Users\76660\.openclaw\workspace\skills')

from pytdx_api.scripts import (
    ConnectionMode,
    get_index_kline_data,
    get_kline_data,
    get_realtime_quote,
    get_batch_quotes,
)
```

### 获取K线数据
```python
# 获取上证指数日K线（默认120根）
series = get_index_kline_data('000001', period='daily')
print(f'K线数量: {series.count}')
print(f'最新收盘: {series.get_latest().close:.2f}')

# 获取个股K线
series = get_kline_data('600726', period='daily', count=60)
```

### 获取实时行情
```python
# 单只股票
quote = get_realtime_quote('600726')
print(f'价格: {quote.price}, 涨跌幅: {quote.change_percent}%')

# 批量获取
quotes = get_batch_quotes(['600726', '000001', '600519'])
```

### 连接模式
```python
ConnectionMode.SHORT     # 短连接（用完即关，适合偶尔查询）
ConnectionMode.LONG      # 长连接（保持心跳，适合监控）
ConnectionMode.POOL      # 连接池（复用连接）
ConnectionMode.ADAPTIVE  # 自适应（根据频率自动选择）
```

## 核心概念

### 两大API类型
1. **标准市场API (TdxHq_API)**：用于A股、B股、指数等标准市场数据
2. **扩展市场API (TdxExHq_API)**：用于期货、期权、港股、美股等扩展市场数据

### 市场代码
- 0: 深圳证券交易所
- 1: 上海证券交易所

### K线类别
- 0: 5分钟K线
- 1: 15分钟K线
- 2: 30分钟K线
- 3: 1小时K线
- 4: 日K线
- 5: 周K线
- 6: 月K线
- 7: 1分钟K线
- 8: 1分钟K线（含成交量）
- 9: 日K线（含成交量）
- 10: 季K线
- 11: 年K线

## 服务器选择机制

### 自动选择策略
本 Skill 实现了智能服务器选择，无需手动指定服务器地址：

1. **服务器来源**
   - 从 pytdx 内置配置获取标准服务器列表
   - 优先使用测试验证的最优服务器

2. **评分算法**
   ```
   评分 = 权重 × 成功率 × 响应时间惩罚 × 新鲜度奖励
   ```
   - 权重：预设优先级（最优服务器权重=1.0）
   - 成功率：历史连接成功/失败比例
   - 响应时间惩罚：响应越快分数越高
   - 新鲜度：最近使用过的服务器有奖励

3. **故障恢复**
   - 连续失败超过3次的服务器评分归零
   - 自动切换到次优服务器
   - 支持自动重试（默认2次）

### 预设最优服务器
| 服务器地址 | 端口 | 权重 | 说明 |
|-----------|------|------|------|
| 115.238.56.198 | 7709 | 1.0 | 测试最优，优先使用 |
| 119.147.212.81 | 7709 | 0.9 | 备选服务器 |
| 218.75.126.9 | 7709 | 0.8 | 备选服务器 |

### 手动指定服务器
如需指定特定服务器：
```python
from pytdx_api.scripts import get_kline_data

# 指定服务器
series = get_kline_data('600726', server_ip='115.238.56.198', server_port=7709)
```

## 操作步骤

### 标准流程
1. **连接服务器**
   - 智能体根据需求选择合适的通达信服务器地址
   - 使用`connect()`方法建立连接
   - 建议使用with语句自动管理连接生命周期

2. **查询数据**
   - 根据需求查阅 [references/api-reference.md](references/api-reference.md) 选择合适的API方法
   - 参考 [references/usage-examples.md](references/usage-examples.md) 了解具体调用方式
   - 注意市场代码、股票代码等参数的正确性

3. **数据处理**
   - 使用`to_df()`方法将返回数据转换为DataFrame格式
   - 进行数据分析和可视化

### 常用场景
- **获取实时行情**：使用`get_realtime_quote()`或`get_batch_quotes()`
- **获取K线数据**：使用`get_kline_data()`或`get_index_kline_data()`
- **获取分时数据**：使用`get_minute_time_data()`方法
- **查询股票列表**：使用`get_security_list()`方法
- **获取财务数据**：使用`get_finance_info()`方法
- **查询板块信息**：使用`get_block_info()`方法

## 资源索引
- 完整API参考：见 [references/api-reference.md](references/api-reference.md)（所有接口的详细说明和参数定义）
- 使用示例：见 [references/usage-examples.md](references/usage-examples.md)（典型场景的代码示例和最佳实践）
- 封装脚本：见 [scripts/](scripts/) 目录（连接池、K线、实时行情等封装）

## 注意事项
- pytdx通过通达信协议获取数据，需要确保网络连接稳定
- 建议使用with语句管理连接，避免资源泄漏
- 查询历史数据时注意start参数的使用（从0开始计数）
- 扩展市场API需要使用专门的扩展市场服务器地址
- 返回的数据格式可能需要转换为DataFrame以便于分析

## 实现方式说明
- **API调用**：由智能体直接使用pytdx库编写代码实现
- **数据处理**：由智能体根据需求进行数据分析和可视化
- **封装脚本**：提供了连接池、K线、实时行情等便捷封装
