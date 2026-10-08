#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pytdx 工具函数模块
参数验证、错误处理、常量定义等
"""

import re
import time
from typing import Optional, Tuple, Union, Dict, Any, List
from datetime import datetime, timedelta
from enum import IntEnum


# ============================================================================
# 常量定义
# ============================================================================

class Market(IntEnum):
    """市场代码"""
    SZ = 0      # 深圳证券交易所
    SH = 1      # 上海证券交易所
    
    @classmethod
    def from_code(cls, stock_code: str) -> Optional['Market']:
        """根据股票代码推断市场"""
        if not stock_code or not isinstance(stock_code, str):
            return None
        
        code = stock_code.strip()
        
        # 检查是否为6位数字
        if len(code) != 6 or not code.isdigit():
            return None
        
        # 常见指数代码特殊处理
        common_indices = {
            # 上证指数系列
            '000001': cls.SH,  # 上证指数
            '000300': cls.SH,  # 沪深300
            '000016': cls.SH,  # 上证50
            '000010': cls.SH,  # 上证180
            '000009': cls.SH,  # 上证380
            
            # 深证指数系列
            '399001': cls.SZ,  # 深证成指
            '399006': cls.SZ,  # 创业板指
            '399005': cls.SZ,  # 中小板指
            '399008': cls.SZ,  # 中小300
            '399102': cls.SZ,  # 创业板综
            '399106': cls.SZ,  # 深证综指
            
            # 其他常见指数
            '000903': cls.SH,  # 中证100
            '000905': cls.SH,  # 中证500
            '000906': cls.SH,  # 中证800
            '000852': cls.SH,  # 中证1000
        }
        
        # 首先检查是否是已知指数
        if code in common_indices:
            return common_indices[code]
        
        # 股票代码判断
        # 深圳市场: 00xxxx（主板）, 30xxxx（创业板）, 200xxx（B股）, 300xxx（创业板，已迁移）
        if code.startswith(('00', '30', '200', '300')):
            return cls.SZ
        
        # 上海市场: 60xxxx（主板）, 900xxx（B股）, 688xxx（科创板）
        elif code.startswith(('60', '900', '688')):
            return cls.SH
        
        # 其他6位数字代码：按规则推断
        # 399xxx 一般是深圳指数
        elif code.startswith('399'):
            return cls.SZ
        
        # 000xxx 一般是上海指数
        elif code.startswith('000'):
            return cls.SH
        
        return None


class KLineCategory(IntEnum):
    """K线类别"""
    MIN5 = 0      # 5分钟K线
    MIN15 = 1     # 15分钟K线
    MIN30 = 2     # 30分钟K线
    HOUR1 = 3     # 1小时K线
    DAILY = 4     # 日K线
    WEEKLY = 5    # 周K线
    MONTHLY = 6   # 月K线
    MIN1 = 7      # 1分钟K线
    MIN1_VOL = 8  # 1分钟K线（含成交量）
    DAILY_VOL = 9 # 日K线（含成交量）
    QUARTERLY = 10 # 季K线
    YEARLY = 11    # 年K线
    
    @classmethod
    def from_string(cls, period: str) -> Optional['KLineCategory']:
        """从字符串转换为K线类别"""
        period_lower = period.lower().strip()
        
        mapping = {
            '1min': cls.MIN1,
            '5min': cls.MIN5,
            '15min': cls.MIN15,
            '30min': cls.MIN30,
            '60min': cls.HOUR1,
            '1h': cls.HOUR1,
            'daily': cls.DAILY,
            'day': cls.DAILY,
            'd': cls.DAILY,
            'weekly': cls.WEEKLY,
            'week': cls.WEEKLY,
            'w': cls.WEEKLY,
            'monthly': cls.MONTHLY,
            'month': cls.MONTHLY,
            'm': cls.MONTHLY,
            'quarterly': cls.QUARTERLY,
            'quarter': cls.QUARTERLY,
            'q': cls.QUARTERLY,
            'yearly': cls.YEARLY,
            'year': cls.YEARLY,
            'y': cls.YEARLY,
        }
        
        return mapping.get(period_lower)


class BlockType:
    """板块类型"""
    BLOCK_SZ = "block_zs.dat"      # 板块指数
    BLOCK_FG = "block_fg.dat"      # 风格板块
    BLOCK_GN = "block_gn.dat"      # 概念板块
    BLOCK_DEFAULT = "block.dat"    # 默认板块


# ============================================================================
# 参数验证函数
# ============================================================================

def validate_stock_code(stock_code: str) -> Tuple[bool, Optional[str]]:
    """
    验证股票代码格式
    
    Args:
        stock_code: 股票代码
        
    Returns:
        (是否有效, 错误信息)
    """
    if not stock_code:
        return False, "股票代码不能为空"
    
    if not isinstance(stock_code, str):
        return False, f"股票代码应为字符串，实际类型: {type(stock_code)}"
    
    code = stock_code.strip()
    
    # 检查长度
    if len(code) != 6:
        return False, f"股票代码应为6位数字，实际长度: {len(code)}"
    
    # 检查是否为数字
    if not code.isdigit():
        return False, f"股票代码应全为数字，实际: {code}"
    
    # 检查市场前缀
    market = Market.from_code(code)
    if market is None:
        return False, f"无法识别的股票代码: {code}"
    
    return True, None


def validate_market(market: Union[int, str, Market]) -> Optional[Market]:
    """
    验证并标准化市场代码
    
    Args:
        market: 市场代码
        
    Returns:
        标准化后的Market枚举，或None（无效）
    """
    if isinstance(market, Market):
        return market
    
    if isinstance(market, int):
        try:
            return Market(market)
        except ValueError:
            return None
    
    if isinstance(market, str):
        market_lower = market.lower().strip()
        if market_lower in ('0', 'sz', 'shenzhen', '深圳'):
            return Market.SZ
        elif market_lower in ('1', 'sh', 'shanghai', '上海'):
            return Market.SH
    
    return None


def validate_kline_category(category: Union[int, str, KLineCategory]) -> Optional[KLineCategory]:
    """
    验证并标准化K线类别
    
    Args:
        category: K线类别
        
    Returns:
        标准化后的KLineCategory枚举，或None（无效）
    """
    if isinstance(category, KLineCategory):
        return category
    
    if isinstance(category, int):
        try:
            return KLineCategory(category)
        except ValueError:
            return None
    
    if isinstance(category, str):
        return KLineCategory.from_string(category)
    
    return None


# ============================================================================
# 数据转换函数
# ============================================================================

def parse_market_code(stock_code: str) -> Tuple[Optional[Market], Optional[str]]:
    """
    解析股票代码，返回市场代码和标准化股票代码
    
    Args:
        stock_code: 股票代码
        
    Returns:
        (市场代码, 标准化股票代码)
    """
    is_valid, error = validate_stock_code(stock_code)
    if not is_valid:
        return None, None
    
    code = stock_code.strip()
    market = Market.from_code(code)
    return market, code


def format_stock_pair(stock_code: str) -> Optional[Tuple[int, str]]:
    """
    格式化股票代码为 (market, code) 元组
    
    Args:
        stock_code: 股票代码
        
    Returns:
        (market, code) 元组，或 None
    """
    market, code = parse_market_code(stock_code)
    if market is None or code is None:
        return None
    return (market.value, code)


def format_stock_pairs(stock_codes: List[str]) -> List[Tuple[int, str]]:
    """
    批量格式化股票代码
    
    Args:
        stock_codes: 股票代码列表
        
    Returns:
        [(market1, code1), (market2, code2), ...]
    """
    result = []
    for code in stock_codes:
        pair = format_stock_pair(code)
        if pair:
            result.append(pair)
    return result


def timestamp_to_datetime(timestamp: Union[int, float]) -> datetime:
    """
    时间戳转换为datetime
    
    Args:
        timestamp: 时间戳（秒）
        
    Returns:
        datetime对象
    """
    return datetime.fromtimestamp(timestamp)


def datetime_to_str(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    datetime转换为字符串
    
    Args:
        dt: datetime对象
        fmt: 格式字符串
        
    Returns:
        格式化后的字符串
    """
    return dt.strftime(fmt)


