#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pytdx 分时数据模块
获取股票分时行情数据
"""

import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, timedelta, time as dt_time

from .connection import get_connection, release_connection, ConnectionMode
from .utils import (
    validate_stock_code, format_stock_pair,
    Market, PyTdxError, ParameterError, DataError,
    handle_api_error, retry_on_failure,
)


@dataclass
class MinuteData:
    """单条分时数据"""
    time: str              # 时间 "HH:MM"
    price: float           # 价格
    volume: int            # 成交量（手）
    amount: float          # 成交额
    
    def __str__(self):
        return f"[{self.time}] {self.price:.2f} 元, 量:{self.volume}手"


@dataclass
class MinuteSeries:
    """分时数据序列"""
    code: str
    market: int
    date: str
    preclose: float        # 昨收
    open: float            # 开盘
    high: float            # 最高
    low: float             # 最低
    current: float         # 当前价
    
    data: List[MinuteData]
    
    @property
    def count(self) -> int:
        return len(self.data)
    
    @property
    def total_volume(self) -> int:
        return sum(d.volume for d in self.data)
    
    @property
    def total_amount(self) -> float:
        return sum(d.amount for d in self.data)
    
    @property
    def change(self) -> float:
        return self.current - self.preclose
    
    @property
    def change_percent(self) -> float:
        if self.preclose == 0:
            return 0.0
        return (self.change / self.preclose) * 100
    
    def get_latest(self) -> Optional[MinuteData]:
        return self.data[-1] if self.data else None
    
    def to_dict_list(self) -> List[Dict]:
        return [
            {
                'time': d.time,
                'price': d.price,
                'volume': d.volume,
                'amount': d.amount,
            }
            for d in self.data
        ]


def _get_last_trading_date() -> int:
    """获取最近交易日日期（简单实现：跳过周末）"""
    now = datetime.now()
    weekday = now.weekday()
    
    if weekday == 5:  # 周六
        now -= timedelta(days=1)
    elif weekday == 6:  # 周日
        now -= timedelta(days=2)
    
    return int(now.strftime("%Y%m%d"))


def _should_use_history_data() -> bool:
    """
    判断是否应该使用历史分时数据
    
    规则：
    - 非交易日（周末）：使用历史分时
    - 交易日开盘前（< 9:30）：使用历史分时
    - 交易日交易时间或收盘后：使用当天分时
    """
    now = datetime.now()
    current_time = now.time()
    weekday = now.weekday()
    
    # 非交易日（周末）
    if weekday >= 5:
        return True
    
    # 交易时间定义
    morning_start = dt_time(9, 30)
    afternoon_end = dt_time(15, 0)
    
    # 开盘前
    if current_time < morning_start:
        return True
    
    # 交易时间或收盘后，使用当天数据
    return False


def _get_previous_trading_date() -> int:
    """获取前一个交易日"""
    now = datetime.now()
    now -= timedelta(days=1)
    
    while now.weekday() >= 5:  # 跳过周末
        now -= timedelta(days=1)
    
    return int(now.strftime("%Y%m%d"))


def _is_valid_price(price: float, preclose: float) -> bool:
    """检查价格是否合理"""
    if price <= 0:
        return False
    if preclose > 0:
        # 价格不应超过昨收的20%（涨跌停限制）
        ratio = abs(price - preclose) / preclose
        return ratio < 0.25
    return True


@handle_api_error
@retry_on_failure(max_retries=2)
def get_minute_data(
    stock_code: str,
    date: Optional[int] = None,
    connection_mode: Optional[ConnectionMode] = None,
    server_ip: Optional[str] = None,
    server_port: Optional[int] = None,
) -> Optional[MinuteSeries]:
    """
    获取股票分时数据
    
    Args:
        stock_code: 股票代码，如 "600726"、"000001"
        date: 日期，格式 20260327，None 表示当天
        connection_mode: 连接模式
        server_ip: 指定服务器IP
        server_port: 指定服务器端口
    
    Returns:
        MinuteSeries 对象，包含分时数据
    
    Example:
        >>> series = get_minute_data('600726')
        >>> print(f"当前价: {series.current}")
        >>> print(f"涨跌幅: {series.change_percent:.2f}%")
    """
    market, code = format_stock_pair(stock_code)
    
    conn = get_connection(server_ip, server_port, mode=connection_mode)
    if not conn:
        raise ConnectionError("无法建立连接")
    
    try:
        # 获取实时行情（包含昨收、开盘、最高、最低等）
        quote_data = conn.api.get_security_quotes([(market, code)])
        if not quote_data:
            raise DataError(f"未获取到 {stock_code} 的实时行情")
        
        quote = quote_data[0]
        preclose = float(quote.get('last_close', 0))
        open_price = float(quote.get('open', 0))
        high_price = float(quote.get('high', 0))
        low_price = float(quote.get('low', 0))
        current = float(quote.get('price', 0))
        total_vol = int(quote.get('vol', 0))
        total_amount = float(quote.get('amount', 0))
        
        # 获取分时数据
        raw_data = None
        actual_date = date
        
        if date:
            # 指定日期，使用历史分时接口
            raw_data = conn.api.get_history_minute_time_data(market, code, date)
        else:
            # 判断是否应该使用历史分时
            if _should_use_history_data():
                # 非交易时间，使用历史分时
                actual_date = _get_previous_trading_date()
                raw_data = conn.api.get_history_minute_time_data(market, code, actual_date)
            else:
                # 交易时间或收盘后，使用当天分时
                raw_data = conn.api.get_minute_time_data(market, code)
        
        data_list = []
        if raw_data:
            for i, item in enumerate(raw_data):
                if isinstance(item, dict):
                    price = float(item.get('price', 0))
                    vol = int(item.get('vol', 0))
                    
                    # 跳过无效价格
                    if not _is_valid_price(price, preclose):
                        continue
                    
                    # 计算时间（每分钟一条）
                    # 上午: 9:30-11:30 (120分钟)
                    # 下午: 13:00-15:00 (120分钟)
                    if i < 120:
                        hour = 9 + (i + 30) // 60
                        minute = (i + 30) % 60
                    else:
                        hour = 13 + (i - 120) // 60
                        minute = (i - 120) % 60
                    
                    if hour > 15 or (hour == 11 and minute > 30):
                        continue
                    
                    time_str = f"{hour:02d}:{minute:02d}"
                    
                    # 成交额估算
                    amount = price * abs(vol) * 100
                    
                    data_list.append(MinuteData(
                        time=time_str,
                        price=price,
                        volume=abs(vol),
                        amount=amount,
                    ))
        
        # 日期字符串
        date_str = str(actual_date) if actual_date else datetime.now().strftime("%Y-%m-%d")
        
        return MinuteSeries(
            code=code,
            market=market,
            date=date_str,
            preclose=preclose,
            open=open_price,
            high=high_price,
            low=low_price,
            current=current,
            data=data_list,
        )
        
    finally:
        release_connection(conn, close=(connection_mode == ConnectionMode.SHORT))


@handle_api_error
@retry_on_failure(max_retries=2)
def get_minute_time_data(
    market: int,
    stock_code: str,
    date: Optional[int] = None,
    connection_mode: Optional[ConnectionMode] = None,
) -> Optional[MinuteSeries]:
    """
    兼容原pytdx接口的分时数据获取
    
    Args:
        market: 市场代码 (0=深圳, 1=上海)
        stock_code: 股票代码
        date: 日期，格式 20260327
        connection_mode: 连接模式
    
    Returns:
        MinuteSeries 对象
    
    Example:
        >>> series = get_minute_time_data(1, '600726')
    """
    return get_minute_data(stock_code, date, connection_mode)


def print_minute_summary(series: MinuteSeries):
    """打印分时数据摘要"""
    print(f"\n=== {series.code} 分时数据 ===")
    print(f"日期: {series.date}")
    print(f"昨收: {series.preclose:.2f}")
    print(f"开盘: {series.open:.2f}")
    print(f"最高: {series.high:.2f}")
    print(f"最低: {series.low:.2f}")
    print(f"当前: {series.current:.2f}")
    print(f"涨跌: {series.change:+.2f} ({series.change_percent:+.2f}%)")
    print(f"分时数据: {series.count} 条")
    
    if series.data:
        latest = series.get_latest()
        print(f"\n最新: {latest}")


if __name__ == "__main__":
    print("测试分时数据获取...")
    
    series = get_minute_data('600726')
    if series:
        print_minute_summary(series)
    else:
        print("获取失败")
