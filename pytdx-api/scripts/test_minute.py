#!/usr/bin/env python3
"""测试pytdx分时数据"""
from pytdx.hq import TdxHq_API

api = TdxHq_API()
if api.connect('218.75.126.9', 7709):
    quote = api.get_security_quotes([(1, '600726')])
    if quote:
        print('=== 实时行情 ===')
        q = quote[0]
        print(f"昨收: {q['last_close']}")
        print(f"开盘: {q['open']}")
        print(f"当前: {q['price']}")
        print(f"最高: {q['high']}")
        print(f"最低: {q['low']}")
    
    print()
    print('=== get_minute_time_data 原始数据 ===')
    data = api.get_minute_time_data(1, '600726')
    if data:
        print(f'数据长度: {len(data)}')
        print()
        print('前10条:')
        for i, item in enumerate(data[:10]):
            print(f"  {i}: price={item.get('price')}, vol={item.get('vol')}")
        
        print()
        print('后10条:')
        for i, item in enumerate(data[-10:]):
            idx = len(data) - 10 + i
            print(f"  {idx}: price={item.get('price')}, vol={item.get('vol')}")
    
    print()
    print('=== get_history_minute_time_data 历史分时 ===')
    data2 = api.get_history_minute_time_data(1, '600726', 20260327)
    if data2:
        print(f'数据长度: {len(data2)}')
        print()
        print('前10条:')
        for i, item in enumerate(data2[:10]):
            print(f"  {i}: price={item.get('price')}, vol={item.get('vol')}")
        
        print()
        print('后10条:')
        for i, item in enumerate(data2[-10:]):
            idx = len(data2) - 10 + i
            print(f"  {idx}: price={item.get('price')}, vol={item.get('vol')}")
    
    api.disconnect()
