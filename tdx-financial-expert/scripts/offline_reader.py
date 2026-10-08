"""
本地数据读取器模块
支持从通达信安装目录读取日线和分钟线数据
"""

import os
import pandas as pd
from mootdx.reader import Reader


def _check_tdx_path(tdx_path: str) -> bool:
    """检查通达信路径是否有效"""
    if not os.path.exists(tdx_path):
        return False
    # 检查是否存在典型的数据目录
    data_dirs = ['vipdoc', 'T0002', 'gpcw']
    return any(os.path.exists(os.path.join(tdx_path, d)) for d in data_dirs)


def get_daily(tdx_path: str, symbol: str) -> str:
    """
    读取本地日线数据
    :param tdx_path: 通达信安装目录路径
    :param symbol: 股票/指数代码
    :return: Markdown格式的日线数据
    """
    if not _check_tdx_path(tdx_path):
        return f"错误: 通达信路径 '{tdx_path}' 无效或不存在。请确认路径是否正确，例如 'D:/new_tdx'"

    try:
        reader = Reader.factory(market='std', tdxdir=tdx_path)
        data = reader.daily(symbol=symbol)
        if data is None or data.empty:
            return f"未在本地找到代码 {symbol} 的日线数据，请确认已下载数据或代码正确"

        summary = f"已成功从本地读取 {symbol} 的日线数据"
        # 将DataFrame转换为Markdown
        return summary + "\n\n" + data.to_markdown() if hasattr(data, 'to_markdown') else data.to_string()
    except Exception as e:
        return f"读取本地日线数据失败: {e}"


def get_minute(tdx_path: str, symbol: str, suffix: str = "1min") -> str:
    """
    读取本地分钟线数据
    :param tdx_path: 通达信安装目录路径
    :param symbol: 股票/指数代码
    :param suffix: 文件后缀，如 '1min', '5min'
    :return: Markdown格式的分钟线数据
    """
    if not _check_tdx_path(tdx_path):
        return f"错误: 通达信路径 '{tdx_path}' 无效或不存在。"

    try:
        reader = Reader.factory(market='std', tdxdir=tdx_path)
        data = reader.minute(symbol=symbol, suffix=suffix)
        if data is None or data.empty:
            return f"未在本地找到代码 {symbol} 的{suffix}数据"

        summary = f"已成功从本地读取 {symbol} 的{suffix}数据"
        return summary + "\n\n" + data.to_markdown() if hasattr(data, 'to_markdown') else data.to_string()
    except Exception as e:
        return f"读取本地分钟数据失败: {e}"


if __name__ == "__main__":
    # 示例用法
    print(get_daily("D:/new_tdx", "600519"))
