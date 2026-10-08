# -*- coding: utf-8 -*-
"""
A股基本面指标分析脚本（修改版，自包含版本）

前置条件 - 设置环境变量:
    set AD_USERNAME=your_username
    set AD_PASSWORD=your_password
    set AD_HOST=server_ip
    set AD_PORT=8600

用法:
    python run_fundamental_analysis.py 60****.SH
    python run_fundamental_analysis.py 60****.SH --category profitability
    python run_fundamental_analysis.py 60****.SH --category valuation --begin 20200101 --end 20260321
    python run_fundamental_analysis.py 60****.SH --factor 净资产收益率TTM
    python run_fundamental_analysis.py --list

参数:
    code: 股票代码 (如 60****.SH, 000001.SZ)
    --begin: K线开始日期 (默认: 20200101, 用于日频指标)
    --end: K线结束日期 (默认: 今天)
    --category: 指标类别 (profitability/growth/efficiency/earnings_quality/safety/governance/valuation/shareholder/size/all)
    --factor: 单个指标名称 (如 净资产收益率TTM, 市盈率TTM)
    --list: 列出所有可用指标
    --output: 输出格式 (json/table, 默认json)
"""

import sys
import os
import argparse
import json
import warnings
from datetime import datetime

warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import AmazingData as ad


# ================================================================
#  辅助函数（内联自 fundamental_factors.py）
# ================================================================

def safe_div(a, b):
    """安全除法，分母为0或NaN时返回NaN"""
    a = pd.Series(a).values.astype(float) if not isinstance(a, np.ndarray) else a.astype(float)
    b = pd.Series(b).values.astype(float) if not isinstance(b, np.ndarray) else b.astype(float)
    with np.errstate(divide='ignore', invalid='ignore'):
        result = np.where((b == 0) | np.isnan(b) | np.isnan(a), np.nan, a / b)
    return result


def get_ttm(df, field):
    """计算TTM（滚动12个月累计值）
    Q1报告期: TTM = Q1本期 + 去年年报 - 去年Q1
    Q2报告期: TTM = Q2本期 + 去年年报 - 去年Q2
    Q3报告期: TTM = Q3本期 + 去年年报 - 去年Q3
    Q4报告期(年报): TTM = 年报值
    """
    if df is None or df.empty or field not in df.columns:
        return pd.Series(dtype=float)
    df = df.sort_values('REPORTING_PERIOD').reset_index(drop=True)
    rp = df['REPORTING_PERIOD'].astype(str)
    result = pd.Series(np.nan, index=df.index)
    for i in range(len(df)):
        val = df[field].iloc[i]
        if pd.isna(val):
            continue
        rp_str = rp.iloc[i]
        yr = rp_str[:4]
        mmdd = rp_str[4:]
        if mmdd == '1231':
            result.iloc[i] = val
        else:
            prev_yr = str(int(yr) - 1)
            ann_mask = rp == prev_yr + '1231'
            same_mask = rp == prev_yr + mmdd
            if ann_mask.any() and same_mask.any():
                ann_val = df.loc[ann_mask, field].iloc[-1]
                same_val = df.loc[same_mask, field].iloc[-1]
                if pd.notna(ann_val) and pd.notna(same_val):
                    result.iloc[i] = val + ann_val - same_val
    return result


def get_single_quarter(df, field):
    """计算单季度值
    Q1: 直接取值
    Q2: Q2累计 - Q1累计
    Q3: Q3累计 - Q2累计
    Q4: Q4累计(年报) - Q3累计
    """
    if df is None or df.empty or field not in df.columns:
        return pd.Series(dtype=float)
    df = df.sort_values('REPORTING_PERIOD').reset_index(drop=True)
    rp = df['REPORTING_PERIOD'].astype(str)
    result = pd.Series(np.nan, index=df.index)
    prev_map = {'0630': '0331', '0930': '0630', '1231': '0930'}
    for i in range(len(df)):
        val = df[field].iloc[i]
        rp_str = rp.iloc[i]
        mmdd = rp_str[4:]
        if mmdd == '0331':
            result.iloc[i] = val
        elif mmdd in prev_map and pd.notna(val):
            yr = rp_str[:4]
            prev_rp = yr + prev_map[mmdd]
            prev_mask = rp == prev_rp
            if prev_mask.any():
                prev_val = df.loc[prev_mask, field].iloc[-1]
                if pd.notna(prev_val):
                    result.iloc[i] = val - prev_val
    return result


def _yoy(s):
    """同比增速（与4个季度前比较）。
    按 REPORTING_PERIOD 索引匹配去年同期，而非盲目 shift(4)。
    分母取绝对值以正确处理负值基期（亏损转盈利等）。
    """
    if not isinstance(s.index, pd.Index) or s.empty:
        return s
    rp = s.index.astype(str)
    result = pd.Series(np.nan, index=s.index)
    # 构建 REPORTING_PERIOD → 去年同期 的映射
    rp_to_val = dict(zip(rp, s.values))
    for i, rp_str in enumerate(rp):
        if len(rp_str) < 8:
            continue
        try:
            prev_rp = str(int(rp_str[:4]) - 1) + rp_str[4:]
        except (ValueError, IndexError):
            continue
        if prev_rp in rp_to_val:
            cur = s.values[i]
            prev = rp_to_val[prev_rp]
            if pd.notna(cur) and pd.notna(prev) and prev != 0:
                result.iloc[i] = (cur - prev) / abs(prev)
    return result


def _qoq(s):
    """环比增速（与上一季度比较）。
    按 REPORTING_PERIOD 索引匹配上一季度。
    分母取绝对值以正确处理负值基期。
    """
    if not isinstance(s.index, pd.Index) or s.empty:
        return s
    prev_map = {'0331': '1231', '0630': '0331', '0930': '0630', '1231': '0930'}
    rp = s.index.astype(str)
    result = pd.Series(np.nan, index=s.index)
    rp_to_val = dict(zip(rp, s.values))
    for i, rp_str in enumerate(rp):
        if len(rp_str) < 8:
            continue
        mmdd = rp_str[4:]
        if mmdd not in prev_map:
            continue
        yr = rp_str[:4]
        prev_mmdd = prev_map[mmdd]
        prev_yr = str(int(yr) - 1) if mmdd == '0331' else yr
        prev_rp = prev_yr + prev_mmdd
        if prev_rp in rp_to_val:
            cur = s.values[i]
            prev = rp_to_val[prev_rp]
            if pd.notna(cur) and pd.notna(prev) and prev != 0:
                result.iloc[i] = (cur - prev) / abs(prev)
    return result


def _ttm_yoy(s):
    """TTM同比增速（与去年同期TTM比较）。
    按 REPORTING_PERIOD 匹配，分母取绝对值。
    """
    return _yoy(s)


def _avg_bs(series):
    """计算期初期末平均值（用于资产、权益等存量科目的分母）。
    对齐到报告期索引，avg = (期初 + 期末) / 2。
    期初 = 上一报告期末值。首期无法计算平均时直接用期末值。
    """
    prev = series.shift(1)
    avg = (prev + series) / 2
    # 首期无前值时回退到期末值
    avg = avg.where(prev.notna(), series)
    return avg


def _safe_diff(series, rp_index):
    """安全差分：检查相邻报告期间隔是否为一个季度（~90天），否则返回NaN。
    series: 待差分的Series, index为REPORTING_PERIOD
    rp_index: 报告期索引（与series.index相同）
    """
    result = series.copy()
    rp_dt = pd.to_datetime(rp_index)
    for i in range(len(result)):
        if i == 0:
            result.iloc[i] = np.nan
            continue
        delta = (rp_dt[i] - rp_dt[i - 1]).days
        # 允许约一个季度的报告期间隔。
        if 75 <= delta <= 110:
            prev_val = series.iloc[i - 1]
            cur_val = series.iloc[i]
            if pd.notna(cur_val) and pd.notna(prev_val):
                result.iloc[i] = cur_val - prev_val
            else:
                result.iloc[i] = np.nan
        else:
            result.iloc[i] = np.nan
    return result


def _filter_statements(df):
    """过滤财务报表：只保留合并报表（STATEMENT_TYPE='1'），同一报告期取最新记录。
    REPORT_TYPE含义: 1=Q1, 2=半年报, 3=Q3, 4=年报，均需保留。
    """
    if df is None or df.empty:
        return df
    mask = pd.Series(True, index=df.index)
    if 'STATEMENT_TYPE' in df.columns:
        st = df['STATEMENT_TYPE'].astype(str)
        mask &= st == '1'
    filtered = df[mask].copy()
    if filtered.empty:
        return df
    # 同一报告期保留最新公告日（更正报表优先）
    if 'ACTUAL_ANN_DATE' in filtered.columns and 'REPORTING_PERIOD' in filtered.columns:
        filtered = filtered.sort_values(['REPORTING_PERIOD', 'ACTUAL_ANN_DATE'])
        filtered = filtered.drop_duplicates('REPORTING_PERIOD', keep='last')
    return filtered


def _prep(bs, inc, cf):
    """预处理三表：过滤、排序、去重，返回副本避免污染原始数据"""
    bs = _filter_statements(bs).copy()
    inc = _filter_statements(inc).copy()
    cf = _filter_statements(cf).copy()
    bs = bs.sort_values('REPORTING_PERIOD').drop_duplicates('REPORTING_PERIOD', keep='last').reset_index(drop=True)
    inc = inc.sort_values('REPORTING_PERIOD').drop_duplicates('REPORTING_PERIOD', keep='last').reset_index(drop=True)
    cf = cf.sort_values('REPORTING_PERIOD').drop_duplicates('REPORTING_PERIOD', keep='last').reset_index(drop=True)
    return bs, inc, cf


def _safe_col(df, col, default=np.nan):
    """安全获取列，不存在则返回默认值"""
    if col in df.columns:
        return df[col].astype(float)
    return pd.Series(default, index=df.index)


