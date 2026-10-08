# -*- coding: utf-8 -*-
"""
期权数据获取示例脚本

演示AmazingData中与期权相关的所有接口。
包含：基础数据（含期权代码表）、行情数据、期权3个专属接口。
注意：所有接口调用前必须先调用 ad.login() 登录。
"""

import AmazingData as ad

# ============================================================
# 【必须】登录AmazingData - 所有接口调用前必须先登录
# 请提前设置以下环境变量：
#   AD_USERNAME     - 用户名
#   AD_PASSWORD - 密码
#   AMAZINGDATA_HOST     - 服务器IP
#   AD_PORT     - 服务器端口
# ============================================================
import os

ad.login(
    username=os.environ['AD_USERNAME'],
    password=os.environ['AD_PASSWORD'],
    host=os.environ['AMAZINGDATA_HOST'],
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

def get_option_code_list():
    """期权代码表 - 获取ETF期权代码列表"""
    option_codes = base_data.get_option_code_list(security_type='EXTRA_ETF_OP')
    print(f"获取到{len(option_codes)}只期权")
    print(option_codes[:10])
    return option_codes


def get_code_info():
    """每日最新证券信息"""
    code_info = base_data.get_code_info(security_type='EXTRA_STOCK_A')
    print(f"证券信息：{len(code_info)}条")
    print(code_info.head())
    return code_info


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
# 三、期权专属数据（InfoData）
# ============================================================

def get_option_basic_info(code_list, local_path='D://AmazingData_local_data//'):
    """期权基本资料"""
    option_info = info_data.get_option_basic_info(code_list)
    print(f"期权基本资料获取成功")
    print(option_info.head())
    return option_info


def get_option_std_ctr_specs(code_list, local_path='D://AmazingData_local_data//'):
    """期权标准合约属性"""
    specs = info_data.get_option_std_ctr_specs(code_list, local_path='D://AmazingData_local_data//')
    print(f"期权标准合约属性获取成功")
    print(specs.head())
    return specs


def get_option_mon_ctr_specs(code_list, local_path='D://AmazingData_local_data//'):
    """期权月合约属性变动"""
    mon_specs = info_data.get_option_mon_ctr_specs(code_list, local_path='D://AmazingData_local_data//')
    print(f"期权月合约属性变动获取成功")
    print(mon_specs.head())
    return mon_specs


# ============================================================
# 主函数 - 以ETF期权为例演示
# ============================================================
if __name__ == '__main__':
    option_list = get_option_code_list()
    option_codes = option_list[:5] if option_list else ['10005032.SH']

    print("=" * 60)
    print("一、基础数据")
    print("=" * 60)
    code_info = get_code_info()
    cal = get_calendar_data()

    print("=" * 60)
    print("二、行情数据")
    print("=" * 60)
    kline = get_kline_data(option_codes, 20240101, 20241231)
    snapshot = get_snapshot_data(option_codes, 20240101, 20241231)

    print("=" * 60)
    print("三、期权专属数据")
    print("=" * 60)
    option_info = get_option_basic_info(option_codes)
    option_specs = get_option_std_ctr_specs(option_codes)
    option_mon = get_option_mon_ctr_specs(option_codes)

    print("\n所有期权相关接口调用完成！")
