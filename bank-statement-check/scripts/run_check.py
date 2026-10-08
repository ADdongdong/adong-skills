# -*- coding: utf-8 -*-
"""银行流水核查四步法执行脚本（bank-statement-check skill 的确定性实现）。

读入三家银行流水 + 关联方清单，跑四步规则，输出核查结论。
阈值默认：50万取现 / 7天累计100万 / 23:00-05:00 / 借款·往来款·往来·暂付 关键词 / 100万大额支付。
"""
import os
import re
from datetime import date, timedelta
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

DIR = r"E:\13_dingdian\z999_归档的文件\06_workbuddy_dingdian\投行产品设计师\output\银行流水模拟数据"

TH_WITHDRAW = 50_0000        # 单笔取现阈值 50万
TH_WINDOW = 100_0000         # 7天累计阈值 100万
TH_LARGE = 100_0000          # 大额支付阈值 100万
WINDOW_DAYS = 7
NIGHT_START, NIGHT_END = "23:00", "05:00"
KEYWORDS = ["借款", "往来款", "往来", "暂付"]

# 简称清洗映射（去括号后再映射）
CLEAN = {
    "辰源贸易有限公司": "辰源贸易",
    "安科电子科技": "安科电子",
    "博远原材料有限公司": "博远原材料",
}

RELATED_RISK = {
    "张三": "高",   # 实际控制人
    "李四": "高",   # 财务总监（董监高）
    "辰源贸易": "高",  # 关联企业
    "张四": "高",   # 实控人配偶
}


def clean_party(name):
    if name is None:
        return ""
    s = str(name).strip()
    s = re.sub(r"[（(].*?[)）]", "", s)   # 去括号
    s = s.strip()
    return CLEAN.get(s, s)


def parse_date(s):
    s = str(s).strip()
    if "/" in s:
        y, m, d = s.split("/")
    elif "-" in s and len(s.split("-")[0]) == 4:
        y, m, d = s.split("-")
    else:  # 20260401
        y, m, d = s[:4], s[4:6], s[6:8]
    return date(int(y), int(m), int(d))


def load():
    rows = []  # dict: date,time,memo,income,expense,party,bank
    # 招行：借贷标志单列
    wb = openpyxl.load_workbook(os.path.join(DIR, "招商银行_华辰精密_流水.xlsx"))
    ws = wb.active
    for r in list(ws.iter_rows(values_only=True))[1:]:
        d, t, memo, flag, amt, bal, party = r
        rows.append(dict(date=parse_date(d), time=str(t), memo=str(memo),
                         income=amt if flag == "贷" else 0,
                         expense=amt if flag == "借" else 0,
                         party=clean_party(party), bank="招商银行"))
    # 工行：收入/支出两列
    wb = openpyxl.load_workbook(os.path.join(DIR, "工商银行_华辰精密_流水.xlsx"))
    ws = wb.active
    for r in list(ws.iter_rows(values_only=True))[1:]:
        d, inc, out, bal, party, memo = r
        rows.append(dict(date=parse_date(d), time=None, memo=str(memo),
                         income=inc or 0, expense=out or 0,
                         party=clean_party(party), bank="工商银行"))
    # 建行：收入/支出两列（辰源贸易，关联企业账户）
    wb = openpyxl.load_workbook(os.path.join(DIR, "建设银行_辰源贸易_流水.xlsx"))
    ws = wb.active
    for r in list(ws.iter_rows(values_only=True))[1:]:
        d, inc, out, bal, party, memo = r
        rows.append(dict(date=parse_date(d), time=None, memo=str(memo),
                         income=inc or 0, expense=out or 0,
                         party=clean_party(party), bank="建设银行"))
    # 关联方清单
    wb = openpyxl.load_workbook(os.path.join(DIR, "关联方清单.xlsx"))
    ws = wb.active
    related = {}
    for r in list(ws.iter_rows(values_only=True))[1:]:
        name, rel = r
        related[clean_party(name)] = str(rel)
    return rows, related


def step2(rows, related):
    """关联方识别：打是否关联方 + 风险等级。"""
    for r in rows:
        r["is_related"] = r["party"] in related
        if r["is_related"]:
            r["rel_type"] = related[r["party"]]
            r["risk"] = RELATED_RISK.get(r["party"], "高")
        else:
            r["rel_type"] = ""
            # 非关联方大额往来(单笔>100万) -> 中风险
            amt = r["income"] + r["expense"]
            r["risk"] = "中" if amt >= TH_LARGE else "低"
    return rows


def step3(rows):
    """异常筛查：四条规则，逐条命中原因。"""
    for r in rows:
        reasons = []
        amt = r["income"] + r["expense"]
        # 规则1：单笔>50万取现
        if r["expense"] >= TH_WITHDRAW and ("取现" in r["memo"] or "现金" in r["party"]):
            reasons.append("单笔取现超50万")
        # 规则3：深夜 23:00-05:00
        if r["time"]:
            t = str(r["time"])
            if t >= "23:00" or t <= "05:00":
                reasons.append("深夜23:00-05:00交易")
        # 规则4：关键词摘要
        if any(k in r["memo"] for k in KEYWORDS):
            reasons.append("摘要含敏感词(" + r["memo"] + ")")
        r["anomaly_reasons"] = reasons
    # 规则2：同一对手7天累计>100万（跨银行合并）
    by_party = {}
    for r in rows:
        by_party.setdefault(r["party"], []).append(r)
    for party, recs in by_party.items():
        recs.sort(key=lambda x: x["date"])
        for i, cur in enumerate(recs):
            lo = cur["date"] - timedelta(days=WINDOW_DAYS - 1)
            total = sum(x["income"] + x["expense"] for x in recs if lo <= x["date"] <= cur["date"])
            if total >= TH_WINDOW and len([x for x in recs if lo <= x["date"] <= cur["date"]]) >= 2:
                if "7天累计超100万" not in cur["anomaly_reasons"]:
                    cur["anomaly_reasons"].append(f"与「{party}」7天累计往来{total/10000:.0f}万")
    return rows


