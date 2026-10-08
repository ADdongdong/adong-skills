"""
行情客户端封装模块
提供实时行情、K线数据、指数数据、分钟数据的获取功能
"""

import subprocess
import sys
import pandas as pd
from retry import retry
import mootdx
from mootdx.quotes import Quotes
from mootdx.exceptions import MootdxException


def ensure_best_ip():
    """
    自动优选最快行情服务器
    """
    try:
        subprocess.run(
            [sys.executable, "-m", "mootdx", "bestip", "-v"],
            check=True,
            timeout=30,
            capture_output=True,
            text=True
        )
        return True
    except subprocess.TimeoutExpired:
        print("[警告] 优选服务器超时，将使用默认配置")
        return False
    except subprocess.CalledProcessError as e:
        print(f"[警告] 优选服务器失败: {e.stderr}，将使用默认配置")
        return False
    except Exception as e:
        print(f"[警告] 优选服务器时发生未知错误: {e}")
        return False


def df_to_markdown(df: pd.DataFrame, title: str = "") -> str:
    """将DataFrame转换为Markdown表格"""
    if df is None or df.empty:
        return "暂无数据"
    md = f"{title}\n\n" if title else ""
    md += df.to_markdown(index=False) if hasattr(df, 'to_markdown') else df.to_string(index=False)
    return md


def _get_client():
    """创建并返回行情客户端实例"""
    # 自动优选服务器
    ensure_best_ip()
    return Quotes.factory(
        market='std',
        multithread=True,
        heartbeat=True,
        timeout=15
    )


@retry(exceptions=(MootdxException, ConnectionError, TimeoutError), tries=3, delay=1, backoff=2)
def get_quotes(symbol: str) -> str:
    """
    获取实时行情快照
    :param symbol: 股票/指数/期货代码，如 '600519'
    :return: Markdown格式的行情数据
    """
    client = None
    try:
        client = _get_client()
        data = client.quotes(symbol=symbol)
        if data is None or data.empty:
            return f"未找到代码 {symbol} 的行情数据"

        # 提取关键字段
        key_fields = ['code', 'name', 'open', 'price', 'high', 'low', 'volume']
        available_fields = [f for f in key_fields if f in data.columns]
        result_df = data[available_fields].copy()
        result_df.columns = ['代码', '名称', '开盘价', '最新价', '最高价', '最低价', '成交量']

        summary = f"已成功获取 {symbol} 的实时行情"
        return df_to_markdown(result_df, summary)
    except MootdxException as e:
        return f"获取行情数据失败: {e}\n建议稍后重试或运行 'mootdx bestip -v' 更新服务器列表"
    except Exception as e:
        return f"未知错误: {e}"
    finally:
        if client:
            client.close()


@retry(exceptions=(MootdxException, ConnectionError, TimeoutError), tries=3, delay=1, backoff=2)
def get_kline(symbol: str, frequency: int = 9, offset: int = 0, count: int = 10) -> str:
    """
    获取历史K线数据
    :param symbol: 股票/指数代码
    :param frequency: K线周期，参考 frequency-mapping.md
    :param offset: 起始偏移（0表示最新）
    :param count: 获取数量
    :return: Markdown格式的K线数据
    """
    client = None
    try:
        client = _get_client()
        data = client.bars(symbol=symbol, frequency=frequency, offset=offset, size=count)
        if data is None or data.empty:
            return f"未找到代码 {symbol} 的历史K线数据"

        # 设置时间列为索引并格式化
        if 'datetime' in data.columns:
            data['datetime'] = pd.to_datetime(data['datetime'])
            data.set_index('datetime', inplace=True)

        summary = f"已成功获取 {symbol} 的K线数据（周期:{frequency}，数量:{len(data)}）"
        return df_to_markdown(data.reset_index(), summary)
    except MootdxException as e:
        return f"获取K线数据失败: {e}"
    except Exception as e:
        return f"未知错误: {e}"
    finally:
        if client:
            client.close()


@retry(exceptions=(MootdxException, ConnectionError, TimeoutError), tries=3, delay=1, backoff=2)
def get_index(symbol: str) -> str:
    """
    获取指数数据
    :param symbol: 指数代码，如 '000001'（上证指数）
    :return: Markdown格式的指数数据
    """
    client = None
    try:
        client = _get_client()
        data = client.index(symbol=symbol)
        if data is None or data.empty:
            return f"未找到指数 {symbol} 的数据"

        summary = f"已成功获取指数 {symbol} 的数据"
        return df_to_markdown(data, summary)
    except MootdxException as e:
        return f"获取指数数据失败: {e}"
    except Exception as e:
        return f"未知错误: {e}"
    finally:
        if client:
            client.close()


@retry(exceptions=(MootdxException, ConnectionError, TimeoutError), tries=3, delay=1, backoff=2)
def get_minute(symbol: str) -> str:
    """
    获取分钟数据（当日分时）
    :param symbol: 股票/指数代码
    :return: Markdown格式的分钟数据
    """
    client = None
    try:
        client = _get_client()
        data = client.minute(symbol=symbol)
        if data is None or data.empty:
            return f"未找到代码 {symbol} 的分钟数据"

        summary = f"已成功获取 {symbol} 的分钟数据"
        return df_to_markdown(data, summary)
    except MootdxException as e:
        return f"获取分钟数据失败: {e}"
    except Exception as e:
        return f"未知错误: {e}"
    finally:
        if client:
            client.close()


# 为了兼容直接调用
if __name__ == "__main__":
    print(get_quotes("600519"))
