---
name: tdxuse
description: 基于通达信TQ策略接口的金融数据分析与量化工具，提供行情获取、财务数据、板块管理、公式计算、消息通知、回测数据发送等全功能支持。当用户需要获取股票/期货/ETF/可转债等金融数据、调用通达信公式、管理自定义板块或进行量化相关操作时触发。
---

# Tdxuse — 通达信TQ量化工具集

## 概述

本技能基于 **通达信金融终端TQ版** 的 TQ 策略接口，提供完整的金融数据获取与量化分析能力。涵盖 A股、港股、美股、期货、期权、可转债、ETF 等多市场数据，并支持通达信公式调用、自定义板块管理、实时行情订阅、消息推送、文件传输及回测数据交互等功能。

## 触发条件

当用户请求以下类型操作时自动触发：

- 获取股票/期货/期权/可转债/ETF 等金融数据
- 查询 K线行情、快照、财务指标、板块信息
- 使用通达信公式计算技术指标或选股
- 管理（创建/删除/重命名）自定义板块
- 订阅/取消订阅实时行情
- 下载历史数据文件、刷新缓存
- 向通达信客户端发送消息/警告/文件/回测数据
- 任何与通达信量化交易相关的请求

---

## 一、行情数据

### 获取K线行情数据

```
/get_market_data --stock_list 688318.SH --period 1d --count 5
```

**参数说明：**

| 参数 | 是否必填 | 说明 |
|---|---|---|
| `--stock_list` | 是 | 股票代码列表，如 `600000.SH 000001.SZ` |
| `--period` | 否 | K线周期，默认 `1d`（见下方枚举值） |
| `--count` | 否 | 获取数量，默认 `1` |
| `--dividend_type` | 否 | 复权类型：`none`/`front`/`back`，默认 `none` |

### 获取快照数据

```
/get_market_snapshot --stock_code 688318.SH
```

### 获取证券基本信息

```
/get_stock_info --stock_code 688318.SH --field_list Name Unit
```

### 获取股票更多信息

```
/get_more_info --stock_code 688318.SH
```

### 获取交易日列表

```
/get_trading_dates --market SH --count 10
```

| 参数 | 说明 |
|---|---|
| `--market` | 市场：`SH`(沪)/`SZ`(深) 等 |

---

## 二、财务数据

### 获取专业财务数据

```
/get_financial_data --stock_list 688318.SH --field_list FN193 FN194
```

### 获取指定日期专业财务数据

```
/get_financial_data_by_date --stock_list 688318.SH --field_list FN193 --year 2025
```

### 获取股票交易数据（GPJY）

```
/get_gpjy_value --stock_list 688318.SH --field_list GP1 GP2
```

### 获取指定日期股票交易数据

```
/get_gpjy_value_by_date --stock_list 688318.SH --field_list GP1 --year 2025
```

### 获取单个财务数据

```
/get_gp_one_data --stock_list 688318.SH --field_list GO1 GO2
```

---

## 三、板块数据

### 获取系统分类成份股

```
/get_stock_list --market 16
```

### 获取A股板块代码列表

```
/get_sector_list
```

### 获取板块成份股

```
/get_stock_list_in_sector --block_code 880081.SH
```

### 获取板块交易数据（BKJY）

```
/get_bkjy_value --stock_list 880660.SH --field_list BK5 BK6
```

### 获取指定日期板块交易数据

```
/get_bkjy_value_by_date --stock_list 880660.SH --field_list BK9 --year 2025
```

---

## 四、市场数据

### 获取市场交易数据（SCJY）

```
/get_scjy_value --field_list SC1 SC2
```

### 获取指定日期市场交易数据

```
/get_scjy_value_by_date --field_list SC6 SC7 --year 2025
```

---

## 五、新股与分红

### 获取新股申购信息

```
/get_ipo_info --ipo_type 2 --ipo_date 1
```

| 参数 | 枚举值 | 说明 |
|---|---|---|
| `--ipo_type` | `0` / `1` / `2` | 新股/新发债/两者 |
| `--ipo_date` | `0` / `1` | 仅今天/今天及以后 |