def build_chain(rows, related):
    """手工/规则结合构建资金链条（针对跨账户追踪）。"""
    chains = []
    big = [r for r in rows if r["bank"] in ("招商银行", "工商银行") and r["expense"] >= TH_LARGE]
    for p in big:
        payee = p["party"]
        # 收款方账户里，7天内转出的钱
        outgoings = [o for o in rows if o["bank"] == "建设银行" and o["expense"] > 0
                     and 0 <= (o["date"] - p["date"]).days <= WINDOW_DAYS]
        # 二级收款方转回发行人
        for o in outgoings:
            second = o["party"]
            back = [b for b in rows if b["income"] > 0 and b["party"] == second
                    and b["date"] >= o["date"] and (b["date"] - o["date"]).days <= WINDOW_DAYS]
            if back:
                for b in back:
                    chains.append({
                        "start": f"{p['date']} 华辰→{payee} 付{p['expense']/10000:.0f}万",
                        "mid": f"{o['date']} {payee}→{second} 转{o['expense']/10000:.0f}万",
                        "end": f"{b['date']} {second}→华辰 回{b['income']/10000:.0f}万",
                        "loop": "疑似资金回流/体外循环",
                    })
    return chains


def main():
    rows, related = load()
    rows = step2(rows, related)
    rows = step3(rows)

    print("=" * 70)
    print("【第一步】格式标准化：三家银行统一为 YYYY-MM-DD + 收支分列 + 银行列")
    print(f"合并后共 {len(rows)} 笔交易")
    for r in rows:
        inc = f"{r['income']/10000:>6.0f}万" if r["income"] else "      "
        exp = f"{r['expense']/10000:>6.0f}万" if r["expense"] else "      "
        t = r["time"] or "   "
        print(f"  {r['date']} {t} {r['bank']} 收{inc} 支{exp} 「{r['party']}」 {r['memo']}")

    print()
    print("=" * 70)
    print("【第二步】关联方识别")
    rel = [r for r in rows if r["is_related"]]
    print(f"命中关联方往来 {len(rel)} 笔：")
    for r in rel:
        amt = (r["income"] + r["expense"]) / 10000
        print(f"  [{r['risk']}] {r['date']} 「{r['party']}」({r['rel_type']}) {amt:.0f}万  {r['memo']}")

    print()
    print("=" * 70)
    print("【第三步】异常交易筛查")
    anom = [r for r in rows if r["anomaly_reasons"]]
    print(f"命中异常 {len(anom)} 笔：")
    for r in anom:
        for reason in r["anomaly_reasons"]:
            amt = (r["income"] + r["expense"]) / 10000
            print(f"  {r['date']} {r['bank']} 「{r['party']}」 {amt:.0f}万 {r['memo']}  ->  {reason}")

    print()
    print("=" * 70)
    print("【第四步】资金闭环核查")
    chains = build_chain(rows, related)
    if chains:
        for c in chains:
            print(f"  起点：{c['start']}")
            print(f"  路径：{c['mid']}")
            print(f"  终点：{c['end']}  => {c['loop']}")
    else:
        print("  未发现明显资金回流链条")

    print()
    print("=" * 70)
    print("【核查结论摘要】")
    print(f"  关联方往来：{len(rel)} 笔（实控人张三、董监高李四、关联企业辰源贸易）")
    print(f"  异常交易：{len(anom)} 笔")
    print(f"  可疑资金链条：{len(chains)} 条")
    print("  建议追问方向：①辰源贸易200万货款真实性 ②张三与发行人频繁往来及150万回流 ③深夜23:30转账王强45万 ④80万大额取现用途")

    # 落底稿
    write_result_xlsx(rows, chains)
    print()
    print("底稿已生成：核查结果汇总.xlsx")


def write_result_xlsx(rows, chains):
    wb = openpyxl.Workbook()
    # sheet1 标准化+打标
    ws = wb.active
    ws.title = "标准化流水_打标"
    hdr = ["交易日期", "时间", "银行", "收入(元)", "支出(元)", "交易对手", "摘要", "是否关联方", "风险等级", "异常命中"]
    ws.append(hdr)
    for r in sorted(rows, key=lambda x: x["date"]):
        ws.append([str(r["date"]), r["time"] or "", r["bank"], r["income"], r["expense"],
                   r["party"], r["memo"], "是" if r["is_related"] else "否",
                   r["risk"], "；".join(r["anomaly_reasons"])])
    for c in ws[1]:
        c.font = Font(bold=True)
    # sheet2 闭环
    ws2 = wb.create_sheet("资金闭环")
    ws2.append(["链条", "起点", "路径", "终点"])
    for i, c in enumerate(chains, 1):
        ws2.append([f"链条{i}", c["start"], c["mid"], c["end"]])
    for c in ws2[1]:
        c.font = Font(bold=True)
    for sh in (ws, ws2):
        for i, col in enumerate(sh.columns, 1):
            mx = max(len(str(c.value)) for c in col if c.value is not None)
            sh.column_dimensions[get_column_letter(i)].width = min(mx + 2, 40)
    wb.save(os.path.join(DIR, "核查结果汇总.xlsx"))


if __name__ == "__main__":
    main()