def _pit_fill(fin_df, field, trade_dates):
    """Point-in-time前向填充：将季频财务字段按公告日映射到每个交易日。
    使用 ACTUAL_ANN_DATE 作为时间索引，避免未来函数。
    fin_df 需含 ACTUAL_ANN_DATE 和目标字段列。
    返回 Series, index=trade_dates。
    """
    if fin_df is None or fin_df.empty or field not in fin_df.columns:
        return pd.Series(np.nan, index=trade_dates)
    df = fin_df.copy()
    # 优先使用公告日，若无则回退到报告期
    if 'ACTUAL_ANN_DATE' in df.columns:
        date_col = 'ACTUAL_ANN_DATE'
    else:
        date_col = 'REPORTING_PERIOD'
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.dropna(subset=[date_col, field])
    df = df.sort_values(date_col)
    # 同一公告日保留最后一条（对应最新报告期）
    s = df.set_index(date_col)[field].astype(float)
    s = s[~s.index.duplicated(keep='last')].sort_index()
    return s.reindex(trade_dates, method='ffill')


def _equity_pit(equity_structure, code, field, trade_dates):
    """将股本结构按 CHANGE_DATE 前向填充到交易日。"""
    if equity_structure is None or equity_structure.empty:
        return pd.Series(np.nan, index=trade_dates)
    eq = equity_structure[equity_structure['MARKET_CODE'] == code].copy()
    if eq.empty or field not in eq.columns:
        return pd.Series(np.nan, index=trade_dates)
    eq = eq.sort_values('CHANGE_DATE').drop_duplicates('CHANGE_DATE', keep='last')
    s = eq.set_index('CHANGE_DATE')[field].astype(float)
    s.index = pd.to_datetime(s.index)
    s = s[~s.index.duplicated(keep='last')].sort_index()
    return s.reindex(trade_dates, method='ffill')


def _ts_pit(date_index, value_series, trade_dates):
    """通用 point-in-time 前向填充：将任意日期索引+值前向填充到交易日序列。
    date_index: 原始日期（字符串、datetime、Series、Index、list等）
    value_series: 对应的值（Series、array、list等，与date_index等长）
    trade_dates: 目标交易日索引（DatetimeIndex）
    返回 Series(index=trade_dates)
    """
    # 统一转换为数组
    if hasattr(date_index, 'values'):
        di = date_index.values
    elif isinstance(date_index, (list, tuple)):
        di = np.array(date_index)
    else:
        di = np.asarray(date_index)
    if hasattr(value_series, 'values'):
        vs = value_series.values
    elif isinstance(value_series, (list, tuple)):
        vs = np.array(value_series, dtype=float)
    else:
        vs = np.asarray(value_series, dtype=float)

    if len(di) == 0 or len(vs) == 0:
        return pd.Series(np.nan, index=trade_dates)
    src = pd.Series(vs, index=pd.to_datetime(di))
    src = src[~src.index.duplicated(keep='last')].sort_index()
    return src.reindex(trade_dates, method='ffill')


# ============================================================
# 1. 盈利能力指标 (Profitability) - 9个
# ============================================================

def calc_profitability(bs, inc, cf):
    """计算盈利能力指标"""
    bs, inc, cf = _prep(bs, inc, cf)
    rp_list = sorted(set(bs['REPORTING_PERIOD']) & set(inc['REPORTING_PERIOD']) & set(cf['REPORTING_PERIOD']))
    if not rp_list:
        return pd.DataFrame()

    # 对齐到共同报告期
    bs_a = bs[bs['REPORTING_PERIOD'].isin(rp_list)].set_index('REPORTING_PERIOD').sort_index()
    inc_a = inc[inc['REPORTING_PERIOD'].isin(rp_list)].set_index('REPORTING_PERIOD').sort_index()
    cf_a = cf[cf['REPORTING_PERIOD'].isin(rp_list)].set_index('REPORTING_PERIOD').sort_index()

    # TTM值
    np_ttm = get_ttm(inc.reset_index(drop=True), 'NET_PRO_EXCL_MIN_INT_INC')
    inc_tmp = inc.copy()
    inc_tmp['np_ttm'] = np_ttm.values
    cf_ttm = get_ttm(cf.reset_index(drop=True), 'NET_CASH_FLOWS_OPERA_ACT')
    cf_tmp = cf.copy()
    cf_tmp['cf_ttm'] = cf_ttm.values
    ebit_ttm = get_ttm(inc.reset_index(drop=True), 'EBIT')
    inc_tmp['ebit_ttm'] = ebit_ttm.values
    tax_cf_ttm = get_ttm(cf.reset_index(drop=True), 'PAY_ALL_TAX')
    cf_tmp['tax_cf_ttm'] = tax_cf_ttm.values

    inc_s = inc_tmp[inc_tmp['REPORTING_PERIOD'].isin(rp_list)].set_index('REPORTING_PERIOD').sort_index()
    cf_s = cf_tmp[cf_tmp['REPORTING_PERIOD'].isin(rp_list)].set_index('REPORTING_PERIOD').sort_index()

    ta = _safe_col(bs_a, 'TOTAL_ASSETS')
    ne = _safe_col(bs_a, 'TOT_SHARE_EQUITY_EXCL_MIN_INT')
    eq_incl = _safe_col(bs_a, 'TOT_SHARE_EQUITY_INCL_MIN_INT')

    # 平均值（用于比率分母，更精确）
    ta_avg = _avg_bs(ta)
    ne_avg = _avg_bs(ne)
    eq_incl_avg = _avg_bs(eq_incl)

    # 有息负债 = 短期借款 + 长期借款 + 应付债券 + 一年内到期非流动负债
    st_borrow = _safe_col(bs_a, 'ST_BORROWING').fillna(0)
    lt_loan = _safe_col(bs_a, 'LT_LOAN').fillna(0)
    bonds = _safe_col(bs_a, 'BONDS_PAYABLE').fillna(0)
    noncur_1y = _safe_col(bs_a, 'NONCUR_LIAB_DUE_WITHIN_1Y').fillna(0)
    interest_bearing_debt = st_borrow + lt_loan + bonds + noncur_1y
    invested_capital = eq_incl + interest_bearing_debt
    invested_capital_avg = _avg_bs(invested_capital)

    f = pd.DataFrame(index=bs_a.index)

    # 1. 全部资产现金回收率TTM（分母用平均总资产）
    f['全部资产现金回收率TTM'] = safe_div(cf_s['cf_ttm'].reindex(f.index).values, ta_avg.values)
    # 2. 全部资产现金回收率变动
    f['全部资产现金回收率变动'] = _safe_diff(f['全部资产现金回收率TTM'], f.index)
    # 3. 资产回报率TTM（分母用平均总资产）
    f['资产回报率TTM'] = safe_div(inc_s['np_ttm'].reindex(f.index).values, ta_avg.values)
    # 4. 资产回报率变动
    f['资产回报率变动'] = _safe_diff(f['资产回报率TTM'], f.index)
    # 5. 净资产收益率TTM（分母用平均净资产）
    f['净资产收益率TTM'] = safe_div(inc_s['np_ttm'].reindex(f.index).values, ne_avg.values)
    # 6. 净资产收益率变动
    f['净资产收益率变动'] = _safe_diff(f['净资产收益率TTM'], f.index)

    # 7. 资本回报率TTM = 息前税后经营利润TTM / 平均投入资本
    # 息前税后经营利润 ≈ EBIT * (1 - 有效税率), 用TTM口径计算有效税率
    inc_tax_ttm = get_ttm(inc.reset_index(drop=True), 'INCOME_TAX')
    total_profit_ttm = get_ttm(inc.reset_index(drop=True), 'TOTAL_PROFIT')
    inc_tmp2 = inc.copy()
    inc_tmp2['inc_tax_ttm'] = inc_tax_ttm.values
    inc_tmp2['total_profit_ttm'] = total_profit_ttm.values
    inc_s2_tax = inc_tmp2[inc_tmp2['REPORTING_PERIOD'].isin(rp_list)].set_index('REPORTING_PERIOD').sort_index()
    effective_tax_rate = safe_div(inc_s2_tax['inc_tax_ttm'].reindex(f.index).values,
                                  inc_s2_tax['total_profit_ttm'].reindex(f.index).values)
    # 有效税率约束在[0,1]区间，异常值回退到25%
    effective_tax_rate = np.where(
        np.isnan(effective_tax_rate) | (effective_tax_rate < 0) | (effective_tax_rate > 1),
        0.25, effective_tax_rate)
    ebit_after_tax = inc_s['ebit_ttm'].reindex(f.index).values * (1 - effective_tax_rate)
    f['资本回报率TTM'] = safe_div(ebit_after_tax, invested_capital_avg.values)
    # 8. 资本回报率变动
    f['资本回报率变动'] = _safe_diff(f['资本回报率TTM'], f.index)

    # 9. 税费负担占净资产比 = (当期应交税费-上年同期应交税费+缴纳税费现金流TTM) / 平均净资产
    tax_payable = _safe_col(bs_a, 'TAX_PAYABLE')
    tax_payable_prev = tax_payable.shift(4)
    tax_cf = cf_s['tax_cf_ttm'].reindex(f.index)
    f['税费负担占净资产比'] = safe_div((tax_payable - tax_payable_prev + tax_cf).values, ne_avg.values)

    return f


# ============================================================
# 2. 成长指标 (Growth) - 21个
# ============================================================

