#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pytdx-api 脚本包
提供通达信pytdx库的封装接口
"""

from .connection import (
    ConnectionMode,
    ConnectionPool,
    PyTdxConnection,
    get_global_pool,
    get_connection,
    release_connection,
    cleanup_connections,
    get_connection_stats,
)

from .utils import (
    Market,
    KLineCategory,
    BlockType,
    PyTdxError,
    ConnectionError,
    ParameterError,
    DataError,
    validate_stock_code,
    validate_market,
    validate_kline_category,
    format_stock_pair,
    format_stock_pairs,
    date_to_int,
    is_trading_time,
)

from .realtime import (
    QuoteData,
    get_realtime_quote,
    get_batch_quotes,
    get_index_quote,
    print_quote_summary,
)

from .kline import (
    KLineData,
    KLineSeries,
    get_kline_data,
    get_index_kline_data,
    print_kline_summary,
)

from .minute import (
    MinuteData,
    MinuteSeries,
    get_minute_data,
    get_minute_time_data,
    print_minute_summary,
)

__version__ = "1.0.0"
__all__ = [
    # connection
    'ConnectionMode',
    'ConnectionPool',
    'PyTdxConnection',
    'get_global_pool',
    'get_connection',
    'release_connection',
    'cleanup_connections',
    'get_connection_stats',
    
    # utils
    'Market',
    'KLineCategory',
    'BlockType',
    'PyTdxError',
    'ConnectionError',
    'ParameterError',
    'DataError',
    'validate_stock_code',
    'validate_market',
    'validate_kline_category',
    'format_stock_pair',
    'format_stock_pairs',
    'date_to_int',
    'is_trading_time',
    
    # realtime
    'QuoteData',
    'get_realtime_quote',
    'get_batch_quotes',
    'get_index_quote',
    'print_quote_summary',
    
    # kline
    'KLineData',
    'KLineSeries',
    'get_kline_data',
    'get_index_kline_data',
    'print_kline_summary',
    
    # minute
    'MinuteData',
    'MinuteSeries',
    'get_minute_data',
    'get_minute_time_data',
    'print_minute_summary',
]

print(f"pytdx-api scripts v{__version__} loaded")