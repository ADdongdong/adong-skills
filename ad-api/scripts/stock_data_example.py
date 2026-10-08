# -*- coding: utf-8 -*-
"""
股票数据获取示例脚本

演示AmazingData中与股票相关的所有接口。
包含：基础数据、行情数据、基础信息、财务数据、股东股本、分红配股、
      融资融券、交易异动、交易所指数、行业指数、债券(国债收益率)。
注意：所有接口调用前必须先调用 ad.login() 登录。
"""

import AmazingData as ad

# ============================================================
# 【必须】登录AmazingData - 所有接口调用前必须先登录
# 请提前设置以下环境变量：
#   AD_USERNAME     - 用户名
#   AD_PASSWORD - 密码
#   AD_HOST     - 服务器IP
#   AD_PORT     - 服务器端口
# ============================================================
import os

ad.login(
    username=os.environ['AD_USERNAME'],
    password=os.environ['AD_PASSWORD'],
    host=os.environ['AD_HOST'],
    port=int(os.environ['AD_PORT'])
)

# ============================================================
# 初始化三大数据对象
# ============================================================
base_data = ad.BaseData()
calendar = base_data.get_calendar()
market_data = ad.MarketData(calendar)
info_data = ad.InfoData()


# ============================================================
# 一、基础数据（BaseData）
# ============================================================

def get_code_list():
    """每日最新代码表 - 获取沪深北A股代码列表"""
    code_list = base_data.get_code_list(security_type='EXTRA_STOCK_A')
    print(f"获取到{len(code_list)}只A股")
    print(code_list[:10])
    return code_list


def get_code_info():
    """每日最新证券信息"""
    code_info = base_data.get_code_info(security_type='EXTRA_STOCK_A')
    print(f"证券信息：{len(code_info)}条")
    print(code_info.head())
    return code_info


def get_backward_factor(code_list, local_path='D://AmazingData_local_data//', is_local=False):
    """复权因子 - 后复权因子"""
    factor = base_data.get_backward_factor(code_list)
    for code, df in factor.items():
        print(f"{code} 后复权因子：{len(df)}条")
        print(df.head())
    return factor


def get_hist_code_list(local_path='D://AmazingData_local_data//'):
    """历史代码表"""
    today = calendar[-1]
    hist_codes = base_data.get_hist_code_list(
        security_type='EXTRA_STOCK_A',
        start_date=20130101,
        end_date=today
    )
    print(f"历史代码：{len(hist_codes)}只")
    return hist_codes


def get_calendar_data():
    """交易日历"""
    cal = base_data.get_calendar()
    print(f"交易日历：{len(cal)}个交易日")
    print(f"最近5个交易日：{cal[-5:]}")
    return cal


# ============================================================
# 二、行情数据（MarketData）
# ============================================================

def get_kline_data(code_list, begin_date, end_date):
    """历史K线数据"""
    kline_dict = market_data.query_kline(
        code_list=code_list,
        begin_date=begin_date,
        end_date=end_date,
        period=ad.constant.Period.day.value
    )
    for code, df in kline_dict.items():
        print(f"{code} K线数据：{len(df)}条")
        print(df.head())
    return kline_dict


def get_snapshot_data(code_list, begin_date, end_date):
    """历史快照数据"""
    snapshot_dict = market_data.query_snapshot(
        code_list=code_list,
        begin_date=begin_date,
        end_date=end_date
    )
    for code, df in snapshot_dict.items():
        print(f"{code} 快照数据：{len(df)}条")
        print(df.head())
    return snapshot_dict


# ============================================================
# 三、基础信息数据（InfoData）
# ============================================================

def get_stock_basic(code_list):
    """证券基础信息"""
    stock_basic = info_data.get_stock_basic(code_list)
    print(f"证券基础信息获取成功")
    print(stock_basic.head())
    return stock_basic


def get_history_stock_status(code_list, local_path='D://AmazingData_local_data//'):
    """历史证券信息"""
    status = info_data.get_history_stock_status(code_list)
    print(f"历史证券信息获取成功")
    print(status.head())
    return status


def get_bj_code_mapping(local_path='D://AmazingData_local_data//'):
    """北交所代码对照"""
    mapping = info_data.get_bj_code_mapping()
    print(f"北交所代码对照：{len(mapping)}条")
    print(mapping.head())
    return mapping


# ============================================================
# 四、财务数据（InfoData）
# ============================================================