### 获取分红配送数据

```
/get_divid_factors --stock_code 688318.SH
```

### 获取股本数据

```
/get_gb_info --stock_code 688318.SH --date_list 20250101 20250601 --count 2
```

---

## 六、自定义板块管理

> 以下命令用于在通达信客户端中管理用户自建板块。

```
/get_user_sector                    # 获取自定义板块列表
/create_sector --block_code TEST --block_name 测试板块   # 创建自定义板块
/delete_sector --block_code TEST    # 删除自定义板块
/rename_sector --block_code TEST --block_name 新名称     # 重命名自定义板块
/send_user_block --block_code TEST --stocks 600000.SH 600004.SH  # 添加成份股
/clear_sector --block_code TEST     # 清空板块所有成份股
```

---

## 七、ETF 与可转债

### 获取跟踪指数的 ETF 信息

```
/get_trackzs_etf_info --zs_code 950162.CSI
```

### 获取可转债基础信息

```
/get_cb_info --stock_code 123039.SZ
```

---

## 八、行情订阅

> 支持对指定股票代码的实时行情进行订阅和取消。

```
/subscribe_hq --stock_list 688318.SH        # 订阅实时行情
/unsubscribe_hq --stock_list 688318.SH       # 取消订阅
/get_subscribe_hq_stock_list                 # 查看当前订阅列表
```

---

## 九、数据刷新与下载

### 刷新行情缓存

```
/refresh_cache --market AG --force
```

参数 `--force`：强制刷新。

### 刷新历史 K 线缓存

```
/refresh_kline --stock_list 688318.SH --period 1d
```

### 下载特定数据文件

```
/download_file --stock_code 688318.SH --down_time 20241231 --down_type 1
```

---

## 十、通达信公式工具

> 通过脚本调用通达信内置公式引擎，执行技术指标计算和选股逻辑。详见 `references/Call TongdaXin formula/` 目录下的详细文档。

```
/formula_tools.py    # 公式计算与选股的核心脚本
```

**主要能力：**
- 设置公式数据源 (`formula_set_data_info`)
- 计算技术指标值 (`formula_get_res`)
- 批量选股处理 (`formula_process_mul_xg`)
- 更多示例见 `references/Scenario-based examples/`

---

## 十一、消息与文件发送

> 可通过通达信客户端向用户发送各类通知和数据。

```
# 发送文本消息到通达信
/send_message --content "操作完成"

# 发送警告信息
/send_warn --content "风险预警"

# 在通达信输出窗口打印内容
/print_to_tdx --content "调试信息"

# 发送文件到通达信
/send_file --file_path C:/data/result.xlsx
```

---

## 十二、回测数据交互

### 发送回测数据

```
/send_bt_data
```

将回测结果数据发送至通达信客户端进行展示和分析。具体使用方式参考脚本说明。

---

## 十三、环境配置辅助

### 自动设置 DLL 路径

```
/setup_dll_path
```

自动配置通达信 TPythClient.dll 相关路径依赖。

---

## 前置条件

使用本技能前需要满足以下条件：

### 1. 安装 Python 依赖包

```bash
pip install numpy pandas
```

### 2. 安装通达信金融终端 TQ 版

- 需要安装 **通达信金融终端 TQ 版** 并确保其正常运行
- 本技能依赖 TQ 策略接口与通达信客户端进行数据交互
- 确保 TQ 策略功能已启用

### 3. 配置 PYTHONPATH

运行脚本前需要设置 PYTHONPATH：

```bash
# Windows (PowerShell)
$env:PYTHONPATH = "C:\path\to\skill\tdxuse"

# 运行脚本示例
python scripts/get_market_data.py --stock_list 688318.SH --period 1d

# 或使用 -m 方式运行
cd C:\path\to\skill\tdxuse
python -m scripts.get_market_data --stock_list 688318.SH --period 1d
```

如果脚本不在通达信默认目录下运行，需在 import 前添加路径：

```python
import sys
sys.path.append('通达信安装目录/PYPlugins/user')
from tqcenter import tq
tq.initialize(__file__)
```