def calc_growth(bs, inc, cf):
    """计算成长指标"""
    bs, inc, cf = _prep(bs, inc, cf)
    rp_list = sorted(set(inc['REPORTING_PERIOD']))
    if not rp_list:
        return pd.DataFrame()

    inc_a = inc.set_index('REPORTING_PERIOD').sort_index()
    cf_a = cf.set_index('REPORTING_PERIOD').sort_index()
    bs_a = bs.set_index('REPORTING_PERIOD').sort_index()

    f = pd.DataFrame(index=inc_a.index)

    # --- TTM序列 ---
    np_ttm = get_ttm(inc, 'NET_PRO_EXCL_MIN_INT_INC')
    inc['np_ttm'] = np_ttm.values
    nr_ttm = get_ttm(inc, 'NET_PRO_AFTER_DED_NR_GL')
    # 若扣非净利润字段全NaN，用 净利润 - 营业外收入 + 营业外支出 估算
    if nr_ttm.isna().all():
        inc_for_nr = inc.copy()
        np_val = _safe_col(inc_for_nr, 'NET_PRO_EXCL_MIN_INT_INC')
        non_oper_inc = _safe_col(inc_for_nr, 'NON_OPER_INCOME').fillna(0)
        non_oper_exp = _safe_col(inc_for_nr, 'NON_OPER_EXP').fillna(0)
        inc_for_nr['_NR_EST'] = np_val - non_oper_inc + non_oper_exp
        nr_ttm = get_ttm(inc_for_nr.reset_index(drop=True), '_NR_EST')
    inc['nr_ttm'] = nr_ttm.values
    rev_ttm = get_ttm(inc, 'OPERA_REV')
    inc['rev_ttm'] = rev_ttm.values
    op_ttm = get_ttm(inc, 'OPERA_PROFIT')
    inc['op_ttm'] = op_ttm.values
    cf_ttm_s = get_ttm(cf, 'NET_CASH_FLOWS_OPERA_ACT')
    cf['cf_ttm'] = cf_ttm_s.values

    inc_s = inc.set_index('REPORTING_PERIOD').sort_index()
    cf_s = cf.set_index('REPORTING_PERIOD').sort_index()

    # --- 单季度序列 ---
    sq_np = get_single_quarter(inc.reset_index(drop=True), 'NET_PRO_EXCL_MIN_INT_INC')
    inc_reset = inc.reset_index(drop=True)
    inc_reset['sq_np'] = sq_np.values
    # 单季度EPS = 单季度净利润 / 总股本
    # 注意：不能对累计BASIC_EPS做差分拆单季度，因为各季度加权股本不同
    inc_for_eps = inc.reset_index(drop=True).copy()
    np_sq_for_eps = get_single_quarter(inc_for_eps, 'NET_PRO_EXCL_MIN_INT_INC')
    bs_for_eps = bs.set_index('REPORTING_PERIOD').sort_index()
    tot_s = _safe_col(bs_for_eps, 'TOT_SHARE').reindex(inc_for_eps.set_index('REPORTING_PERIOD').sort_index().index)
    sq_eps = pd.Series(safe_div(np_sq_for_eps.values, tot_s.values), index=np_sq_for_eps.index)
    inc_reset['sq_eps'] = sq_eps.values
    sq_op = get_single_quarter(inc.reset_index(drop=True), 'OPERA_PROFIT')
    inc_reset['sq_op'] = sq_op.values
    sq_rev = get_single_quarter(inc.reset_index(drop=True), 'OPERA_REV')
    inc_reset['sq_rev'] = sq_rev.values
    sq_cf = get_single_quarter(cf.reset_index(drop=True), 'NET_CASH_FLOWS_OPERA_ACT')
    cf_reset = cf.reset_index(drop=True)
    cf_reset['sq_cf'] = sq_cf.values

    inc_sq = inc_reset.set_index('REPORTING_PERIOD').sort_index()
    cf_sq = cf_reset.set_index('REPORTING_PERIOD').sort_index()

    # 10. 营业收入增速 = (当期营业收入-去年同期) / 去年同期
    rev = _safe_col(inc_a, 'OPERA_REV')
    f['营业收入增速'] = _yoy(rev)

    # 11. 每股盈利
    if 'BASIC_EPS' in inc_a.columns and inc_a['BASIC_EPS'].notna().any():
        f['每股盈利'] = _safe_col(inc_a, 'BASIC_EPS').reindex(f.index)
    else:
        # fallback: 净利润 / 总股本(股)
        np_val = _safe_col(inc_a, 'NET_PRO_EXCL_MIN_INT_INC').reindex(f.index)
        tot_s = _safe_col(bs_a, 'TOT_SHARE').reindex(f.index)
        f['每股盈利'] = pd.Series(safe_div(np_val.values, tot_s.values), index=f.index)

    # 12. 每股盈利增速_单季度同比
    f['每股盈利增速_单季度同比'] = _yoy(inc_sq['sq_eps'].reindex(f.index))

    # 13. 每股盈利增速_TTM同比 = EPS_TTM 同比增长率
    np_ttm_for_eps = inc_s['np_ttm'].reindex(f.index)
    bs_tot_share = _safe_col(bs_a, 'TOT_SHARE').reindex(f.index)
    eps_ttm_series = pd.Series(safe_div(np_ttm_for_eps.values, bs_tot_share.values), index=f.index)
    f['每股盈利增速_TTM同比'] = _ttm_yoy(eps_ttm_series)

    # 14. 扣非净利润增速_TTM同比
    f['扣非净利润增速_TTM同比'] = _ttm_yoy(inc_s['nr_ttm'].reindex(f.index))

    # 15. 净利润增速_单季度同比
    f['净利润增速_单季度同比'] = _yoy(inc_sq['sq_np'].reindex(f.index))

    # 16. 净利润增速_单季度环比
    f['净利润增速_单季度环比'] = _qoq(inc_sq['sq_np'].reindex(f.index))

    # 17. 净利润增速_TTM同比
    f['净利润增速_TTM同比'] = _ttm_yoy(inc_s['np_ttm'].reindex(f.index))

    # 18. 经营现金流增速_单季度环比
    f['经营现金流增速_单季度环比'] = _qoq(cf_sq['sq_cf'].reindex(f.index))

    # 19. 经营现金流增速_单季度同比
    f['经营现金流增速_单季度同比'] = _yoy(cf_sq['sq_cf'].reindex(f.index))

    # 20. 经营现金流增速_TTM同比
    f['经营现金流增速_TTM同比'] = _ttm_yoy(cf_s['cf_ttm'].reindex(f.index))

    # 21. 营业利润增速_单季度同比
    f['营业利润增速_单季度同比'] = _yoy(inc_sq['sq_op'].reindex(f.index))

    # 22. 营业利润增速_单季度环比
    f['营业利润增速_单季度环比'] = _qoq(inc_sq['sq_op'].reindex(f.index))

    # 23. 营业利润增速_TTM同比
    f['营业利润增速_TTM同比'] = _ttm_yoy(inc_s['op_ttm'].reindex(f.index))

    # 24. 营业收入增速_单季度同比
    f['营业收入增速_单季度同比'] = _yoy(inc_sq['sq_rev'].reindex(f.index))

    # 25. 营业收入增速_单季度环比
    f['营业收入增速_单季度环比'] = _qoq(inc_sq['sq_rev'].reindex(f.index))

    # 26. 营业收入增速_TTM同比
    f['营业收入增速_TTM同比'] = _ttm_yoy(inc_s['rev_ttm'].reindex(f.index))

    # 27-29. 净资产收益率增速 (单季度同比/环比, TTM同比)
    sq_ne = get_single_quarter(inc.reset_index(drop=True), 'NET_PRO_EXCL_MIN_INT_INC')
    bs_rp = bs.set_index('REPORTING_PERIOD').sort_index()
    ne_aligned = _safe_col(bs_rp, 'TOT_SHARE_EQUITY_EXCL_MIN_INT').reindex(f.index)
    ne_avg_aligned = _avg_bs(ne_aligned)
    sq_roe = pd.Series(safe_div(
        pd.Series(sq_ne.values, index=inc.set_index('REPORTING_PERIOD').sort_index().index).reindex(f.index).values,
        ne_avg_aligned.values
    ), index=f.index)
    f['净资产收益率增速_单季度同比'] = _yoy(sq_roe)
    f['净资产收益率增速_单季度环比'] = _qoq(sq_roe)

    roe_ttm = pd.Series(safe_div(
        inc_s['np_ttm'].reindex(f.index).values,
        ne_avg_aligned.values
    ), index=f.index)
    f['净资产收益率增速_TTM同比'] = _ttm_yoy(roe_ttm)

    # 30. 总资产增速
    ta = _safe_col(bs_rp, 'TOTAL_ASSETS').reindex(f.index)
    f['总资产增速'] = _yoy(ta)

    return f


# ============================================================
# 3. 营运效率指标 (Efficiency) - 15个
# ============================================================