def date_to_int(date: Union[str, datetime]) -> int:
    """
    日期转换为整数格式 (YYYYMMDD)
    
    Args:
        date: 日期字符串或datetime
        
    Returns:
        YYYYMMDD格式整数
    """
    if isinstance(date, str):
        # 尝试解析各种格式
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d", "%Y.%m.%d"):
            try:
                dt = datetime.strptime(date, fmt)
                return int(dt.strftime("%Y%m%d"))
            except ValueError:
                continue
        raise ValueError(f"无法解析日期: {date}")
    elif isinstance(date, datetime):
        return int(date.strftime("%Y%m%d"))
    else:
        raise TypeError(f"不支持的日期类型: {type(date)}")


# ============================================================================
# 错误处理
# ============================================================================

class PyTdxError(Exception):
    """pytdx基础异常"""
    pass


class ConnectionError(PyTdxError):
    """连接异常"""
    pass


class ParameterError(PyTdxError):
    """参数错误"""
    pass


class DataError(PyTdxError):
    """数据错误"""
    pass


def handle_api_error(func):
    """
    装饰器：处理API调用错误
    
    Args:
        func: 被装饰的函数
        
    Returns:
        包装后的函数
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConnectionError:
            raise
        except ParameterError:
            raise
        except Exception as e:
            # 转换为统一的异常类型
            raise DataError(f"API调用失败: {str(e)}")
    
    return wrapper


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """
    装饰器：失败重试
    
    Args:
        max_retries: 最大重试次数
        delay: 重试延迟（秒）
        
    Returns:
        包装后的函数
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (ConnectionError, DataError) as e:
                    last_error = e
                    
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))  # 递增延迟
                        continue
                    else:
                        raise last_error
                except Exception as e:
                    # 非预期异常，不重试
                    raise
            
            raise last_error
        
        return wrapper
    
    return decorator


