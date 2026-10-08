#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TDX DLL 路径配置工具
用于设置通达信 DLL 文件路径
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib import config


def main():
    """交互式配置DLL路径"""
    print("=" * 70)
    print(" " * 20 + "TDX DLL 路径配置工具")
    print("=" * 70)
    
    # 检查当前配置
    current_path = config.find_dll()
    if current_path:
        print(f"\n✓ 已找到DLL文件: {current_path}")
        print("\n是否需要更换路径? (y/n): ", end="")
        choice = input().strip().lower()
        if choice != 'y':
            print("\n保持当前配置，退出。")
            return
    
    print("\n未找到通达信 DLL 文件 (TPythClient.dll)")
    print("-" * 70)
    print("\nDLL 文件通常位于以下位置:")
    print("  <通达信安装目录>/PYPlugins/TPythClient.dll")
    print("\n常见安装路径:")
    for i, path in enumerate(config.COMMON_PATHS[:5], 1):
        status = "✓" if os.path.exists(path) else "✗"
        print(f"  {i}. [{status}] {path}")
    
    print("\n" + "-" * 70)
    print("请输入完整的 DLL 文件路径 (例如: D:/new_tdx64/PYPlugins/TPythClient.dll)")
    print("或输入 'q' 退出: ")
    
    while True:
        print("\n> ", end="")
        user_path = input().strip()
        
        if user_path.lower() == 'q':
            print("\n退出配置。")
            return
        
        # 转换路径分隔符
        user_path = user_path.replace('\\', '/')
        
        # 验证路径
        is_valid, message = config.validate_dll_path(user_path)
        
        if is_valid:
            # 保存配置
            config.set_dll_path(user_path)
            print(f"\n✓ 配置成功!")
            print(f"  DLL路径已设置为: {user_path}")
            print(f"  配置已保存到: {config.CONFIG_FILE}")
            print("\n现在可以正常使用 tdxuse 技能了!")
            break
        else:
            print(f"\n✗ 验证失败: {message}")
            print("请重新输入路径，或输入 'q' 退出:")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n操作已取消。")
        sys.exit(0)
    except Exception as e:
        print(f"\n错误: {e}")
        sys.exit(1)