def calc_efficiency(bs, inc, cf):
    """计算营运效率指标"""
    bs, inc, cf = _prep(bs, inc, cf)
    rp_list = sorted(set(bs['REPORTING_PERIOD']) & set(inc['REPORTING_PERIOD']))
    if not rp_list:
        return pd.DataFrame()

    bs_a = bs[bs['REPORTING_PERIOD'].isin(rp_list)].set_index('REPORTING_PERIOD').sort_index()
    inc_a = inc[inc['REPORTING_PERIOD'].isin(rp_list)].set_index('REPORTING_PERIOD').sort_index()

    # TTM序列
    rev_ttm = get_ttm(inc, 'OPERA_REV')
    inc['rev_ttm'] = rev_ttm.values
    cost_ttm = get_ttm(inc, 'LESS_OPERA_COST')
    inc['cost_ttm'] = cost_ttm.values
    np_ttm = get_ttm(inc, 'NET_PRO_EXCL_MIN_INT_INC')
    inc['np_ttm'] = np_ttm.values
    op_ttm = get_ttm(inc, 'OPERA_PROFIT')
    inc['op_ttm'] = op_ttm.values
    fin_ttm = get_ttm(inc, 'LESS_FIN_EXP')
    inc['fin_ttm'] = fin_ttm.values
    sell_ttm = get_ttm(inc, 'LESS_SELLING_EXP')
    inc['sell_ttm'] = sell_ttm.values

    inc_s = inc[inc['REPORTING_PERIOD'].isin(rp_list)].set_index('REPORTING_PERIOD').sort_index()

    f = pd.DataFrame(index=bs_a.index)
    ta = _safe_col(bs_a, 'TOTAL_ASSETS')
    ta_avg = _avg_bs(ta)

    # 31. 资产周转率TTM（分母用平均总资产）
    f['资产周转率TTM'] = safe_div(inc_s['rev_ttm'].reindex(f.index).values, ta_avg.values)
    # 32. 资产周转率变动
    f['资产周转率变动'] = _safe_diff(f['资产周转率TTM'], f.index)

    # 33. 毛利率变动 = 当期毛利率TTM - 上期毛利率TTM
    gross_margin_ttm = safe_div(
        (inc_s['rev_ttm'].reindex(f.index) - inc_s['cost_ttm'].reindex(f.index)).values,
        inc_s['rev_ttm'].reindex(f.index).values
    )
    f['毛利率变动'] = _safe_diff(pd.Series(gross_margin_ttm, index=f.index), f.index)

    # 34. 存货周转率TTM = 营业成本TTM / 滚动四季度存货平均余额
    inv = _safe_col(bs_a, 'INV')
    # 使用TTM期初及四个季末余额平均，更精确匹配TTM口径。
    inv_avg = (inv + inv.shift(1) + inv.shift(2) + inv.shift(3) + inv.shift(4)) / 5
    # 数据不足时回退到2点平均
    inv_avg_2pt = (inv + inv.shift(1)) / 2
    inv_avg = inv_avg.where(inv_avg.notna(), inv_avg_2pt)
    # 仍不足时回退到期末值
    inv_avg = inv_avg.where(inv_avg.notna(), inv)
    f['存货周转率TTM'] = safe_div(inc_s['cost_ttm'].reindex(f.index).values, inv_avg.values)
    # 35. 存货周转率变动
    f['存货周转率变动'] = _safe_diff(f['存货周转率TTM'], f.index)

    # 36. 净利率TTM
    f['净利率TTM'] = safe_div(inc_s['np_ttm'].reindex(f.index).values,
                              inc_s['rev_ttm'].reindex(f.index).values)

    # 37. 营业利润率TTM
    f['营业利润率TTM'] = safe_div(inc_s['op_ttm'].reindex(f.index).values,
                               inc_s['rev_ttm'].reindex(f.index).values)
    # 38. 营业利润率变动
    f['营业利润率变动'] = _safe_diff(f['营业利润率TTM'], f.index)

    # 39. 营业利润比毛利润 = 营业利润TTM / 毛利润TTM
    gross_profit_ttm = inc_s['rev_ttm'].reindex(f.index) - inc_s['cost_ttm'].reindex(f.index)
    f['营业利润比毛利润'] = safe_div(inc_s['op_ttm'].reindex(f.index).values,
                                gross_profit_ttm.values)

    # 40. 应收周转率TTM = 营业收入TTM / 滚动四季度应收项目平均余额
    ar = _safe_col(bs_a, 'ACCT_RECEIVABLE').fillna(0)
    nr = _safe_col(bs_a, 'NOTES_RECEIVABLE').fillna(0)
    recv = ar + nr
    recv_avg = (recv + recv.shift(1) + recv.shift(2) + recv.shift(3) + recv.shift(4)) / 5
    recv_avg_2pt = (recv + recv.shift(1)) / 2
    recv_avg = recv_avg.where(recv_avg.notna(), recv_avg_2pt)
    recv_avg = recv_avg.where(recv_avg.notna(), recv)
    f['应收周转率TTM'] = safe_div(inc_s['rev_ttm'].reindex(f.index).values, recv_avg.values)
    # 41. 应收周转率变动
    f['应收周转率变动'] = _safe_diff(f['应收周转率TTM'], f.index)

    # 42. 财务费用率TTM
    f['财务费用率TTM'] = safe_div(inc_s['fin_ttm'].reindex(f.index).values,
                               inc_s['rev_ttm'].reindex(f.index).values)
    # 43. 财务费用率变动
    f['财务费用率变动'] = _safe_diff(f['财务费用率TTM'], f.index)

    # 44. 销售费用率TTM
    f['销售费用率TTM'] = safe_div(inc_s['sell_ttm'].reindex(f.index).values,
                               inc_s['rev_ttm'].reindex(f.index).values)
    # 45. 销售费用率变动
    f['销售费用率变动'] = _safe_diff(f['销售费用率TTM'], f.index)

    return f


# ============================================================
# 4. 盈余质量指标 (Earnings Quality) - 8个
# ============================================================

def calc_earnings_quality(bs, inc, cf):
    """计算盈余质量指标"""
    bs, inc, cf = _prep(bs, inc, cf)
    rp_list = sorted(set(bs['REPORTING_PERIOD']) & set(inc['REPORTING_PERIOD']) & set(cf['REPORTING_PERIOD']))
    if not rp_list:
        return pd.DataFrame()

    bs_a = bs[bs['REPORTING_PERIOD'].isin(rp_list)].set_index('REPORTING_PERIOD').sort_index()
    inc_a = inc[inc['REPORTING_PERIOD'].isin(rp_list)].set_index('REPORTING_PERIOD').sort_index()

    # TTM
    op_ttm = get_ttm(inc, 'OPERA_PROFIT')
    inc['op_ttm'] = op_ttm.values
    rev_ttm = get_ttm(inc, 'OPERA_REV')
    inc['rev_ttm'] = rev_ttm.values
    cf_ttm_s = get_ttm(cf, 'NET_CASH_FLOWS_OPERA_ACT')
    cf['cf_ttm'] = cf_ttm_s.values

    inc_s = inc[inc['REPORTING_PERIOD'].isin(rp_list)].set_index('REPORTING_PERIOD').sort_index()
    cf_s = cf[cf['REPORTING_PERIOD'].isin(rp_list)].set_index('REPORTING_PERIOD').sort_index()

    f = pd.DataFrame(index=bs_a.index)

    op_ttm_a = inc_s['op_ttm'].reindex(f.index)
    cf_ttm_a = cf_s['cf_ttm'].reindex(f.index)
    rev_ttm_a = inc_s['rev_ttm'].reindex(f.index)

    # 46. 应计利润占比 = (营业利润TTM - 经营现金流TTM) / 营业利润TTM
    accrual = op_ttm_a - cf_ttm_a
    f['应计利润占比'] = safe_div(accrual.values, op_ttm_a.values)
    # 47. 应计利润占比变动
    f['应计利润占比变动'] = _safe_diff(f['应计利润占比'], f.index)

    # 48. 现金比率 = 期末现金及现金等价物余额 / 流动负债
    # 使用现金流量表的 END_BAL_CASH_CASH_EQU 更准确
    cash = _safe_col(bs_a, 'CURRENCY_CAP')  # 回退用货币资金
    if cf is not None and not cf.empty:
        cf_rp = cf[cf['REPORTING_PERIOD'].isin(rp_list)].set_index('REPORTING_PERIOD').sort_index()
        if 'END_BAL_CASH_CASH_EQU' in cf_rp.columns:
            cash = _safe_col(cf_rp, 'END_BAL_CASH_CASH_EQU').reindex(f.index)
    cur_liab = _safe_col(bs_a, 'TOTAL_CUR_LIAB')
    f['现金比率'] = safe_div(cash.values, cur_liab.values)
    # 49. 现金比率变动
    f['现金比率变动'] = _safe_diff(f['现金比率'], f.index)

    # 50. 经营现金流比营业收入
    f['经营现金流比营业收入'] = safe_div(cf_ttm_a.values, rev_ttm_a.values)
    # 51. 经营现金流比营业收入变动
    f['经营现金流比营业收入变动'] = _safe_diff(f['经营现金流比营业收入'], f.index)

    # 52. 经营现金流比营业利润
    f['经营现金流比营业利润'] = safe_div(cf_ttm_a.values, op_ttm_a.values)
    # 53. 经营现金流比营业利润变动
    f['经营现金流比营业利润变动'] = _safe_diff(f['经营现金流比营业利润'], f.index)

    return f


# ============================================================
# 5. 安全性指标 (Safety) - 14个
# ============================================================

def calc_safety(bs, inc, cf):
    """计算安全性指标"""
    bs, inc, cf = _prep(bs, inc, cf)
    rp_list = sorted(set(bs['REPORTING_PERIOD']) & set(cf['REPORTING_PERIOD']))
    if not rp_list:
        return pd.DataFrame()

    bs_a = bs[bs['REPORTING_PERIOD'].isin(rp_list)].set_index('REPORTING_PERIOD').sort_index()
    cf_ttm_s = get_ttm(cf, 'NET_CASH_FLOWS_OPERA_ACT')
    cf['cf_ttm'] = cf_ttm_s.values
    cf_s = cf[cf['REPORTING_PERIOD'].isin(rp_list)].set_index('REPORTING_PERIOD').sort_index()

    f = pd.DataFrame(index=bs_a.index)

    ta = _safe_col(bs_a, 'TOTAL_ASSETS')
    tl = _safe_col(bs_a, 'TOTAL_LIAB')
    cur_liab = _safe_col(bs_a, 'TOTAL_CUR_LIAB')
    cur_asset = _safe_col(bs_a, 'TOTAL_CUR_ASSETS')
    noncur_liab = _safe_col(bs_a, 'TOTAL_NONCUR_LIAB')
    ne = _safe_col(bs_a, 'TOT_SHARE_EQUITY_EXCL_MIN_INT')
    inv = _safe_col(bs_a, 'INV').fillna(0)
    prepay = _safe_col(bs_a, 'PREPAYMENT').fillna(0)
    cf_ttm_a = cf_s['cf_ttm'].reindex(f.index)

    # 54. 流动负债占比 = 流动负债 / 总负债
    f['流动负债占比'] = safe_div(cur_liab.values, tl.values)
    # 55. 流动负债占比变动
    f['流动负债占比变动'] = _safe_diff(f['流动负债占比'], f.index)

    # 56. 长期负债占比 = 非流动负债 / 总负债
    f['长期负债占比'] = safe_div(noncur_liab.values, tl.values)
    # 57. 长期负债占比变动
    f['长期负债占比变动'] = _safe_diff(f['长期负债占比'], f.index)

    # 58. 现金流动负债比率 = 经营净现金流TTM / 流动负债
    f['现金流动负债比率'] = safe_div(cf_ttm_a.values, cur_liab.values)
    # 59. 现金流动负债比率变动
    f['现金流动负债比率变动'] = _safe_diff(f['现金流动负债比率'], f.index)

    # 60. 流动比率 = 流动资产 / 流动负债
    f['流动比率'] = safe_div(cur_asset.values, cur_liab.values)
    # 61. 流动比率变动
    f['流动比率变动'] = _safe_diff(f['流动比率'], f.index)

    # 62. 资产负债率变动
    alr = pd.Series(safe_div(tl.values, ta.values), index=f.index)
    f['资产负债率变动'] = _safe_diff(alr, f.index)

    # 63. 资产负债比 = 总负债 / 总资产
    f['资产负债比'] = alr

    # 64. 产权比率 = 总负债 / 归母股东权益
    f['产权比率'] = safe_div(tl.values, ne.values)
    # 65. 产权比率变动
    f['产权比率变动'] = _safe_diff(f['产权比率'], f.index)

    # 66. 速动比率 = (流动资产-存货-预付款项-待摊费用) / 流动负债
    unamortized = _safe_col(bs_a, 'UNAMORTIZED_EXP').fillna(0)
    quick_asset = cur_asset - inv - prepay - unamortized
    f['速动比率'] = safe_div(quick_asset.values, cur_liab.values)
    # 67. 速动比率变动
    f['速动比率变动'] = _safe_diff(f['速动比率'], f.index)

    return f


