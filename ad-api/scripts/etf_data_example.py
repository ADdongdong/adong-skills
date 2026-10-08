# -*- coding: utf-8 -*-
"""
ETF数据获取示例脚本

演示AmazingData中与ETF相关的所有接口。
包含：基础数据、行情数据、ETF申赎清单、ETF基金份额、ETF IOPV、
      交易所指数、行业指数。
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
    """每日最新代码表 - 获取ETF代码列表"""
    # 手册示例：get_hist_code_list(security_type="EXTRA_ETF")
    code_list = base_data.get_hist_code_list(security_type="EXTRA_ETF", local_path='D://AmazingData_local_data//')
    print(f"获取到{len(code_list)}只ETF")
    print(code_list[:10])
    return code_list


def get_code_info():
    """每日最新证券信息"""
    code_info = base_data.get_code_info(security_type='EXTRA_ETF')
    print(f"ETF证券信息：{len(code_info)}条")
    print(code_info.head())
    return code_info


def get_backward_factor(code_list, local_path='D://AmazingData_local_data//', is_local=False):
    """复权因子 - 后复权因子"""
    factor = base_data.get_backward_factor(code_list)
    for code, df in factor.items():
        print(f"{code} 后复权因子：{len(df)}条")
        print(df.head())
    return factor


def get_hist_code_list():
    """历史代码表"""
    today = calendar[-1]
    hist_codes = base_data.get_hist_code_list(
        security_type='EXTRA_ETF',
        start_date=20130101,
        end_date=today
    )
    print(f"历史ETF代码：{len(hist_codes)}只")
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
# 三、ETF专属数据（BaseData + InfoData）
# ============================================================

def get_etf_pcf(code_list):
    """ETF申赎清单（BaseData）"""
    etf_pcf_info, etf_pcf_constituent = base_data.get_etf_pcf(code_list[:5])
    print(f"ETF申赎信息：{len(etf_pcf_info)}只")
    print(etf_pcf_info.head())
    return etf_pcf_info, etf_pcf_constituent


def get_etf_fund_share(code_list):
    """ETF基金份额（InfoData）"""
    share = info_data.get_fund_share(code_list[:5], is_local=False, local_path='D://AmazingData_local_data//')
    for code, df in share.items():
        print(f"{code} 份额数据：{len(df)}条")
        print(df.head())
    return share


def get_etf_iopv(code_list):
    """ETF每日收盘IOPV（InfoData）"""
    iopv = info_data.get_fund_iopv(code_list[:5], is_local=False, local_path='D://AmazingData_local_data//')
    for code, df in iopv.items():
        print(f"{code} IOPV数据：{len(df)}条")
        print(df.head())
    return iopv


# ============================================================
# 四、交易所指数数据（InfoData）
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
# 五、行业指数数据（InfoData）
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
# 主函数 - 以ETF(510300.SH 沪深300ETF)为例演示
# ============================================================
if __name__ == '__main__':
    etf_list = get_code_list()
    etf_codes = ['510300.SH']

    print("=" * 60)
    print("一、基础数据")
    print("=" * 60)
    code_info = get_code_info()
    backward_factor = get_backward_factor(etf_codes)
    hist_codes = get_hist_code_list()
    cal = get_calendar_data()

    print("=" * 60)
    print("二、行情数据")
    print("=" * 60)
    kline = get_kline_data(etf_codes, 20240101, 20241231)
    snapshot = get_snapshot_data(etf_codes, 20240101, 20241231)

    print("=" * 60)
    print("三、ETF专属数据")
    print("=" * 60)
    etf_pcf_info, etf_pcf_constituent = get_etf_pcf(etf_list)
    etf_share = get_etf_fund_share(etf_list)
    etf_iopv = get_etf_iopv(etf_list)

    print("=" * 60)
    print("四、交易所指数数据")
    print("=" * 60)
    index_constituent = get_index_constituent()
    index_weight = get_index_weight()

    print("=" * 60)
    print("五、行业指数数据")
    print("=" * 60)
    industry_info = get_industry_base_info()
    industry_constituent = get_industry_constituent(industry_codes)
    industry_weight = get_industry_weight(industry_codes)
    industry_daily = get_industry_daily(industry_codes)

    print("\n所有ETF相关接口调用完成！")
