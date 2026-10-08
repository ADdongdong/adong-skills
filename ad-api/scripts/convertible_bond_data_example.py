# -*- coding: utf-8 -*-
"""
可转债数据获取示例脚本

演示AmazingData中与可转债相关的所有接口。
包含：基础数据、行情数据、可转债11个专属接口、债券(国债收益率)。
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
    """每日最新代码表 - 获取可转债代码列表"""
    code_list = base_data.get_code_list(security_type='EXTRA_KZZ')
    print(f"获取到{len(code_list)}只可转债")
    print(code_list[:10])
    return code_list


def get_code_info():
    """每日最新证券信息"""
    code_info = base_data.get_code_info(security_type='EXTRA_KZZ')
    print(f"可转债证券信息：{len(code_info)}条")
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
        security_type='EXTRA_KZZ',
        start_date=20130101,
        end_date=today
    )
    print(f"历史可转债代码：{len(hist_codes)}只")
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
# 三、可转债专属数据（InfoData）
# ============================================================

def get_kzz_issuance(code_list, local_path='D://AmazingData_local_data//'):
    """可转债发行"""
    issuance = info_data.get_kzz_issuance(code_list, is_local=False)
    print(f"可转债发行获取成功")
    print(issuance.head())
    return issuance


def get_kzz_share(code_list, local_path='D://AmazingData_local_data//'):
    """可转债份额"""
    share = info_data.get_kzz_share(code_list, is_local=False)
    print(f"可转债份额获取成功")
    print(share.head())
    return share


def get_kzz_conv(code_list, local_path='D://AmazingData_local_data//'):
    """可转债转股"""
    conv = info_data.get_kzz_conv(code_list, is_local=False)
    print(f"可转债转股获取成功")
    print(conv.head())
    return conv


def get_kzz_conv_change(code_list, local_path='D://AmazingData_local_data//'):
    """可转债转股变动"""
    change = info_data.get_kzz_conv_change(code_list, is_local=False)
    print(f"可转债转股变动获取成功")
    print(change.head())
    return change


def get_kzz_corr(code_list, local_path='D://AmazingData_local_data//'):
    """可转债修正"""
    corr = info_data.get_kzz_corr(code_list, is_local=False)
    print(f"可转债修正获取成功")
    print(corr.head())
    return corr


def get_kzz_call(code_list, local_path='D://AmazingData_local_data//'):
    """可转债赎回"""
    call = info_data.get_kzz_call(code_list, is_local=False)
    print(f"可转债赎回获取成功")
    print(call.head())
    return call


def get_kzz_put(code_list, local_path='D://AmazingData_local_data//'):
    """可转债回售"""
    put = info_data.get_kzz_put(code_list, is_local=False)
    print(f"可转债回售获取成功")
    print(put.head())
    return put


def get_kzz_put_call_item(code_list, local_path='D://AmazingData_local_data//'):
    """可转债回售赎回条款"""
    item = info_data.get_kzz_put_call_item(code_list, is_local=False)
    print(f"可转债回售赎回条款获取成功")
    print(item.head())
    return item


def get_kzz_put_explanation(code_list, local_path='D://AmazingData_local_data//'):
    """可转债回售条款执行说明"""
    explanation = info_data.get_kzz_put_explanation(code_list, is_local=False)
    print(f"可转债回售条款执行说明获取成功")
    print(explanation.head())
    return explanation


def get_kzz_call_explanation(code_list, local_path='D://AmazingData_local_data//'):
    """可转债赎回条款执行说明"""
    explanation = info_data.get_kzz_call_explanation(code_list, is_local=False)
    print(f"可转债赎回条款执行说明获取成功")
    print(explanation.head())
    return explanation


def get_kzz_suspend(code_list, local_path='D://AmazingData_local_data//'):
    """可转债停复牌"""
    suspend = info_data.get_kzz_suspend(code_list, is_local=False)
    print(f"可转债停复牌获取成功")
    print(suspend.head())
    return suspend


# ============================================================
# 四、债券数据（InfoData）
# ============================================================

def get_treasury_yield(local_path='D://AmazingData_local_data//'):
    """国债收益率"""
    yields = info_data.get_treasury_yield(['m3', 'm6', 'y1', 'y2', 'y3', 'y5', 'y7', 'y10', 'y30'])
    print(f"国债收益率获取成功")
    print(yields.head())
    return yields


# ============================================================
# 主函数 - 以可转债(113***.SH)为例演示
# ============================================================
if __name__ == '__main__':
    kzz_list = get_code_list()
    kzz_codes = ['113***.SH']

    print("=" * 60)
    print("一、基础数据")
    print("=" * 60)
    code_info = get_code_info()
    backward_factor = get_backward_factor(kzz_codes)
    hist_codes = get_hist_code_list()
    cal = get_calendar_data()

    print("=" * 60)
    print("二、行情数据")
    print("=" * 60)
    kline = get_kline_data(kzz_codes, 20240101, 20241231)
    snapshot = get_snapshot_data(kzz_codes, 20240101, 20241231)

    print("=" * 60)
    print("三、可转债专属数据")
    print("=" * 60)
    kzz_issuance = get_kzz_issuance(kzz_list[:10])
    kzz_share = get_kzz_share(kzz_list[:10])
    kzz_conv = get_kzz_conv(kzz_list[:10])
    kzz_conv_change = get_kzz_conv_change(kzz_list[:10])
    kzz_corr = get_kzz_corr(kzz_list[:10])
    kzz_call = get_kzz_call(kzz_list[:10])
    kzz_put = get_kzz_put(kzz_list[:10])
    kzz_put_call_item = get_kzz_put_call_item(kzz_list[:10])
    kzz_put_explanation = get_kzz_put_explanation(kzz_list[:10])
    kzz_call_explanation = get_kzz_call_explanation(kzz_list[:10])
    kzz_suspend = get_kzz_suspend(kzz_list[:10])

    print("=" * 60)
    print("四、债券数据")
    print("=" * 60)
    treasury = get_treasury_yield()

    print("\n所有可转债相关接口调用完成！")
