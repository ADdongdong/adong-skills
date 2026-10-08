#!/usr/bin/env python3
"""测试分时接口"""
import sys

from .minute import get_minute_time_data

print("=== 兼容接口测试 get_minute_time_data(1, '600300') ===")
series = get_minute_time_data(1, '600300')

if series:
    print(f"股票代码: {series.code}")
    print(f"日期: {series.date}")
    print(f"昨收: {series.preclose:.2f}")
    print(f"当前: {series.current:.2f}")
    print(f"涨跌: {series.change:+.2f} ({series.change_percent:+.2f}%)")
    print(f"分时数据: {series.count} 条")
    if series.data:
        print()
        print("前3条:")
        for d in series.data[:3]:
            print(f"  {d}")
        print()
        print("后3条:")
        for d in series.data[-3:]:
            print(f"  {d}")
else:
    print("获取失败")