def get_balance_sheet(code_list, local_path='D://AmazingData_local_data//'):
    """资产负债表"""
    balance = info_data.get_balance_sheet(code_list)
    print(f"资产负债表获取成功")
    print(balance.head())
    return balance


def get_cash_flow(code_list, local_path='D://AmazingData_local_data//'):
    """现金流量表"""
    cash = info_data.get_cash_flow(code_list)
    print(f"现金流量表获取成功")
    print(cash.head())
    return cash


def get_income(code_list, local_path='D://AmazingData_local_data//'):
    """利润表"""
    income = info_data.get_income(code_list)
    print(f"利润表获取成功")
    print(income.head())
    return income


def get_profit_express(code_list, local_path='D://AmazingData_local_data//'):
    """业绩快报"""
    express = info_data.get_profit_express(code_list)
    print(f"业绩快报获取成功")
    print(express.head())
    return express


def get_profit_notice(code_list, local_path='D://AmazingData_local_data//'):
    """业绩预告"""
    notice = info_data.get_profit_notice(code_list)
    print(f"业绩预告获取成功")
    print(notice.head())
    return notice


# ============================================================
# 五、股东股本数据（InfoData）
# ============================================================

def get_share_holder(code_list, local_path='D://AmazingData_local_data//'):
    """十大股东"""
    holders = info_data.get_share_holder(code_list)
    print(f"十大股东获取成功")
    print(holders.head())
    return holders


def get_holder_num(code_list, local_path='D://AmazingData_local_data//'):
    """股东户数"""
    holder_num = info_data.get_holder_num(code_list)
    print(f"股东户数获取成功")
    print(holder_num.head())
    return holder_num


def get_equity_structure(code_list, local_path='D://AmazingData_local_data//'):
    """股本结构"""
    equity = info_data.get_equity_structure(code_list)
    print(f"股本结构获取成功")
    print(equity.head())
    return equity


def get_equity_pledge_freeze(code_list, local_path='D://AmazingData_local_data//'):
    """股权冻结质押"""
    pledge = info_data.get_equity_pledge_freeze(code_list)
    print(f"股权冻结质押获取成功")
    print(pledge.head())
    return pledge


def get_equity_restricted(code_list, local_path='D://AmazingData_local_data//'):
    """限售股解禁"""
    restricted = info_data.get_equity_restricted(code_list)
    print(f"限售股解禁获取成功")
    print(restricted.head())
    return restricted


# ============================================================
# 六、股东权益数据（InfoData）
# ============================================================

def get_dividend(code_list, local_path='D://AmazingData_local_data//'):
    """分红数据"""
    dividend = info_data.get_dividend(code_list)
    print(f"分红数据获取成功")
    print(dividend.head())
    return dividend


def get_right_issue(code_list, local_path='D://AmazingData_local_data//'):
    """配股数据"""
    right_issue = info_data.get_right_issue(code_list)
    print(f"配股数据获取成功")
    print(right_issue.head())
    return right_issue


# ============================================================
# 七、融资融券数据（InfoData）
# ============================================================

def get_margin_summary(code_list):
    """融资融券汇总"""
    margin = info_data.get_margin_summary(code_list, is_local=False)
    print(f"融资融券汇总获取成功")
    print(margin.head())
    return margin


def get_margin_detail(code_list, local_path='D://AmazingData_local_data//'):
    """融资融券明细"""
    detail = info_data.get_margin_detail(code_list, is_local=False)
    print(f"融资融券明细获取成功")
    print(detail.head())
    return detail


# ============================================================
# 八、交易异动数据（InfoData）
# ============================================================

def get_long_hu_bang(code_list, local_path='D://AmazingData_local_data//'):
    """龙虎榜"""
    lhb = info_data.get_long_hu_bang(code_list, is_local=False)
    print(f"龙虎榜获取成功")
    print(lhb.head())
    return lhb


def get_block_trading(code_list, local_path='D://AmazingData_local_data//'):
    """大宗交易"""
    block = info_data.get_block_trading(code_list, is_local=False)
    print(f"大宗交易获取成功")
    print(block.head())
    return block


# ============================================================
# 九、交易所指数数据（InfoData）
# ============================================================

def get_index_constituent(local_path='D://AmazingData_local_data//'):
    """交易所指数成分股"""
    constituent = info_data.get_index_constituent(['000300.SH'])
    print(f"指数成分股获取成功")
    print(constituent.head())
    return constituent


def get_index_weight(local_path='D://AmazingData_local_data//'):
    """交易所指数成分股日权重"""
    weight = info_data.get_index_weight(['000300.SH'], is_local=False)
    print(f"指数成分股日权重获取成功")
    print(weight.head())
    return weight