# ============================================================
# 6. 公司治理指标 (Governance) - 2个
# ============================================================

def calc_governance(code, inc, equity_structure, dividend, trade_dates):
    """计算公司治理指标（日频），返回 DataFrame, index=trade_dates"""
    f = pd.DataFrame(index=trade_dates)

    # 68. 流通股占比 = 流通股 / 总股本（按 CHANGE_DATE 前向填充到交易日）
    float_a = _equity_pit(equity_structure, code, 'FLOAT_A_SHARE', trade_dates)
    tot_s = _equity_pit(equity_structure, code, 'TOT_SHARE', trade_dates)
    f['流通股占比'] = safe_div(float_a.values, tot_s.values)

    # 69. 股利支付率 = 每股分红*基准股本 / 对应报告期净利润，按公告日 pit 填充到交易日
    f['股利支付率'] = np.nan
    if dividend is not None and not dividend.empty and inc is not None and not inc.empty:
        div = dividend[dividend['MARKET_CODE'] == code].copy()
        inc_f = _filter_statements(inc)
        if not div.empty and not inc_f.empty and 'DVD_PER_SHARE_PRE_TAX_CASH' in div.columns and 'REPORT_PERIOD' in div.columns:
            div = div.sort_values('REPORT_PERIOD').drop_duplicates('REPORT_PERIOD', keep='last')
            inc_sorted = inc_f.sort_values('REPORTING_PERIOD').drop_duplicates('REPORTING_PERIOD', keep='last')
            inc_sorted = inc_sorted.set_index('REPORTING_PERIOD')
            # 计算每条分红记录的股利支付率，以 REPORT_PERIOD 作为时间索引
            payout_dates = []
            payout_vals = []
            for _, row in div.iterrows():
                rp = row['REPORT_PERIOD']
                dps = float(row['DVD_PER_SHARE_PRE_TAX_CASH']) if pd.notna(row['DVD_PER_SHARE_PRE_TAX_CASH']) else 0
                base_share = float(row['DIV_BASESHARE']) if 'DIV_BASESHARE' in div.columns and pd.notna(row.get('DIV_BASESHARE')) else np.nan
                total_div = dps * base_share if pd.notna(base_share) else np.nan
                if rp in inc_sorted.index and 'NET_PRO_EXCL_MIN_INT_INC' in inc_sorted.columns:
                    np_val = float(inc_sorted.loc[rp, 'NET_PRO_EXCL_MIN_INT_INC'])
                    if pd.notna(total_div) and pd.notna(np_val) and np_val != 0:
                        payout_dates.append(rp)
                        payout_vals.append(total_div / np_val)
            if payout_dates:
                f['股利支付率'] = _ts_pit(pd.Index(payout_dates), pd.Series(payout_vals), trade_dates)

    return f


# ============================================================
# 估值/规模辅助函数：股息率计算
# ============================================================

def _calc_dividend_yield(code, dividend, equity_structure, close, trade_dates, tot_share, mc):
    """计算股息率（日频），point-in-time：每个交易日用截至该日最近一次已实施分红 / 总市值"""
    result = pd.Series(np.nan, index=trade_dates)
    if dividend is None or dividend.empty:
        return result.values
    div_code = dividend[dividend['MARKET_CODE'] == code].copy()
    if div_code.empty or 'DVD_PER_SHARE_PRE_TAX_CASH' not in div_code.columns:
        return result.values

    # 确定时间基准列：优先派息日，fallback到报告期
    date_col = 'DATE_DVD_PAYOUT'
    if date_col not in div_code.columns or div_code[date_col].isna().all():
        date_col = 'REPORT_PERIOD'
    if date_col not in div_code.columns:
        return result.values

    div_code = div_code[div_code[date_col].notna() & (div_code[date_col].astype(str) != '')]
    if div_code.empty:
        return result.values

    div_code[date_col] = pd.to_datetime(div_code[date_col])
    div_code = div_code.sort_values(date_col)

    # 每条分红记录计算 分红总额 = DPS * 基准股本 * 10000
    dps_vals = div_code['DVD_PER_SHARE_PRE_TAX_CASH'].astype(float).fillna(0)
    if 'DIV_BASESHARE' in div_code.columns:
        base_shares = div_code['DIV_BASESHARE'].astype(float)
    else:
        base_shares = pd.Series(np.nan, index=div_code.index)

    # 构建 point-in-time 分红总额序列：每个分红日记录一个分红总额，ffill到交易日
    div_amounts = []
    div_dates_list = []
    for idx in div_code.index:
        dps = dps_vals.loc[idx]
        bs_val = base_shares.loc[idx]
        d = div_code.loc[idx, date_col]
        # 基准股本缺失时用NaN，后续ffill时匹配当日总股本
        amount = dps * bs_val * 10000 if pd.notna(bs_val) else np.nan
        div_amounts.append(amount)
        div_dates_list.append(d)

    if not div_dates_list:
        return result.values

    # pit填充：每个交易日用最近一次分红的总额
    div_pit = _ts_pit(pd.Index(div_dates_list), pd.Series(div_amounts), trade_dates)
    # 对基准股本缺失的记录，用当日总股本 * 最近DPS 重算
    dps_pit = _ts_pit(pd.Index(div_dates_list), dps_vals.reset_index(drop=True), trade_dates)
    div_pit_filled = div_pit.copy()
    na_mask = div_pit.isna() & dps_pit.notna()
    div_pit_filled[na_mask] = dps_pit[na_mask] * tot_share[na_mask] * 10000

    return safe_div(div_pit_filled.values, mc)


def _calc_dividend_yield_ttm(code, dividend, equity_structure, trade_dates, tot_share, mc):
    """计算股息率TTM（日频），滚动12个月内所有已实施分红总额 / 总市值。
    按 DATE_DVD_PAYOUT（派息日）确认实施时间，未实施的不计入。
    对每个交易日，汇总过去12个月内的分红总额。
    """
    result = pd.Series(np.nan, index=trade_dates)
    if dividend is None or dividend.empty:
        return result.values
    div_code = dividend[dividend['MARKET_CODE'] == code].copy()
    if div_code.empty or 'DVD_PER_SHARE_PRE_TAX_CASH' not in div_code.columns:
        return result.values

    # 优先使用派息日确认已实施，fallback到报告期
    date_col = 'DATE_DVD_PAYOUT'
    if date_col not in div_code.columns or div_code[date_col].isna().all():
        date_col = 'REPORT_PERIOD'
    if date_col not in div_code.columns:
        return result.values

    div_code = div_code[div_code[date_col].notna() & (div_code[date_col].astype(str) != '')]
    if div_code.empty:
        return result.values

    div_code[date_col] = pd.to_datetime(div_code[date_col])
    div_code = div_code.sort_values(date_col)
    dps_vals = div_code['DVD_PER_SHARE_PRE_TAX_CASH'].astype(float).fillna(0)

    # 每条分红记录的基准股本
    if 'DIV_BASESHARE' in div_code.columns:
        base_shares = div_code['DIV_BASESHARE'].astype(float)
    else:
        base_shares = pd.Series(np.nan, index=div_code.index)

    div_dates = div_code[date_col].values
    td_dt = trade_dates.to_numpy()

    # 对每个交易日，汇总过去365天内的分红总额
    div_total_daily = np.full(len(trade_dates), np.nan)
    for j in range(len(trade_dates)):
        td = td_dt[j]
        lookback = td - np.timedelta64(365, 'D')
        mask = (div_dates > lookback) & (div_dates <= td)
        if mask.any():
            total = 0.0
            for idx in div_code.index[mask]:
                dps = dps_vals.loc[idx]
                bs_val = base_shares.loc[idx]
                if pd.isna(bs_val):
                    bs_val = tot_share.iloc[j] if pd.notna(tot_share.iloc[j]) else 0
                total += dps * bs_val * 10000
            if total > 0:
                div_total_daily[j] = total

    return safe_div(div_total_daily, mc)


# ============================================================
# 7. 估值指标 (Valuation) - 12个（日频时序）
# ============================================================

