#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pytdx K线数据模块
获取股票K线数据，支持多种周期
"""

import time
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass
from datetime import datetime

from .connection import get_connection, release_connection, ConnectionMode
from .utils import (
    validate_stock_code, format_stock_pair,
    Market, KLineCategory, PyTdxError, ParameterError, DataError,
    handle_api_error, retry_on_failure,
    format_price, format_volume, format_amount,
    timestamp_to_datetime, datetime_to_str
)


@dataclass
class KLineData:
    """单根K线数据"""
    # 标识信息
    code: str                      # 股票代码
    market: int                    # 市场代码 (0=深圳, 1=上海)
    period: str                    # 周期（如 'daily', '5min'）
    
    # 时间信息
    timestamp: float               # 时间戳（秒）
    datetime: str                  # 日期时间字符串
    
    # 价格信息
    open: float                    # 开盘价
    close: float                   # 收盘价
    high: float                    # 最高价
    low: float                     # 最低价
    
    # 成交量信息
    volume: float                  # 成交量（手）
    amount: float                  # 成交额（元）
    
    # 技术指标（可选）
    ma5: Optional[float] = None    # 5日均线/均线
    ma10: Optional[float] = None   # 10日均线/均线
    ma20: Optional[float] = None   # 20日均线/均线
    ma60: Optional[float] = None   # 60日均线/均线
    
    # 其他字段
    turnover_ratio: Optional[float] = None  # 换手率
    avg_price: Optional[float] = None       # 均价
    
    # 元数据
    source: str = "pytdx"          # 数据源
    index: int = 0                 # 在序列中的位置（0=最新）
    
    def __post_init__(self):
        # 确保datetime是字符串
        if not isinstance(self.datetime, str) and self.timestamp > 0:
            self.datetime = datetime_to_str(timestamp_to_datetime(self.timestamp))
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'code': self.code,
            'market': self.market,
            'period': self.period,
            'timestamp': self.timestamp,
            'datetime': self.datetime,
            'open': self.open,
            'close': self.close,
            'high': self.high,
            'low': self.low,
            'volume': self.volume,
            'amount': self.amount,
            'ma5': self.ma5,
            'ma10': self.ma10,
            'ma20': self.ma20,
            'ma60': self.ma60,
            'turnover_ratio': self.turnover_ratio,
            'avg_price': self.avg_price,
            'source': self.source,
            'index': self.index,
        }
    
    def format(self, verbose: bool = False) -> Dict[str, Any]:
        """
        格式化输出
        
        Args:
            verbose: 是否显示详细信息
            
        Returns:
            格式化后的字典
        """
        result = {
            '时间': self.datetime.split()[0] if ' ' in self.datetime else self.datetime,
            '开盘': format_price(self.open),
            '收盘': format_price(self.close),
            '最高': format_price(self.high),
            '最低': format_price(self.low),
            '涨跌': format_price(self.close - self.open, decimals=3),
            '涨幅': f"{((self.close - self.open) / self.open * 100) if self.open > 0 else 0:+.2f}%",
            '成交量': format_volume(self.volume),
            '成交额': format_amount(self.amount),
        }
        
        if verbose:
            if self.ma5 is not None:
                result['MA5'] = format_price(self.ma5)
            if self.ma10 is not None:
                result['MA10'] = format_price(self.ma10)
            if self.ma20 is not None:
                result['MA20'] = format_price(self.ma20)
            if self.turnover_ratio is not None:
                result['换手率'] = f"{self.turnover_ratio:.2f}%"
        
        return result


@dataclass
class KLineSeries:
    """K线序列数据"""
    code: str                      # 股票代码
    market: int                    # 市场代码
    period: str                    # 周期
    klines: List[KLineData]        # K线列表
    count: int                     # K线数量
    start_time: str                # 开始时间
    end_time: str                  # 结束时间
    
    # 元数据
    source: str = "pytdx"          # 数据源
    response_time_ms: float = 0.0  # 响应时间
    
    def __post_init__(self):
        if self.klines:
            self.start_time = self.klines[-1].datetime if self.klines else ""
            self.end_time = self.klines[0].datetime if self.klines else ""
            self.count = len(self.klines)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'code': self.code,
            'market': self.market,
            'period': self.period,
            'count': self.count,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'klines': [k.to_dict() for k in self.klines],
            'source': self.source,
            'response_time_ms': self.response_time_ms,
        }
    
    def get_latest(self) -> Optional[KLineData]:
        """获取最新K线"""
        return self.klines[0] if self.klines else None
    
    def get_oldest(self) -> Optional[KLineData]:
        """获取最旧K线"""
        return self.klines[-1] if self.klines else None
    
    def slice(self, start: int = 0, end: Optional[int] = None) -> 'KLineSeries':
        """切片获取部分K线"""
        if not self.klines:
            return self
        
        sliced = self.klines[start:end]
        return KLineSeries(
            code=self.code,
            market=self.market,
            period=self.period,
            klines=sliced,
            count=len(sliced),
            start_time=sliced[-1].datetime if sliced else "",
            end_time=sliced[0].datetime if sliced else "",
            source=self.source,
            response_time_ms=self.response_time_ms,
        )
    
    def calculate_ma(self, window: int = 5) -> List[Optional[float]]:
        """
        计算移动平均线
        
        Args:
            window: 窗口大小
            
        Returns:
            移动平均值列表
        """
        if not self.klines or len(self.klines) < window:
            return [None] * len(self.klines)
        
        closes = [k.close for k in self.klines]
        ma_values = []
        
        for i in range(len(closes)):
            if i < window - 1:
                ma_values.append(None)
            else:
                window_closes = closes[i - window + 1:i + 1]
                ma = sum(window_closes) / window
                ma_values.append(ma)
        
        return ma_values
    
    def apply_ma(self, windows: List[int] = [5, 10, 20, 60]):
        """
        计算并应用移动平均线到K线数据
        
        Args:
            windows: 移动平均窗口列表
        """
        if not self.klines:
            return
        
        # 为每个窗口计算MA
        ma_results = {}
        for window in windows:
            ma_results[window] = self.calculate_ma(window)
        
        # 应用到每根K线
        for i, kline in enumerate(self.klines):
            if 5 in windows and ma_results[5][i] is not None:
                kline.ma5 = ma_results[5][i]
            if 10 in windows and ma_results[10][i] is not None:
                kline.ma10 = ma_results[10][i]
            if 20 in windows and ma_results[20][i] is not None:
                kline.ma20 = ma_results[20][i]
            if 60 in windows and ma_results[60][i] is not None:
                kline.ma60 = ma_results[60][i]


def _parse_kline_data(
    raw_data: Dict[str, Any],
    code: str,
    market: int,
    period: str,
    index: int
) -> KLineData:
    """
    解析原始K线数据
    
    Args:
        raw_data: 原始数据行
        code: 股票代码
        market: 市场代码
        period: 周期
        index: 在序列中的位置
        
    Returns:
        KLineData对象
    """
    # 解析时间戳（pytdx返回的时间戳可能是秒或毫秒，也可能是字符串）
    raw_timestamp = raw_data.get('datetime', 0)
    timestamp = 0
    dt_str = ""
    
    if isinstance(raw_timestamp, str):
        # 字符串格式，如 "20260327" 或 "2026-03-27" 或 "2026-03-27 15:00"
        dt_str = raw_timestamp
        
        # 尝试解析常见格式
        formats_to_try = [
            "%Y-%m-%d %H:%M:%S",   # 2026-03-27 15:00:00
            "%Y-%m-%d %H:%M",      # 2026-03-27 15:00
            "%Y%m%d %H:%M:%S",     # 20260327 15:00:00
            "%Y%m%d %H:%M",        # 20260327 15:00
            "%Y-%m-%d",            # 2026-03-27
            "%Y%m%d",              # 20260327
        ]
        
        for fmt in formats_to_try:
            try:
                dt = datetime.strptime(raw_timestamp, fmt)
                timestamp = dt.timestamp()
                
                # 标准化输出格式
                if fmt.endswith("%H:%M:%S"):
                    dt_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                elif fmt.endswith("%H:%M"):
                    dt_str = dt.strftime("%Y-%m-%d %H:%M")
                else:
                    dt_str = dt.strftime("%Y-%m-%d")
                break
            except ValueError:
                continue
        
        # 如果所有格式都失败，保留原始字符串，时间戳为0
        # （这种情况可能发生在其他格式的日期时间字符串）
        
    else:
        # 数值时间戳
        timestamp = float(raw_timestamp)
        if timestamp > 10000000000:  # 毫秒级时间戳
            timestamp = timestamp / 1000
        
        # 转换为日期时间字符串
        if timestamp > 0:
            try:
                dt = timestamp_to_datetime(timestamp)
                dt_str = datetime_to_str(dt)
            except Exception:
                dt_str = ""
    
    return KLineData(
        code=code,
        market=market,
        period=period,
        timestamp=timestamp,
        datetime=dt_str,
        open=float(raw_data.get('open', 0)),
        close=float(raw_data.get('close', 0)),
        high=float(raw_data.get('high', 0)),
        low=float(raw_data.get('low', 0)),
        volume=float(raw_data.get('vol', 0)),
        amount=float(raw_data.get('amount', 0)),
        turnover_ratio=float(raw_data.get('turnover_ratio', 0)) if 'turnover_ratio' in raw_data else None,
        avg_price=float(raw_data.get('avg_price', 0)) if 'avg_price' in raw_data else None,
        source='pytdx',
        index=index,
    )


@handle_api_error
@retry_on_failure(max_retries=2)
def get_kline_data(
    stock_code: str,
    period: Union[str, int, KLineCategory] = 'daily',
    count: int = 120,
    start: int = 0,
    connection_mode: Optional[ConnectionMode] = None,
    server_ip: Optional[str] = None,
    server_port: Optional[int] = None,
    calculate_ma: bool = True
) -> Optional[KLineSeries]:
    """
    获取K线数据
    
    Args:
        stock_code: 股票代码
        period: K线周期（支持字符串如 'daily', '5min' 或数字类别）
        count: 获取数量（最大800）
        start: 起始位置（0=最新）
        connection_mode: 连接模式
        server_ip: 指定服务器IP
        server_port: 指定服务器端口
        calculate_ma: 是否计算移动平均线
        
    Returns:
        KLineSeries 对象，失败返回 None
    """
    # 验证股票代码
    is_valid, error = validate_stock_code(stock_code)
    if not is_valid:
        raise ParameterError(f"股票代码无效: {error}")
    
    # 解析股票代码对
    stock_pair = format_stock_pair(stock_code)
    if not stock_pair:
        raise ParameterError(f"无法解析股票代码: {stock_code}")
    
    market, code = stock_pair
    
    # 验证并标准化K线周期
    category = KLineCategory.from_string(str(period)) if isinstance(period, str) else None
    if category is None:
        try:
            category = KLineCategory(period)
        except (ValueError, TypeError):
            raise ParameterError(f"无效的K线周期: {period}")
    
    # 验证参数范围
    if count <= 0 or count > 800:
        raise ParameterError(f"count参数应在1-800之间，实际: {count}")
    
    if start < 0:
        raise ParameterError(f"start参数应≥0，实际: {start}")
    
    # 记录开始时间
    start_time = time.time()
    
    # 获取连接
    conn = None
    try:
        conn = get_connection(
            server_ip=server_ip,
            server_port=server_port,
            mode=connection_mode
        )
        
        if not conn:
            raise ConnectionError("无法建立连接")
        
        # 获取K线数据
        raw_data = conn.api.get_security_bars(
            category=category.value,
            market=market,
            code=code,
            start=start,
            count=count
        )
        
        # 计算响应时间
        response_time_ms = (time.time() - start_time) * 1000
        
        if not raw_data or len(raw_data) == 0:
            raise DataError(f"未获取到K线数据: {stock_code}")
        
        # 转换为DataFrame
        df = conn.api.to_df(raw_data)
        if df.empty:
            raise DataError(f"数据转换失败: {stock_code}")
        
        # 解析K线数据
        klines = []
        period_str = category.name.lower() if hasattr(category, 'name') else str(period)
        
        for idx, (_, row) in enumerate(df.iterrows()):
            kline = _parse_kline_data(
                raw_data=row.to_dict(),
                code=code,
                market=market,
                period=period_str,
                index=idx
            )
            klines.append(kline)
        
        # pytdx API返回正序（最旧在前），我们需要倒序（最新在前）
        # 反转列表以便最新数据在前
        klines.reverse()
        
        # 创建K线序列
        series = KLineSeries(
            code=code,
            market=market,
            period=period_str,
            klines=klines,
            count=len(klines),
            start_time="",
            end_time="",
            source='pytdx',
            response_time_ms=response_time_ms,
        )
        
        # 计算移动平均线
        if calculate_ma:
            series.apply_ma([5, 10, 20, 60])
        
        return series
        
    except Exception as e:
        # 记录错误
        if conn:
            conn.record_error()
        
        # 重新抛出异常
        if isinstance(e, (ConnectionError, ParameterError, DataError)):
            raise
        else:
            raise DataError(f"获取K线失败: {str(e)}")
    
    finally:
        # 释放连接
        if conn:
            close_conn = (connection_mode == ConnectionMode.SHORT) or (conn.error_count > 2)
            release_connection(conn, close=close_conn)


@handle_api_error
@retry_on_failure(max_retries=2)
def get_index_kline_data(
    index_code: str,
    period: Union[str, int, KLineCategory] = 'daily',
    count: int = 120,
    start: int = 0,
    connection_mode: Optional[ConnectionMode] = None,
    server_ip: Optional[str] = None,
    server_port: Optional[int] = None,
    calculate_ma: bool = True
) -> Optional[KLineSeries]:
    """
    获取指数K线数据
    
    Args:
        index_code: 指数代码
        period: K线周期
        count: 获取数量
        start: 起始位置
        connection_mode: 连接模式
        server_ip: 指定服务器IP
        server_port: 指定服务器端口
        calculate_ma: 是否计算移动平均线
        
    Returns:
        KLineSeries 对象，失败返回 None
    """
    # 指数代码处理（简化：上证指数用上海市场，其他用深圳）
    market = 1 if index_code == '000001' else 0
    
    # 验证参数
    if not isinstance(index_code, str) or len(index_code) != 6 or not index_code.isdigit():
        raise ParameterError(f"指数代码应为6位数字: {index_code}")
    
    # 使用get_security_bars获取指数K线（注意：get_index_bars可能更合适）
    # 这里简化处理，使用相同的接口
    
    # 记录开始时间
    start_time = time.time()
    
    # 获取连接
    conn = None
    try:
        conn = get_connection(
            server_ip=server_ip,
            server_port=server_port,
            mode=connection_mode
        )
        
        if not conn:
            raise ConnectionError("无法建立连接")
        
        # 标准化K线周期
        category = KLineCategory.from_string(str(period)) if isinstance(period, str) else None
        if category is None:
            try:
                category = KLineCategory(period)
            except (ValueError, TypeError):
                raise ParameterError(f"无效的K线周期: {period}")
        
        # 获取指数K线数据
        raw_data = conn.api.get_index_bars(
            category=category.value,
            market=market,
            code=index_code,
            start=start,
            count=count
        )
        
        # 计算响应时间
        response_time_ms = (time.time() - start_time) * 1000
        
        if not raw_data or len(raw_data) == 0:
            raise DataError(f"未获取到指数K线数据: {index_code}")
        
        # 转换为DataFrame
        df = conn.api.to_df(raw_data)
        if df.empty:
            raise DataError(f"数据转换失败: {index_code}")
        
        # 解析K线数据
        klines = []
        period_str = category.name.lower() if hasattr(category, 'name') else str(period)
        
        for idx, (_, row) in enumerate(df.iterrows()):
            kline = _parse_kline_data(
                raw_data=row.to_dict(),
                code=index_code,
                market=market,
                period=period_str,
                index=idx
            )
            klines.append(kline)
        
        # pytdx API返回正序（最旧在前），我们需要倒序（最新在前）
        # 反转列表以便最新数据在前
        klines.reverse()
        
        # 创建K线序列
        series = KLineSeries(
            code=index_code,
            market=market,
            period=period_str,
            klines=klines,
            count=len(klines),
            start_time="",
            end_time="",
            source='pytdx',
            response_time_ms=response_time_ms,
        )
        
        # 计算移动平均线
        if calculate_ma:
            series.apply_ma([5, 10, 20, 60])
        
        return series
        
    except Exception as e:
        # 记录错误
        if conn:
            conn.record_error()
        
        # 重新抛出异常
        if isinstance(e, (ConnectionError, ParameterError, DataError)):
            raise
        else:
            raise DataError(f"获取指数K线失败: {str(e)}")
    
    finally:
        # 释放连接
        if conn:
            close_conn = (connection_mode == ConnectionMode.SHORT) or (conn.error_count > 2)
            release_connection(conn, close=close_conn)


def print_kline_summary(series: KLineSeries, show_count: int = 5):
    """
    打印K线摘要
    
    Args:
        series: KLineSeries对象
        show_count: 显示最近多少根K线
    """
    if not series or not series.klines:
        print("无K线数据")
        return
    
    print(f"\n{series.code} {series.period.upper()} K线")
    print(f"时间范围: {series.start_time} 到 {series.end_time}")
    print(f"K线数量: {series.count}")
    print("=" * 80)
    
    # 显示表头
    header = ["时间", "开盘", "收盘", "最高", "最低", "涨跌", "涨幅", "成交量", "成交额"]
    if series.klines[0].ma5 is not None:
        header.append("MA5")
    if series.klines[0].ma10 is not None:
        header.append("MA10")
    
    print(" | ".join(header))
    print("-" * 80)
    
    # 显示最近的K线
    for kline in series.klines[:show_count]:
        formatted = kline.format(verbose=False)
        
        row = [
            formatted['时间'],
            formatted['开盘'],
            formatted['收盘'],
            formatted['最高'],
            formatted['最低'],
            formatted['涨跌'],
            formatted['涨幅'],
            formatted['成交量'],
            formatted['成交额'],
        ]
        
        if kline.ma5 is not None:
            row.append(format_price(kline.ma5))
        if kline.ma10 is not None:
            row.append(format_price(kline.ma10))
        
        print(" | ".join(row))
    
    # 显示统计信息
    if series.klines:
        latest = series.get_latest()
        if latest:
            print(f"\n最新K线:")
            for key, value in latest.format(verbose=True).items():
                print(f"  {key}: {value}")


# ============================================================================
# 测试函数
# ============================================================================

if __name__ == "__main__":
    print("测试K线数据模块...")
    
    # 测试股票K线
    test_codes = ["000001", "600000"]
    
    for code in test_codes:
        try:
            print(f"\n获取 {code} 日K线:")
            series = get_kline_data(
                stock_code=code,
                period='daily',
                count=20,
                connection_mode=ConnectionMode.SHORT
            )
            
            if series:
                print_kline_summary(series, show_count=5)
            else:
                print(f"  失败: 未获取到数据")
                
        except Exception as e:
            print(f"  异常: {e}")
    
    # 测试不同周期
    test_periods = ['5min', '15min', 'daily', 'weekly']
    
    for period in test_periods[:2]:  # 只测试前两个，避免太慢
        try:
            print(f"\n获取 000001 {period} K线:")
            series = get_kline_data(
                stock_code='000001',
                period=period,
                count=10,
                connection_mode=ConnectionMode.SHORT
            )
            
            if series:
                print(f"  成功: 获取到{series.count}根{period}K线")
                if series.klines:
                    latest = series.get_latest()
                    print(f"  最新: {latest.datetime} 收盘{format_price(latest.close)}")
            else:
                print(f"  失败: 未获取到数据")
                
        except Exception as e:
            print(f"  异常: {e}")
    
    # 测试指数K线
    try:
        print(f"\n获取上证指数日K线:")
        series = get_index_kline_data(
            index_code='000001',
            period='daily',
            count=10,
            connection_mode=ConnectionMode.SHORT
        )
        
        if series:
            print_kline_summary(series, show_count=3)
        else:
            print(f"  失败: 未获取到数据")
            
    except Exception as e:
        print(f"  异常: {e}")
    
    print("\n测试完成")