---

## 枚举值速查

### period（K线周期）

| 值 | 说明 |
|---|---|
| `1m` | 1分钟 |
| `5m` | 5分钟 |
| `15m` | 15分钟 |
| `30m` | 30分钟 |
| `1h` | 60分钟（1小时） |
| `1d` | 1天 |
| `1w` | 1周 |
| `1mon` | 1月 |
| `1q` | 1季 |
| `1y` | 1年 |
| `tick` | 分笔 |

### dividend_type（复权类型）

| 值 | 说明 |
|---|---|
| `none` | 不复权 |
| `front` | 前复权 |
| `back` | 后复权 |

### market（市场类型）

| 值 | 说明 |
|---|---|
| `AG` | A股 |
| `HK` | 港股 |
| `US` | 美股 |
| `QH` | 国内期货 |
| `QQ` | 股票期权 |
| `NQ` | 新三板 |
| `ZZ` | 中证和国证指数 |
| `ZS` | 沪深京指数 |

### 市场代码（扩展）

| 后缀 | 数值 | 说明 |
|---|---|---|
| `.SZ` | 0 | 深圳交易所 |
| `.SH` | 1 | 上海交易所 |
| `.BJ` | 2 | 北京交易所 |
| `.NQ` | 44 | 新三板 |
| `.HK` | 31 | 港股个股 |
| `.US` | 74 | 美国股票 |
| `.CSI` | 62 | 中证指数 |
| `.CNI` | 102 | 国证指数 |
| `.HG` | 38 | 国内宏观指标 |
| `.CFF` | 47 | 中金期货 |
| `.CZC` | 28 | 郑州期货 |
| `.DCE` | 29 | 大连期货 |
| `.SHF` | 30 | 上海期货 |

### ipo_type（新股类型）

| 值 | 说明 |
|---|---|
| `0` | 新股申购信息 |
| `1` | 新发债信息 |
| `2` | 新股和新发债信息 |

### ipo_date（新股日期范围）

| 值 | 说明 |
|---|---|
| `0` | 只获取今天的信息 |
| `1` | 获取今天及以后的信息 |

---

## 常见问题 (Q&A)

> 详细问答文档请参见 `references/QA.md`，以下为摘要：

| 问题 | 解决方案 |
|---|---|
| 脚本可以不在 PYPlugins\user 目录下运行吗？ | 可以，在 import tqcenter 前 sys.path.append 通达信安装路径 |
| 报错找不到 TPythClient.dll？ | 通常是杀毒软件误删了同目录下的 tdxrpcx64.dll，需恢复并加白名单 |
| 外部运行的 py 文件报"已存在运行"？ | 在 TQ 策略管理器中找到该 OutSide 策略并删除 |
| 菜单一直显示"正在开启TQ策略.."？ | 检查是否有防火墙/权限弹窗，点击允许访问 |
| 获取的数据前面是 None？ | count 数量需覆盖公式计算所需的最大回溯周期数 |
| 选股结果比客户端少？ | 确保 count 参数足够大，满足公式计算的数据需求 |

---

## 技能资源结构

```
tdxuse/
├── scripts/          # 可执行的 Python 脚本（41个），覆盖上述全部功能
├── lib/              # 核心库模块（tqcenter 封装、配置管理）
├── references/       # 参考文档（按主题分类）
│   ├── Call TongdaXin formula/   # 通达信公式调用指南
│   ├── Customized sectors for selected stocks/  # 自定义板块操作详解
│   ├── ETF convertible bond futures data/       # ETF/可转债/期货数据说明
│   ├── Financial data/              # 财务数据字段手册
│   ├── General functions/           # 通用功能 API 文档
│   ├── Market information/          # 市场信息相关
│   ├── Scenario-based examples/     # 场景化使用示例
│   ├── Sector constituent stocks/   # 板块成份股接口
│   ├── Examples of articles on WeChat official accounts/  # 公众号文章案例
│   ├── Enum.md                      # 完整枚举值定义
│   └── QA.md                        # 常见问题解答
└── assets/            # 静态资源文件
```