def calc_valuation(code, bs, inc, cf, dividend, kline, equity_structure):
    """计算估值指标（日频时序），返回 DataFrame, index=交易日, 12列。
    市值 = 原始close * 总股本（不复权），财务数据按 point-in-time 前向填充。
    """
    if kline is None or kline.empty:
        return pd.DataFrame()

    # 构建交易日索引
    kl = kline.copy()
    kl['kline_time'] = pd.to_datetime(kl['kline_time'])
    kl = kl.sort_values('kline_time').drop_duplicates('kline_time', keep='last')
    trade_dates = kl.set_index('kline_time').index
    close = kl.set_index('kline_time')['close'].astype(float)

    # 总股本 point-in-time (万股)
    tot_share = _equity_pit(equity_structure, code, 'TOT_SHARE', trade_dates)
    # 总市值 = close * 总股本 * 10000
    total_mkt_cap = close * tot_share * 10000

    # 准备财务数据
    bs_f = _filter_statements(bs) if bs is not None and not bs.empty else pd.DataFrame()
    inc_f = _filter_statements(inc) if inc is not None and not inc.empty else pd.DataFrame()
    cf_f = _filter_statements(cf) if cf is not None and not cf.empty else pd.DataFrame()
    for df in [bs_f, inc_f, cf_f]:
        if not df.empty:
            df.sort_values('REPORTING_PERIOD', inplace=True)
            df.drop_duplicates('REPORTING_PERIOD', keep='last', inplace=True)

    # point-in-time 财务字段
    ne_total = _pit_fill(bs_f, 'TOT_SHARE_EQUITY_EXCL_MIN_INT', trade_dates)
    # 其他权益工具（永续债/优先股）计入权益但不归属普通股股东，计算普通股口径净资产时剔除
    oth_eq = _pit_fill(bs_f, 'OTH_EQUITY_TOOLS', trade_dates).fillna(0)
    ne = ne_total - oth_eq  # 普通股口径净资产
    np_last = _pit_fill(inc_f, 'NET_PRO_EXCL_MIN_INT_INC', trade_dates)
    rev_last = _pit_fill(inc_f, 'OPERA_REV', trade_dates)
    cf_op_last = _pit_fill(cf_f, 'NET_CASH_FLOWS_OPERA_ACT', trade_dates)

    # TTM 字段 → pit
    def _ttm_pit(df, field):
        if df is None or df.empty:
            return pd.Series(np.nan, index=trade_dates)
        ttm_s = get_ttm(df.reset_index(drop=True), field)
        tmp = df.copy()
        tmp['_ttm'] = ttm_s.values
        return _pit_fill(tmp, '_ttm', trade_dates)

    np_ttm = _ttm_pit(inc_f, 'NET_PRO_EXCL_MIN_INT_INC')
    rev_ttm = _ttm_pit(inc_f, 'OPERA_REV')
    cf_ttm = _ttm_pit(cf_f, 'NET_CASH_FLOWS_OPERA_ACT')
    fcf_ttm = _ttm_pit(cf_f, 'FREE_CASH_FLOW')
    ncf_ttm = _ttm_pit(cf_f, 'NET_INCR_CASH_AND_CASH_EQU')

    mc = total_mkt_cap.values
    f = pd.DataFrame(index=trade_dates)

    # 70. 市净率（使用最新报告期净资产，point-in-time）
    f['市净率'] = safe_div(mc, ne.values)
    # 71. 市现率（使用最新报告期经营现金流）
    f['市现率'] = safe_div(mc, cf_op_last.values)
    # 72. 市盈率（使用最新报告期净利润）
    f['市盈率'] = safe_div(mc, np_last.values)

    # 73. 股息率 = 每股分红 / close (pit)
    f['股息率'] = _calc_dividend_yield(code, dividend, equity_structure, close, trade_dates, tot_share, mc)

    # 74. 市销率（使用最新报告期营收）
    f['市销率'] = safe_div(mc, rev_last.values)
    # 75. 市现率TTM（使用经营现金流TTM）
    f['市现率TTM'] = safe_div(mc, cf_ttm.values)
    # 76. 市盈率TTM（使用净利润TTM）
    f['市盈率TTM'] = safe_div(mc, np_ttm.values)

    # 77. 股息率TTM
    f['股息率TTM'] = _calc_dividend_yield_ttm(code, dividend, equity_structure, trade_dates, tot_share, mc)

    # 78. 市销率TTM（使用营收TTM）
    f['市销率TTM'] = safe_div(mc, rev_ttm.values)
    # 79. 自由现金流TTM比总市值
    f['自由现金流TTM比总市值'] = safe_div(fcf_ttm.values, mc)
    # 80. 净现金流TTM比总市值 = 现金及现金等价物净增加额TTM / 总市值
    f['净现金流TTM比总市值'] = safe_div(ncf_ttm.values, mc)

    # 81. 市盈率相对盈利增长率(PEG) = PE_TTM / (净利润TTM同比增长率*100)
    # 精确匹配去年同日的TTM值
    np_ttm_series = np_ttm.copy()
    np_ttm_series.index = pd.to_datetime(np_ttm_series.index)
    prev_dates = np_ttm_series.index - pd.DateOffset(years=1)
    np_ttm_prev_aligned = np_ttm_series.reindex(prev_dates, method='ffill')
    np_ttm_prev_aligned.index = np_ttm_series.index
    # 增长率 = (当期TTM - 去年同期TTM) / abs(去年同期TTM)，用绝对值处理负基期
    growth = safe_div((np_ttm_series - np_ttm_prev_aligned).values,
                      np.abs(np_ttm_prev_aligned.values))
    pe_ttm_vals = f['市盈率TTM'].values
    f['市盈率相对盈利增长率'] = safe_div(pe_ttm_vals, growth * 100)

    return f


# ============================================================
# 8. 股东指标 (Shareholder) - 4个
# ============================================================

def calc_shareholder(code, holder_num, share_holder, trade_dates):
    """计算股东指标（日频），返回 DataFrame, index=trade_dates"""
    f = pd.DataFrame(index=trade_dates)

    # 82. 股东数目时序标准分数 = (披露期股东数目-历史披露期均值) / 历史披露期标准差
    f['股东数目时序标准分数'] = np.nan
    if holder_num is not None and not holder_num.empty:
        hn = holder_num[holder_num['MARKET_CODE'] == code].copy()
        if not hn.empty and 'HOLDER_NUM' in hn.columns:
            hn = hn.sort_values('HOLDER_ENDDATE').drop_duplicates('HOLDER_ENDDATE', keep='last')
            hn_series = hn.set_index('HOLDER_ENDDATE')['HOLDER_NUM'].astype(float).sort_index()
            # 在披露期维度计算z-score，再前向填充到交易日，避免日频重复值加权。
            exp_mean = hn_series.expanding(min_periods=2).mean()
            exp_std = hn_series.expanding(min_periods=2).std().replace(0, np.nan)
            z_score = (hn_series - exp_mean) / exp_std
            f['股东数目时序标准分数'] = _ts_pit(z_score.index.to_series(), z_score, trade_dates)

    # 83-85. 持仓机构相关 & 十大股东占比分散度
    f['持仓机构个数'] = np.nan
    f['持仓机构个数变化'] = np.nan
    f['十大股东占比分散度'] = np.nan
    if share_holder is not None and not share_holder.empty:
        sh = share_holder[share_holder['MARKET_CODE'] == code].copy()
        if not sh.empty and 'HOLDER_ENDDATE' in sh.columns:
            sh = sh.sort_values('HOLDER_ENDDATE')
            # HOLDER_HOLDER_CATEGORY: 1=个人, 2=公司；仅统计机构/公司股东。
            if 'HOLDER_HOLDER_CATEGORY' in sh.columns:
                holder_category = pd.to_numeric(sh['HOLDER_HOLDER_CATEGORY'], errors='coerce')
                sh_inst = sh[holder_category.eq(2)].copy()
            else:
                sh_inst = sh.iloc[0:0].copy()

            if not sh_inst.empty:
                inst_count = sh_inst.groupby('HOLDER_ENDDATE').size()
                inst_daily = _ts_pit(inst_count.index.to_series(), inst_count, trade_dates)
                f['持仓机构个数'] = inst_daily

                # 持仓机构个数变化：在每个披露日计算与上期的差值，前向填充到交易日
                if len(inst_count) >= 2:
                    inst_change_raw = inst_count.diff()
                    inst_change_daily = _ts_pit(inst_change_raw.index.to_series(), inst_change_raw, trade_dates)
                else:
                    inst_change_daily = pd.Series(np.nan, index=trade_dates)
                f['持仓机构个数变化'] = inst_change_daily

            # 十大股东占比分散度：按 HOLDER_ENDDATE 分组取 HOLDER_PCT 标准差 → ffill到交易日
            if 'HOLDER_PCT' in sh.columns:
                disp = sh.groupby('HOLDER_ENDDATE')['HOLDER_PCT'].apply(
                    lambda x: x.astype(float).dropna().std() if len(x.dropna()) > 1 else np.nan
                )
                disp_daily = _ts_pit(disp.index.to_series(), disp, trade_dates)
                f['十大股东占比分散度'] = disp_daily

    return f


# ============================================================
# 9. 规模指标 (Size) - 5个（日频时序）
# ============================================================

def calc_size(code, kline, equity_structure):
    """计算规模指标（日频时序），返回 DataFrame, index=交易日, 5列。
    市值 = 原始close * 股本（不复权）。
    """
    if kline is None or kline.empty:
        return pd.DataFrame()

    kl = kline.copy()
    kl['kline_time'] = pd.to_datetime(kl['kline_time'])
    kl = kl.sort_values('kline_time').drop_duplicates('kline_time', keep='last')
    trade_dates = kl.set_index('kline_time').index
    close = kl.set_index('kline_time')['close'].astype(float)

    tot_share = _equity_pit(equity_structure, code, 'TOT_SHARE', trade_dates)
    float_share = _equity_pit(equity_structure, code, 'FLOAT_A_SHARE', trade_dates)

    total_mkt_cap = close * tot_share * 10000
    float_mkt_cap = close * float_share * 10000

    f = pd.DataFrame(index=trade_dates)
    # 86. 流通市值
    f['流通市值'] = float_mkt_cap
    # 87. 流通市值比总市值
    f['流通市值比总市值'] = safe_div(float_mkt_cap.values, total_mkt_cap.values)
    # 88. 流通市值对数
    f['流通市值对数'] = np.where(float_mkt_cap > 0, np.log(float_mkt_cap), np.nan)
    # 89. 总市值对数
    f['总市值对数'] = np.where(total_mkt_cap > 0, np.log(total_mkt_cap), np.nan)
    # 90. 总市值
    f['总市值'] = total_mkt_cap

    return f


