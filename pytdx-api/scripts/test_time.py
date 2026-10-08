#!/usr/bin/env python3
"""测试交易时间判断"""
from datetime import datetime, time as dt_time

now = datetime.now()
current_time = now.time()
weekday = now.weekday()

print(f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"星期: {weekday+1}")

# 交易时间
morning_start = dt_time(9, 30)
morning_end = dt_time(11, 30)
afternoon_start = dt_time(13, 0)
afternoon_end = dt_time(15, 0)

is_trading_day = weekday < 5  # 周一到周五
is_trading_time = (morning_start <= current_time <= morning_end) or (afternoon_start <= current_time <= afternoon_end)
is_after_close = current_time > afternoon_end

print(f"是否交易日: {is_trading_day}")
print(f"是否交易时间: {is_trading_time}")
print(f"是否收盘后: {is_after_close}")

# 判断应该使用哪种数据
if not is_trading_day:
    print("-> 非交易日，使用历史分时")
elif is_trading_time:
    print("-> 交易时间，使用当天分时")
elif is_after_close:
    print("-> 收盘后，使用当天分时（已完成）")
else:
    print("-> 开盘前，使用历史分时")