# ============================================================
# 十、行业指数数据（InfoData）
# ============================================================

def get_industry_base_info(local_path='D://AmazingData_local_data//'):
    """行业指数基本信息"""
    industry_info = info_data.get_industry_base_info()
    print(f"行业指数基本信息获取成功")
    print(industry_info.head())
    return industry_info


def get_industry_constituent(code_list, local_path='D://AmazingData_local_data//'):
    """行业指数成分股"""
    constituent = info_data.get_industry_constituent(code_list, local_path='D://AmazingData_local_data//')
    print(f"行业指数成分股获取成功")
    print(constituent.head())
    return constituent


def get_industry_weight(code_list, local_path='D://AmazingData_local_data//'):
    """行业指数成分股日权重"""
    weight = info_data.get_industry_weight(code_list, local_path='D://AmazingData_local_data//', is_local=False)
    print(f"行业指数成分股日权重获取成功")
    print(weight.head())
    return weight


def get_industry_daily(code_list, local_path='D://AmazingData_local_data//'):
    """行业指数日行情"""
    daily = info_data.get_industry_daily(code_list, local_path='D://AmazingData_local_data//', is_local=False)
    print(f"行业指数日行情获取成功")
    print(daily.head())
    return daily


# ============================================================
# 十一、债券数据（InfoData）
# ============================================================

def get_treasury_yield(local_path='D://AmazingData_local_data//'):
    """国债收益率"""
    yields = info_data.get_treasury_yield(['m3', 'm6', 'y1', 'y2', 'y3', 'y5', 'y7', 'y10', 'y30'])
    print(f"国债收益率获取成功")
    print(yields.head())
    return yields


# ============================================================
# 主函数 - 以股票(000***.SZ)为例演示
# ============================================================
if __name__ == '__main__':
    stock_codes = ['000***.SZ']

    print("=" * 60)
    print("一、基础数据")
    print("=" * 60)
    code_list = get_code_list()
    code_info = get_code_info()
    backward_factor = get_backward_factor(stock_codes)
    hist_codes = get_hist_code_list()
    cal = get_calendar_data()

    print("=" * 60)
    print("二、行情数据")
    print("=" * 60)
    kline = get_kline_data(stock_codes, 20240101, 20241231)
    snapshot = get_snapshot_data(stock_codes, 20240101, 20241231)

    print("=" * 60)
    print("三、基础信息数据")
    print("=" * 60)
    stock_basic = get_stock_basic(stock_codes)
    history_status = get_history_stock_status(stock_codes)
    bj_mapping = get_bj_code_mapping()

    print("=" * 60)
    print("四、财务数据")
    print("=" * 60)
    balance = get_balance_sheet(stock_codes)
    cash = get_cash_flow(stock_codes)
    income = get_income(stock_codes)
    express = get_profit_express(stock_codes)
    notice = get_profit_notice(stock_codes)

    print("=" * 60)
    print("五、股东股本数据")
    print("=" * 60)
    holders = get_share_holder(stock_codes)
    holder_num = get_holder_num(stock_codes)
    equity = get_equity_structure(stock_codes)
    pledge = get_equity_pledge_freeze(stock_codes)
    restricted = get_equity_restricted(stock_codes)

    print("=" * 60)
    print("六、股东权益数据")
    print("=" * 60)
    dividend = get_dividend(stock_codes)
    right_issue = get_right_issue(stock_codes)

    print("=" * 60)
    print("七、融资融券数据")
    print("=" * 60)
    margin_summary = get_margin_summary(stock_codes)
    margin_detail = get_margin_detail(stock_codes)

    print("=" * 60)
    print("八、交易异动数据")
    print("=" * 60)
    lhb = get_long_hu_bang(stock_codes)
    block = get_block_trading(stock_codes)

    print("=" * 60)
    print("九、交易所指数数据")
    print("=" * 60)
    index_constituent = get_index_constituent()
    index_weight = get_index_weight()

    print("=" * 60)
    print("十、行业指数数据")
    print("=" * 60)
    industry_info = get_industry_base_info()
    industry_constituent = get_industry_constituent(industry_codes)
    industry_weight = get_industry_weight(industry_codes)
    industry_daily = get_industry_daily(industry_codes)

    print("=" * 60)
    print("十一、债券数据")
    print("=" * 60)
    treasury = get_treasury_yield()

    print("\n所有股票相关接口调用完成！")