# ============================================================
# 主计算函数：汇总所有指标
# ============================================================

def calc_all_factors_for_stock(code, bs, inc, cf, kline,
                               equity_structure, dividend,
                               holder_num, share_holder):
    """为单只股票计算全部指标，返回 (quarterly_df, daily_df)。
    quarterly_df: 盈利+成长+效率+盈余+安全, index=REPORTING_PERIOD
    daily_df: 估值+规模+治理+股东, index=交易日
    """
    # ---- 季频指标 ----
    quarterly_parts = []

    try:
        prof = calc_profitability(bs, inc, cf)
        if not prof.empty:
            quarterly_parts.append(prof)
    except Exception as e:
        print(f'  [WARN] {code} 盈利能力指标计算异常: {e}', file=sys.stderr)

    try:
        grow = calc_growth(bs, inc, cf)
        if not grow.empty:
            quarterly_parts.append(grow)
    except Exception as e:
        print(f'  [WARN] {code} 成长指标计算异常: {e}', file=sys.stderr)

    try:
        eff = calc_efficiency(bs, inc, cf)
        if not eff.empty:
            quarterly_parts.append(eff)
    except Exception as e:
        print(f'  [WARN] {code} 营运效率指标计算异常: {e}', file=sys.stderr)

    try:
        eq = calc_earnings_quality(bs, inc, cf)
        if not eq.empty:
            quarterly_parts.append(eq)
    except Exception as e:
        print(f'  [WARN] {code} 盈余质量指标计算异常: {e}', file=sys.stderr)

    try:
        saf = calc_safety(bs, inc, cf)
        if not saf.empty:
            quarterly_parts.append(saf)
    except Exception as e:
        print(f'  [WARN] {code} 安全性指标计算异常: {e}', file=sys.stderr)

    # 合并季频时序指标
    if quarterly_parts:
        q_df = quarterly_parts[0]
        for part in quarterly_parts[1:]:
            for col in part.columns:
                q_df[col] = part[col].reindex(q_df.index)
    else:
        q_df = pd.DataFrame()

    if not q_df.empty:
        q_df.insert(0, 'code', code)

    # ---- 日频指标 ----
    daily_parts = []

    try:
        val = calc_valuation(code, bs, inc, cf, dividend, kline, equity_structure)
        if not val.empty:
            daily_parts.append(val)
    except Exception as e:
        print(f'  [WARN] {code} 估值指标计算异常: {e}', file=sys.stderr)

    try:
        sz = calc_size(code, kline, equity_structure)
        if not sz.empty:
            daily_parts.append(sz)
    except Exception as e:
        print(f'  [WARN] {code} 规模指标计算异常: {e}', file=sys.stderr)

    # 治理+股东指标（日频）：需要 trade_dates，从 kline 构建
    if kline is not None and not kline.empty:
        kl_tmp = kline.copy()
        kl_tmp['kline_time'] = pd.to_datetime(kl_tmp['kline_time'])
        kl_tmp = kl_tmp.sort_values('kline_time').drop_duplicates('kline_time', keep='last')
        trade_dates = kl_tmp.set_index('kline_time').index

        try:
            gov = calc_governance(code, inc, equity_structure, dividend, trade_dates)
            if not gov.empty:
                daily_parts.append(gov)
        except Exception as e:
            print(f'  [WARN] {code} 公司治理指标计算异常: {e}', file=sys.stderr)

        try:
            sh = calc_shareholder(code, holder_num, share_holder, trade_dates)
            if not sh.empty:
                daily_parts.append(sh)
        except Exception as e:
            print(f'  [WARN] {code} 股东指标计算异常: {e}', file=sys.stderr)

    if daily_parts:
        d_df = daily_parts[0]
        for part in daily_parts[1:]:
            for col in part.columns:
                d_df[col] = part[col].reindex(d_df.index)
    else:
        d_df = pd.DataFrame()

    if not d_df.empty:
        d_df.insert(0, 'code', code)

    return q_df, d_df


CATEGORY_MAP = {
    'profitability': {
        'name': '盈利能力',
        'freq': 'quarterly',
        'count': 9,
        'factors': [
            '全部资产现金回收率TTM', '全部资产现金回收率变动',
            '资产回报率TTM', '资产回报率变动',
            '净资产收益率TTM', '净资产收益率变动',
            '资本回报率TTM', '资本回报率变动',
            '税费负担占净资产比'
        ]
    },
    'growth': {
        'name': '成长指标',
        'freq': 'quarterly',
        'count': 21,
        'factors': [
            '营业收入增速', '每股盈利',
            '每股盈利增速_单季度同比', '每股盈利增速_TTM同比',
            '扣非净利润增速_TTM同比',
            '净利润增速_单季度同比', '净利润增速_单季度环比', '净利润增速_TTM同比',
            '经营现金流增速_单季度环比', '经营现金流增速_单季度同比', '经营现金流增速_TTM同比',
            '营业利润增速_单季度同比', '营业利润增速_单季度环比', '营业利润增速_TTM同比',
            '营业收入增速_单季度同比', '营业收入增速_单季度环比', '营业收入增速_TTM同比',
            '净资产收益率增速_单季度同比', '净资产收益率增速_单季度环比', '净资产收益率增速_TTM同比',
            '总资产增速'
        ]
    },
    'efficiency': {
        'name': '营运效率',
        'freq': 'quarterly',
        'count': 15,
        'factors': [
            '资产周转率TTM', '资产周转率变动',
            '毛利率变动',
            '存货周转率TTM', '存货周转率变动',
            '净利率TTM',
            '营业利润率TTM', '营业利润率变动',
            '营业利润比毛利润',
            '应收周转率TTM', '应收周转率变动',
            '财务费用率TTM', '财务费用率变动',
            '销售费用率TTM', '销售费用率变动'
        ]
    },
    'earnings_quality': {
        'name': '盈余质量',
        'freq': 'quarterly',
        'count': 8,
        'factors': [
            '应计利润占比', '应计利润占比变动',
            '现金比率', '现金比率变动',
            '经营现金流比营业收入', '经营现金流比营业收入变动',
            '经营现金流比营业利润', '经营现金流比营业利润变动'
        ]
    },
    'safety': {
        'name': '安全性',
        'freq': 'quarterly',
        'count': 14,
        'factors': [
            '流动负债占比', '流动负债占比变动',
            '长期负债占比', '长期负债占比变动',
            '现金流动负债比率', '现金流动负债比率变动',
            '流动比率', '流动比率变动',
            '资产负债率变动', '资产负债比',
            '产权比率', '产权比率变动',
            '速动比率', '速动比率变动'
        ]
    },
    'governance': {
        'name': '公司治理',
        'freq': 'daily',
        'count': 2,
        'factors': ['流通股占比', '股利支付率']
    },
    'valuation': {
        'name': '估值指标',
        'freq': 'daily',
        'count': 12,
        'factors': [
            '市净率', '市现率', '市盈率', '股息率', '市销率',
            '市现率TTM', '市盈率TTM', '股息率TTM', '市销率TTM',
            '自由现金流TTM比总市值', '净现金流TTM比总市值',
            '市盈率相对盈利增长率'
        ]
    },
    'shareholder': {
        'name': '股东指标',
        'freq': 'daily',
        'count': 4,
        'factors': ['股东数目时序标准分数', '持仓机构个数', '持仓机构个数变化', '十大股东占比分散度']
    },
    'size': {
        'name': '规模指标',
        'freq': 'daily',
        'count': 5,
        'factors': ['流通市值', '流通市值比总市值', '流通市值对数', '总市值对数', '总市值']
    }
}

QUARTERLY_CATEGORIES = ['profitability', 'growth', 'efficiency', 'earnings_quality', 'safety']
DAILY_CATEGORIES = ['governance', 'valuation', 'shareholder', 'size']


# ================================================================
#  评判函数
# ================================================================

def _find_factor_category(factor_name):
    """查找指标所属类别"""
    for cat_key, cat_info in CATEGORY_MAP.items():
        if factor_name in cat_info['factors']:
            return cat_key
    return None


def _format_value(v):
    """格式化单个值用于JSON输出"""
    if isinstance(v, (np.floating, float)):
        if np.isnan(v) or np.isinf(v):
            return None
        return round(float(v), 6)
    if isinstance(v, (np.integer, int)):
        return int(v)
    return v


def _df_to_records(df, max_rows=20):
    """DataFrame转换为JSON友好的记录列表"""
    if df is None or df.empty:
        return []
    df_out = df.tail(max_rows).copy()
    records = []
    for idx, row in df_out.iterrows():
        rec = {'period': str(idx)}
        for col in row.index:
            rec[col] = _format_value(row[col])
        records.append(rec)
    return records



# ================================================================
#  主分析函数
# ================================================================

