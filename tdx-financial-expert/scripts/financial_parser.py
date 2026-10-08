"""
财务数据解析器模块
提供资产负债表、利润表、现金流量表数据获取
"""

from mootdx.affair import Affair


def _infer_market(symbol: str) -> str:
    """
    根据股票代码推断市场
    :param symbol: 股票代码
    :return: 市场代码 'sh' 或 'sz'
    """
    if symbol.startswith(('6', '5', '9')):
        return 'sh'
    elif symbol.startswith(('0', '3', '2')):
        return 'sz'
    else:
        return 'sh'  # 默认上海


def get_balance_sheet(symbol: str) -> str:
    """
    获取资产负债表
    :param symbol: 股票代码
    :return: Markdown格式的资产负债表数据
    """
    try:
        market = _infer_market(symbol)
        affair = Affair()
        data = affair.fetch_balance(symbol=symbol, market=market)
        if data is None or data.empty:
            return f"未找到 {symbol} 的资产负债表数据"

        summary = f"已成功获取 {symbol} 的资产负债表"
        return summary + "\n\n" + data.to_markdown() if hasattr(data, 'to_markdown') else data.to_string()
    except Exception as e:
        return f"获取资产负债表失败: {e}"


def get_profit_statement(symbol: str) -> str:
    """
    获取利润表
    :param symbol: 股票代码
    :return: Markdown格式的利润表数据
    """
    try:
        market = _infer_market(symbol)
        affair = Affair()
        data = affair.fetch_income(symbol=symbol, market=market)
        if data is None or data.empty:
            return f"未找到 {symbol} 的利润表数据"

        summary = f"已成功获取 {symbol} 的利润表"
        return summary + "\n\n" + data.to_markdown() if hasattr(data, 'to_markdown') else data.to_string()
    except Exception as e:
        return f"获取利润表失败: {e}"


def get_cash_flow(symbol: str) -> str:
    """
    获取现金流量表
    :param symbol: 股票代码
    :return: Markdown格式的现金流量表数据
    """
    try:
        market = _infer_market(symbol)
        affair = Affair()
        data = affair.fetch_cashflow(symbol=symbol, market=market)
        if data is None or data.empty:
            return f"未找到 {symbol} 的现金流量表数据"

        summary = f"已成功获取 {symbol} 的现金流量表"
        return summary + "\n\n" + data.to_markdown() if hasattr(data, 'to_markdown') else data.to_string()
    except Exception as e:
        return f"获取现金流量表失败: {e}"


if __name__ == "__main__":
    print(get_balance_sheet("600519"))
