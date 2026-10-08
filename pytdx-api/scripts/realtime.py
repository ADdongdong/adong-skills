#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pytdx 实时行情模块
获取股票实时行情数据
"""

import time
from typing import Optional, Dict, Any, List, Union, Tuple
from dataclasses import dataclass

from .connection import get_connection, release_connection, ConnectionMode
from .utils import (
    validate_stock_code, format_stock_pair, format_stock_pairs,
    Market, PyTdxError, ParameterError, DataError,
    handle_api_error, retry_on_failure,
    format_price, format_volume, format_amount, format_change
)


@dataclass
class QuoteData:
    """实时行情数据"""
    # 基础信息
    code: str                      # 股票代码
    market: int                    # 市场代码 (0=深圳, 1=上海)
    name: Optional[str] = None     # 股票名称（需要从其他接口获取）
    
    # 价格信息
    price: float = 0.0             # 当前价格
    last_close: float = 0.0        # 昨收价
    open: float = 0.0              # 开盘价
    high: float = 0.0              # 最高价
    low: float = 0.0               # 最低价
    
    # 涨跌信息
    change: float = 0.0            # 涨跌额
    change_percent: float = 0.0    # 涨跌幅（%）
    
    # 成交量信息
    volume: float = 0.0            # 成交量（手）
    amount: float = 0.0            # 成交额（元）
    
    # 买卖盘（前五档）
    bid_prices: List[float] = None      # 买价 [bid1, bid2, ...]
    bid_volumes: List[float] = None     # 买量
    ask_prices: List[float] = None      # 卖价
    ask_volumes: List[float] = None     # 卖量
    
    # 内外盘
    inner_volume: float = 0.0      # 内盘（主动卖）
    outer_volume: float = 0.0      # 外盘（主动买）
    
    # 时间信息
    timestamp: float = 0.0         # 时间戳
    server_time: str = ""          # 服务器时间
    
    # 元数据
    source: str = "pytdx"          # 数据源
    response_time_ms: float = 0.0  # 响应时间
    
    def __post_init__(self):
        if self.bid_prices is None:
            self.bid_prices = []
        if self.bid_volumes is None:
            self.bid_volumes = []
        if self.ask_prices is None:
            self.ask_prices = []
        if self.ask_volumes is None:
            self.ask_volumes = []
        
        # 如果价格有效但涨跌未计算，则自动计算
        if self.price > 0 and self.last_close > 0 and self.change == 0:
            self.change = self.price - self.last_close
            self.change_percent = (self.change / self.last_close) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'code': self.code,
            'market': self.market,
            'name': self.name,
            'price': self.price,
            'last_close': self.last_close,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'change': self.change,
            'change_percent': self.change_percent,
            'volume': self.volume,
            'amount': self.amount,
            'bid_prices': self.bid_prices,
            'bid_volumes': self.bid_volumes,
            'ask_prices': self.ask_prices,
            'ask_volumes': self.ask_volumes,
            'inner_volume': self.inner_volume,
            'outer_volume': self.outer_volume,
            'timestamp': self.timestamp,
            'server_time': self.server_time,
            'source': self.source,
            'response_time_ms': self.response_time_ms,
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
            '代码': self.code,
            '市场': '深圳' if self.market == 0 else '上海',
            '名称': self.name or 'N/A',
            '价格': format_price(self.price),
            '涨跌': format_change(self.change, percent=False),
            '涨幅': format_change(self.change_percent),
            '昨收': format_price(self.last_close),
            '今开': format_price(self.open),
            '最高': format_price(self.high),
            '最低': format_price(self.low),
            '成交量': format_volume(self.volume),
            '成交额': format_amount(self.amount),
        }
        
        if verbose:
            result.update({
                '内外盘': f"内{format_volume(self.inner_volume)}/外{format_volume(self.outer_volume)}",
                '时间': self.server_time,
                '响应时间': f"{self.response_time_ms:.1f}ms",
            })
            
            # 买卖五档
            if self.bid_prices and self.ask_prices:
                bid_ask = []
                for i in range(min(5, len(self.bid_prices), len(self.ask_prices))):
                    bid_str = f"买{i+1}: {format_price(self.bid_prices[i])}×{format_volume(self.bid_volumes[i])}"
                    ask_str = f"卖{i+1}: {format_price(self.ask_prices[i])}×{format_volume(self.ask_volumes[i])}"
                    bid_ask.append(f"{bid_str} | {ask_str}")
                
                if bid_ask:
                    result['买卖盘'] = bid_ask
        
        return result


def _parse_quote_data(raw_data: Dict[str, Any], response_time_ms: float = 0.0) -> QuoteData:
    """
    解析原始行情数据
    
    Args:
        raw_data: pytdx返回的原始数据
        response_time_ms: 响应时间
        
    Returns:
        解析后的QuoteData
    """
    # 提取买卖盘数据（前五档）
    bid_prices = []
    bid_volumes = []
    ask_prices = []
    ask_volumes = []
    
    for i in range(1, 6):
        bid_price_key = f'bid{i}'
        bid_vol_key = f'bid_vol{i}'
        ask_price_key = f'ask{i}'
        ask_vol_key = f'ask_vol{i}'
        
        if bid_price_key in raw_data and raw_data[bid_price_key]:
            bid_prices.append(float(raw_data[bid_price_key]))
            bid_volumes.append(float(raw_data.get(bid_vol_key, 0)))
        
        if ask_price_key in raw_data and raw_data[ask_price_key]:
            ask_prices.append(float(raw_data[ask_price_key]))
            ask_volumes.append(float(raw_data.get(ask_vol_key, 0)))
    
    # 计算涨跌
    price = float(raw_data.get('price', 0))
    last_close = float(raw_data.get('last_close', 0))
    change = price - last_close if price > 0 and last_close > 0 else 0
    change_percent = (change / last_close * 100) if last_close > 0 else 0
    
    return QuoteData(
        code=str(raw_data.get('code', '')),
        market=int(raw_data.get('market', 0)),
        price=price,
        last_close=last_close,
        open=float(raw_data.get('open', 0)),
        high=float(raw_data.get('high', 0)),
        low=float(raw_data.get('low', 0)),
        change=change,
        change_percent=change_percent,
        volume=float(raw_data.get('vol', 0)),
        amount=float(raw_data.get('amount', 0)),
        bid_prices=bid_prices,
        bid_volumes=bid_volumes,
        ask_prices=ask_prices,
        ask_volumes=ask_volumes,
        inner_volume=float(raw_data.get('s_vol', 0)),  # 内盘
        outer_volume=float(raw_data.get('b_vol', 0)),  # 外盘
        timestamp=time.time(),
        server_time=str(raw_data.get('servertime', '')),
        source='pytdx',
        response_time_ms=response_time_ms,
    )


@handle_api_error
@retry_on_failure(max_retries=2)
def get_realtime_quote(
    stock_code: str,
    connection_mode: Optional[ConnectionMode] = None,
    server_ip: Optional[str] = None,
    server_port: Optional[int] = None
) -> Optional[QuoteData]:
    """
    获取单只股票实时行情
    
    Args:
        stock_code: 股票代码（如 '000001', '600000'）
        connection_mode: 连接模式
        server_ip: 指定服务器IP
        server_port: 指定服务器端口
        
    Returns:
        QuoteData 对象，失败返回 None
    """
    # 验证股票代码
    is_valid, error = validate_stock_code(stock_code)
    if not is_valid:
        raise ParameterError(f"股票代码无效: {error}")
    
    # 格式化股票代码对
    stock_pair = format_stock_pair(stock_code)
    if not stock_pair:
        raise ParameterError(f"无法解析股票代码: {stock_code}")
    
    # 记录开始时间
    start_time = time.time()
    
    # 获取连接
    conn = None
    try:
        # 获取连接
        conn = get_connection(
            server_ip=server_ip,
            server_port=server_port,
            mode=connection_mode
        )
        
        if not conn:
            raise ConnectionError("无法建立连接")
        
        # 查询行情
        raw_data_list = conn.api.get_security_quotes([stock_pair])
        
        # 计算响应时间
        response_time_ms = (time.time() - start_time) * 1000
        
        if not raw_data_list or len(raw_data_list) == 0:
            raise DataError(f"未获取到行情数据: {stock_code}")
        
        # 转换为DataFrame格式（pytdx的to_df方法）
        df = conn.api.to_df(raw_data_list)
        if df.empty:
            raise DataError(f"数据转换失败: {stock_code}")
        
        # 提取第一行数据
        raw_quote = df.iloc[0].to_dict()
        
        # 解析数据
        quote = _parse_quote_data(raw_quote, response_time_ms)
        
        return quote
        
    except Exception as e:
        # 记录错误
        if conn:
            conn.record_error()
        
        # 重新抛出异常（会被装饰器处理）
        if isinstance(e, (ConnectionError, ParameterError, DataError)):
            raise
        else:
            raise DataError(f"获取行情失败: {str(e)}")
    
    finally:
        # 释放连接（短连接模式或异常时关闭）
        if conn:
            close_conn = (connection_mode == ConnectionMode.SHORT) or (conn.error_count > 2)
            release_connection(conn, close=close_conn)


@handle_api_error
@retry_on_failure(max_retries=2)
def get_batch_quotes(
    stock_codes: List[str],
    connection_mode: Optional[ConnectionMode] = None,
    server_ip: Optional[str] = None,
    server_port: Optional[int] = None,
    batch_size: int = 50
) -> Dict[str, Optional[QuoteData]]:
    """
    批量获取股票实时行情
    
    Args:
        stock_codes: 股票代码列表
        connection_mode: 连接模式
        server_ip: 指定服务器IP
        server_port: 指定服务器端口
        batch_size: 每批查询数量（pytdx支持批量查询，但建议分批）
        
    Returns:
        字典 {股票代码: QuoteData 或 None}
    """
    if not stock_codes:
        return {}
    
    # 验证并格式化所有股票代码
    valid_pairs = []
    valid_codes = []
    invalid_codes = []
    
    for code in stock_codes:
        is_valid, error = validate_stock_code(code)
        if is_valid:
            pair = format_stock_pair(code)
            if pair:
                valid_pairs.append(pair)
                valid_codes.append(code)
            else:
                invalid_codes.append((code, "格式转换失败"))
        else:
            invalid_codes.append((code, error))
    
    if not valid_pairs:
        raise ParameterError(f"所有股票代码都无效: {invalid_codes}")
    
    # 记录开始时间
    start_time = time.time()
    
    # 获取连接
    conn = None
    results = {code: None for code in stock_codes}
    
    try:
        # 获取连接（批量查询建议使用连接池）
        if connection_mode is None:
            connection_mode = ConnectionMode.POOL
        
        conn = get_connection(
            server_ip=server_ip,
            server_port=server_port,
            mode=connection_mode
        )
        
        if not conn:
            raise ConnectionError("无法建立连接")
        
        # 分批查询（避免单次查询过多）
        for i in range(0, len(valid_pairs), batch_size):
            batch_pairs = valid_pairs[i:i + batch_size]
            batch_codes = valid_codes[i:i + batch_size]
            
            try:
                # 查询行情
                raw_data_list = conn.api.get_security_quotes(batch_pairs)
                response_time_ms = ((time.time() - start_time) * 1000) / ((i/batch_size)+1)
                
                if raw_data_list and len(raw_data_list) > 0:
                    # 转换为DataFrame
                    df = conn.api.to_df(raw_data_list)
                    
                    # 处理每只股票
                    for idx, code in enumerate(batch_codes):
                        if idx < len(df):
                            row = df.iloc[idx]
                            raw_quote = row.to_dict()
                            
                            # 解析数据
                            quote = _parse_quote_data(raw_quote, response_time_ms)
                            results[code] = quote
                        else:
                            results[code] = None
                
            except Exception as e:
                # 当前批次失败，记录但继续下一批
                for code in batch_codes:
                    results[code] = None
                print(f"批次 {i//batch_size + 1} 失败: {e}")
                continue
        
        # 记录无效代码
        for code, error in invalid_codes:
            results[code] = None
        
        return results
        
    except Exception as e:
        # 记录错误
        if conn:
            conn.record_error()
        
        # 重新抛出异常
        if isinstance(e, (ConnectionError, ParameterError, DataError)):
            raise
        else:
            raise DataError(f"批量获取行情失败: {str(e)}")
    
    finally:
        # 释放连接
        if conn:
            release_connection(conn, close=False)


@handle_api_error
def get_index_quote(
    index_code: str,
    connection_mode: Optional[ConnectionMode] = None,
    server_ip: Optional[str] = None,
    server_port: Optional[int] = None
) -> Optional[QuoteData]:
    """
    获取指数实时行情
    
    Args:
        index_code: 指数代码（如 '000001' 上证指数, '399001' 深成指）
        connection_mode: 连接模式
        server_ip: 指定服务器IP
        server_port: 指定服务器端口
        
    Returns:
        QuoteData 对象，失败返回 None
    """
    # 指数代码通常也是6位数字，但市场判断不同
    # 这里简化处理：上证指数(000001)用上海市场，其他用深圳市场
    market = 1 if index_code == '000001' else 0
    
    # 使用股票行情接口（指数也适用）
    return get_realtime_quote(
        stock_code=index_code,
        connection_mode=connection_mode,
        server_ip=server_ip,
        server_port=server_port
    )


def print_quote_summary(quote: QuoteData, show_details: bool = False):
    """
    打印行情摘要
    
    Args:
        quote: QuoteData对象
        show_details: 是否显示详细信息
    """
    if not quote:
        print("无行情数据")
        return
    
    formatted = quote.format(verbose=show_details)
    
    print(f"\n{quote.code} {formatted.get('名称', 'N/A')}")
    print("=" * 50)
    
    # 基础信息
    print(f"价格: {formatted['价格']} ({formatted['涨幅']})")
    print(f"区间: {formatted['最低']} - {formatted['最高']}")
    print(f"今开: {formatted['今开']} | 昨收: {formatted['昨收']}")
    print(f"成交: {formatted['成交量']} | 金额: {formatted['成交额']}")
    
    if show_details:
        print(f"市场: {formatted['市场']}")
        print(f"时间: {formatted.get('时间', 'N/A')}")
        print(f"响应: {formatted.get('响应时间', 'N/A')}")
        
        # 买卖盘
        if '买卖盘' in formatted:
            print("\n买卖盘:")
            for line in formatted['买卖盘']:
                print(f"  {line}")
        
        # 内外盘
        if '内外盘' in formatted:
            print(f"内外盘: {formatted['内外盘']}")
    
    print()


# ============================================================================
# 测试函数
# ============================================================================

if __name__ == "__main__":
    print("测试实时行情模块...")
    
    # 测试单只股票
    test_codes = ["000001", "600000", "300118"]
    
    for code in test_codes:
        try:
            print(f"\n获取 {code} 行情:")
            quote = get_realtime_quote(code, connection_mode=ConnectionMode.SHORT)
            
            if quote:
                print_quote_summary(quote, show_details=False)
            else:
                print(f"  失败: 未获取到数据")
                
        except Exception as e:
            print(f"  异常: {e}")
    
    # 测试批量获取
    try:
        print(f"\n批量获取 {len(test_codes)} 只股票:")
        results = get_batch_quotes(test_codes, batch_size=2)
        
        success_count = sum(1 for q in results.values() if q is not None)
        print(f"  成功: {success_count}/{len(test_codes)}")
        
        for code, quote in results.items():
            if quote:
                print(f"    {code}: {format_price(quote.price)} ({format_change(quote.change_percent)})")
            else:
                print(f"    {code}: 失败")
                
    except Exception as e:
        print(f"  批量获取异常: {e}")
    
    print("\n测试完成")