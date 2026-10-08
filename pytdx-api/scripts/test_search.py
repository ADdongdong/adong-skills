#!/usr/bin/env python3
"""测试股票名称搜索"""
from pytdx.hq import TdxHq_API

api = TdxHq_API()
if api.connect('115.238.56.198', 7709):
    print('=== 测试 get_security_list 正确用法 ===')
    
    # pytdx的get_security_list返回的是分类列表
    # 要获取股票列表需要遍历
    
    print('\n--- 深圳市场股票 (market=0) ---')
    count = 0
    for start in range(0, 10000, 1000):
        data = api.get_security_list(0, start)
        if not data:
            break
        for item in data:
            code = item.get('code', '')
            name = item.get('name', '')
            # 只显示股票代码（6位数字）
            if len(code) == 6 and code.isdigit():
                count += 1
                if count <= 10:
                    print(f"  {code} - {name}")
    print(f"  ... 共 {count} 只")
    
    print('\n--- 上海市场股票 (market=1) ---')
    count = 0
    for start in range(0, 10000, 1000):
        data = api.get_security_list(1, start)
        if not data:
            break
        for item in data:
            code = item.get('code', '')
            name = item.get('name', '')
            if len(code) == 6 and code.isdigit():
                count += 1
                if count <= 10:
                    print(f"  {code} - {name}")
    print(f"  ... 共 {count} 只")
    
    print('\n=== 搜索"平安银行" ===')
    found = {}
    for market in [0, 1]:
        for start in range(0, 10000, 1000):
            data = api.get_security_list(market, start)
            if not data:
                break
            for item in data:
                code = item.get('code', '')
                name = item.get('name', '')
                if len(code) == 6 and code.isdigit() and '平安' in name:
                    if code not in found:
                        found[code] = (market, name)
    
    print(f"找到 {len(found)} 只")
    for code, (m, name) in found.items():
        print(f"  {code} ({'深圳' if m==0 else '上海'}) - {name}")
    
    api.disconnect()