# ============================================================================
# 数据格式化
# ============================================================================

def format_price(price: float, decimals: int = 2) -> str:
    """
    格式化价格
    
    Args:
        price: 价格
        decimals: 小数位数
        
    Returns:
        格式化后的字符串
    """
    return f"{price:.{decimals}f}"


def format_volume(volume: float) -> str:
    """
    格式化成交量
    
    Args:
        volume: 成交量（手）
        
    Returns:
        格式化后的字符串
    """
    if volume >= 100000000:  # 1亿手以上
        return f"{volume/100000000:.2f}亿手"
    elif volume >= 10000:    # 1万手以上
        return f"{volume/10000:.2f}万手"
    else:
        return f"{volume:.0f}手"


def format_amount(amount: float) -> str:
    """
    格式化成交额
    
    Args:
        amount: 成交额（元）
        
    Returns:
        格式化后的字符串
    """
    if amount >= 100000000:  # 1亿元以上
        return f"{amount/100000000:.2f}亿元"
    elif amount >= 10000:    # 1万元以上
        return f"{amount/10000:.2f}万元"
    else:
        return f"{amount:.0f}元"


def format_change(change: float, percent: bool = True) -> str:
    """
    格式化涨跌幅
    
    Args:
        change: 涨跌值
        percent: 是否显示百分比
        
    Returns:
        格式化后的字符串
    """
    if percent:
        return f"{change:+.2f}%"
    else:
        sign = '+' if change >= 0 else ''
        return f"{sign}{change:.2f}"


# ============================================================================
# 其他工具函数
# ============================================================================

def get_trading_date(offset: int = 0) -> str:
    """
    获取交易日（简化版，实际应从交易所获取）
    
    Args:
        offset: 偏移天数（0=今天，-1=昨天，1=明天）
        
    Returns:
        交易日字符串 YYYY-MM-DD
    """
    today = datetime.now()
    target_date = today + timedelta(days=offset)
    
    # 简单处理周末（实际应排除节假日）
    weekday = target_date.weekday()
    if weekday >= 5:  # 周六或周日
        # 调整到最近的周五
        days_to_friday = weekday - 4  # 5-4=1（周六到周五），6-4=2（周日到周五）
        target_date -= timedelta(days=days_to_friday)
    
    return target_date.strftime("%Y-%m-%d")


def is_trading_time() -> bool:
    """
    判断当前是否为交易时间（简化版）
    
    Returns:
        是否为交易时间
    """
    now = datetime.now()
    weekday = now.weekday()
    
    # 周末休市
    if weekday >= 5:
        return False
    
    # 交易时段：9:30-11:30, 13:00-15:00
    hour = now.hour
    minute = now.minute
    
    morning_start = (9, 30)
    morning_end = (11, 30)
    afternoon_start = (13, 0)
    afternoon_end = (15, 0)
    
    current = (hour, minute)
    
    return (morning_start <= current <= morning_end) or (afternoon_start <= current <= afternoon_end)


# ============================================================================
# 测试函数
# ============================================================================

if __name__ == "__main__":
    # 测试参数验证
    print("测试参数验证:")
    
    test_codes = ["000001", "600000", "300001", "123", "ABCDEF", ""]
    for code in test_codes:
        is_valid, error = validate_stock_code(code)
        status = "✓" if is_valid else "✗"
        print(f"  {status} {code:10s} -> {error or '有效'}")
    
    # 测试市场推断
    print("\n测试市场推断:")
    for code in ["000001", "600000", "300118", "688981", "000300"]:
        market = Market.from_code(code)
        print(f"  {code} -> {market.name if market else '未知'}")
    
    # 测试格式化
    print("\n测试格式化:")
    pairs = format_stock_pairs(["000001", "600000", "300118"])
    for market, code in pairs:
        print(f"  {code} -> ({market}, '{code}')")
    
    # 测试日期转换
    print("\n测试日期转换:")
    test_dates = ["2026-03-30", "2026/03/30", "20260330"]
    for date_str in test_dates:
        try:
            date_int = date_to_int(date_str)
            print(f"  {date_str} -> {date_int}")
        except ValueError as e:
            print(f"  {date_str} -> 错误: {e}")
    
    print("\n测试完成")