def run_analysis(code, begin_date, end_date, category=None, factor_name=None,
                 list_factors=False, output_format='json'):
    """运行基本面指标分析"""

    if list_factors:
        total = sum(c['count'] for c in CATEGORY_MAP.values())
        result = {"total_factors": total, "categories": {}}
        for cat_key, cat_info in CATEGORY_MAP.items():
            result["categories"][cat_key] = {
                "name": cat_info['name'],
                "freq": cat_info['freq'],
                "count": cat_info['count'],
                "factors": cat_info['factors']
            }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    username = os.environ.get('AD_USERNAME')
    password = os.environ.get('AD_PASSWORD')
    host = os.environ.get('AD_HOST')
    port = os.environ.get('AD_PORT')

    if not all([username, password, host, port]):
        missing = []
        if not username: missing.append('AD_USERNAME')
        if not password: missing.append('AD_PASSWORD')
        if not host: missing.append('AD_HOST')
        if not port: missing.append('AD_PORT')
        print(json.dumps({
            "error": f"缺少环境变量: {', '.join(missing)}。请先设置: "
                     f"set AD_USERNAME=xxx & set AD_PASSWORD=xxx & set AD_HOST=xxx & set AD_PORT=xxx"
        }, ensure_ascii=False))
        return

    if factor_name:
        cat_key = _find_factor_category(factor_name)
        if not cat_key:
            print(json.dumps({"error": f"未找到指标: {factor_name}"}, ensure_ascii=False))
            return
        categories_to_calc = [cat_key]
    elif category and category != 'all':
        if category not in CATEGORY_MAP:
            print(json.dumps({
                "error": f"未知类别: {category}, 可选: {list(CATEGORY_MAP.keys()) + ['all']}"
            }, ensure_ascii=False))
            return
        categories_to_calc = [category]
    else:
        categories_to_calc = list(CATEGORY_MAP.keys())

    need_quarterly = any(c in QUARTERLY_CATEGORIES for c in categories_to_calc)
    need_daily = any(c in DAILY_CATEGORIES for c in categories_to_calc)

    print(f"正在登录AmazingData...", file=sys.stderr)
    ad.login(username=username, password=password, host=host, port=int(port))

    print(f"正在获取 {code} 的数据...", file=sys.stderr)
    base_data = ad.BaseData()
    info_data = ad.InfoData()
    code_list = [code]

    print(f"  获取财务报表...", file=sys.stderr)
    balance_sheet = info_data.get_balance_sheet(code_list, is_local=False)
    income = info_data.get_income(code_list, is_local=False)
    cash_flow = info_data.get_cash_flow(code_list, is_local=False)

    bs = balance_sheet.get(code) if balance_sheet else None
    inc = income.get(code) if income else None
    cf = cash_flow.get(code) if cash_flow else None

    if bs is None or inc is None or cf is None or \
       (hasattr(bs, 'empty') and bs.empty) or \
       (hasattr(inc, 'empty') and inc.empty) or \
       (hasattr(cf, 'empty') and cf.empty):
        print(json.dumps({"error": f"获取 {code} 财务数据失败或为空"}, ensure_ascii=False))
        return

    kline = None
    equity_structure = None
    dividend = None
    holder_num = None
    share_holder = None

    if need_daily:
        print(f"  获取股本结构...", file=sys.stderr)
        equity_structure = info_data.get_equity_structure(code_list, is_local=False)
        print(f"  获取分红数据...", file=sys.stderr)
        dividend = info_data.get_dividend(code_list, is_local=False)

        if any(c == 'shareholder' for c in categories_to_calc):
            print(f"  获取股东数据...", file=sys.stderr)
            holder_num = info_data.get_holder_num(code_list, is_local=False)
            share_holder = info_data.get_share_holder(code_list, is_local=False)

        print(f"  获取K线行情({begin_date}-{end_date})...", file=sys.stderr)
        calendar = base_data.get_calendar(market='SZ')
        market_data = ad.MarketData(calendar)
        kline_dict = market_data.query_kline(
            code_list, begin_date=begin_date, end_date=end_date,
            period=ad.constant.Period.day.value
        )
        kline = kline_dict.get(code) if kline_dict else None

    result_data = {
        "code": code,
        "analysis_date": datetime.now().strftime('%Y-%m-%d'),
        "categories": {}
    }

    quarterly_dfs = {}
    if need_quarterly:
        for cat_key in categories_to_calc:
            if cat_key not in QUARTERLY_CATEGORIES:
                continue
            try:
                print(f"  计算{CATEGORY_MAP[cat_key]['name']}...", file=sys.stderr)
                if cat_key == 'profitability':
                    df = calc_profitability(bs, inc, cf)
                elif cat_key == 'growth':
                    df = calc_growth(bs, inc, cf)
                elif cat_key == 'efficiency':
                    df = calc_efficiency(bs, inc, cf)
                elif cat_key == 'earnings_quality':
                    df = calc_earnings_quality(bs, inc, cf)
                elif cat_key == 'safety':
                    df = calc_safety(bs, inc, cf)
                else:
                    continue

                if df is not None and not df.empty:
                    quarterly_dfs[cat_key] = df
                    latest = {}
                    for col in df.columns:
                        val = df[col].iloc[-1]
                        latest[col] = _format_value(val)


                    result_data["categories"][cat_key] = {
                        "name": CATEGORY_MAP[cat_key]['name'],
                        "freq": "季频",
                        "latest_period": str(df.index[-1]),
                        "total_periods": len(df),
                        "latest_values": latest,
                        "history": _df_to_records(df, max_rows=8),
                    }
                else:
                    result_data["categories"][cat_key] = {
                        "name": CATEGORY_MAP[cat_key]['name'],
                        "error": "计算结果为空"
                    }
            except Exception as e:
                result_data["categories"][cat_key] = {
                    "name": CATEGORY_MAP[cat_key]['name'],
                    "error": str(e)
                }

    daily_dfs = {}
    if need_daily:
        for cat_key in categories_to_calc:
            if cat_key not in DAILY_CATEGORIES:
                continue
            try:
                print(f"  计算{CATEGORY_MAP[cat_key]['name']}...", file=sys.stderr)
                if cat_key == 'valuation':
                    df = calc_valuation(code, bs, inc, cf, dividend, kline, equity_structure)
                elif cat_key == 'size':
                    df = calc_size(code, kline, equity_structure)
                elif cat_key == 'governance':
                    if kline is not None and not kline.empty:
                        kl_tmp = kline.copy()
                        kl_tmp['kline_time'] = pd.to_datetime(kl_tmp['kline_time'])
                        kl_tmp = kl_tmp.sort_values('kline_time').drop_duplicates('kline_time', keep='last')
                        trade_dates = kl_tmp.set_index('kline_time').index
                        df = calc_governance(code, inc, equity_structure, dividend, trade_dates)
                    else:
                        df = pd.DataFrame()
                elif cat_key == 'shareholder':
                    if kline is not None and not kline.empty:
                        kl_tmp = kline.copy()
                        kl_tmp['kline_time'] = pd.to_datetime(kl_tmp['kline_time'])
                        kl_tmp = kl_tmp.sort_values('kline_time').drop_duplicates('kline_time', keep='last')
                        trade_dates = kl_tmp.set_index('kline_time').index
                        df = calc_shareholder(code, holder_num, share_holder, trade_dates)
                    else:
                        df = pd.DataFrame()
                else:
                    continue

                if df is not None and not df.empty:
                    daily_dfs[cat_key] = df
                    latest = {}
                    for col in df.columns:
                        if col == 'code':
                            continue
                        val = df[col].iloc[-1]
                        latest[col] = _format_value(val)


                    result_data["categories"][cat_key] = {
                        "name": CATEGORY_MAP[cat_key]['name'],
                        "freq": "日频",
                        "latest_date": str(df.index[-1])[:10],
                        "total_days": len(df),
                        "latest_values": latest,
                        "history": _df_to_records(df.drop(columns=['code'], errors='ignore'), max_rows=5),
                    }
                else:
                    result_data["categories"][cat_key] = {
                        "name": CATEGORY_MAP[cat_key]['name'],
                        "error": "计算结果为空（可能缺少K线或股本数据）"
                    }
            except Exception as e:
                result_data["categories"][cat_key] = {
                    "name": CATEGORY_MAP[cat_key]['name'],
                    "error": str(e)
                }

    if factor_name:
        cat_key = _find_factor_category(factor_name)
        cat_data = result_data["categories"].get(cat_key, {})
        latest_vals = cat_data.get("latest_values", {})
        factor_result = {
            "code": code,
            "factor": factor_name,
            "category": CATEGORY_MAP[cat_key]['name'],
            "freq": CATEGORY_MAP[cat_key]['freq'],
            "latest_value": latest_vals.get(factor_name),
            "latest_period": cat_data.get("latest_period") or cat_data.get("latest_date"),
        }
        history = cat_data.get("history", [])
        factor_result["history"] = [
            {"period": h["period"], "value": h.get(factor_name)}
            for h in history if factor_name in h
        ]
        print(json.dumps(factor_result, ensure_ascii=False, indent=2))
        return

    print(json.dumps(result_data, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description='A股基本面指标分析')
    parser.add_argument('code', nargs='?', help='股票代码 (如 60****.SH, 000001.SZ)')
    parser.add_argument('--begin', type=int, default=20200101, help='K线开始日期 (默认: 20200101)')
    parser.add_argument('--end', type=int, default=None, help='K线结束日期 (默认: 今天)')
    parser.add_argument('--category', type=str, default='all',
                        help='指标类别 (profitability/growth/efficiency/earnings_quality/safety/'
                             'governance/valuation/shareholder/size/all)')
    parser.add_argument('--factor', type=str, default=None, help='单个指标名称 (如 净资产收益率TTM)')
    parser.add_argument('--list', action='store_true', help='列出所有可用指标')
    parser.add_argument('--output', type=str, default='json', choices=['json', 'table'],
                        help='输出格式 (json/table)')

    args = parser.parse_args()

    if args.end is None:
        args.end = int(datetime.now().strftime('%Y%m%d'))

    if args.list:
        run_analysis(None, None, None, list_factors=True)
        return

    if not args.code:
        parser.error('请提供股票代码，如: python run_fundamental_analysis.py 60****.SH')
        return

    run_analysis(args.code, args.begin, args.end, args.category, args.factor,
                 output_format=args.output)


if __name__ == '__main__':
    main()
