# -*- coding: utf-8 -*-
"""生成"银行流水核查"skill 的打印版测试数据：4 家银行对账单 PDF（A4，可打印→扫描）+ 关联方清单。

场景（与 skill 四步埋点对应）：
- 发行人：华辰精密制造股份有限公司
- 实控人：张*栋（中行个人卡）；财务总监：李*敏；配偶：张*华；关联企业：辰源贸易有限公司
- 主要客户：安科电子科技有限公司（故意混用简称）；主要供应商：博远原材料（简称混用）

埋点（answer key 见 埋点说明.txt）：
1) 四家银行日期/列结构刻意不统一 -> 测试「格式标准化」
2) 与张*栋/李*敏/辰源贸易的往来、客户简称混用 -> 测试「关联方识别」
3) R1 取现 80万/62万、R2 张*栋 7天累计120万、R3 深夜23:30/23:40、R4 借款/往来款/备用金 -> 「异常筛查」
4) 华辰(4-10 付200万)->辰源(4-13 转150万给张*栋)->张*栋(4-13 转回华辰150万) -> 「资金闭环」

所有数据均为模拟生成，姓名/账号/证件号已打码，页脚带"测试样本"标识与模拟专用章。
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
import openpyxl
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

OUT = os.path.dirname(os.path.abspath(__file__))

# ---------------- 字体 ----------------
pdfmetrics.registerFont(TTFont("msyh", r"C:\Windows\Fonts\msyh.ttc", subfontIndex=0))
pdfmetrics.registerFont(TTFont("msyhbd", r"C:\Windows\Fonts\msyhbd.ttc", subfontIndex=0))
pdfmetrics.registerFont(TTFont("simhei", r"C:\Windows\Fonts\simhei.ttf"))

F = "msyh"
FB = "msyhbd"


def money(x):
    return f"{x:,.2f}"


# ---------------- 银行数据 ----------------
# 招商银行：华辰精密基本户（借贷标志单列 + 日期 2026-04-02 格式 + 含交易时间）
cmb_rows_raw = [
    ("2026-04-02", "10:12", "货款",   "贷", 500000,  "安科电子科技有限公司", "6222 08** **** 1194"),
    ("2026-04-03", "14:30", "材料款", "借", 300000,  "博远原材料有限公司",   "6222 08** **** 2703"),
    ("2026-04-05", "09:20", "工资",   "借", 185000,  "代发工资户",           "————"),
    ("2026-04-06", "16:45", "往来款", "借", 600000,  "张*栋",                "6216 61** **** 7412"),
    ("2026-04-08", "11:00", "货款",   "贷", 800000,  "安科电子",             "6222 08** **** 1194"),
    ("2026-04-10", "15:00", "货款",   "借", 2000000, "辰源贸易有限公司",     "6217 50** **** 0533"),
    ("2026-04-11", "23:30", "转账",   "借", 450000,  "王*",                  "6228 48** **** 0266"),
    ("2026-04-12", "10:00", "借款",   "借", 900000,  "张*栋",                "6216 61** **** 7412"),
    ("2026-04-13", "09:15", "往来款", "贷", 1500000, "张*栋",                "6216 61** **** 7412"),
    ("2026-04-14", "13:20", "取现",   "借", 800000,  "本行现金",             "————"),
    ("2026-04-15", "17:00", "税费",   "借", 260000,  "国家税务总局××市税务局", "————"),
    ("2026-04-16", "10:30", "货款",   "贷", 650000,  "安科电子(本部)",       "6222 08** **** 1194"),
    ("2026-04-18", "11:20", "往来款", "贷", 300000,  "李*敏",                "6217 00** **** 5561"),
    ("2026-04-20", "15:40", "材料款", "借", 280000,  "博远原材料",           "6222 08** **** 2703"),
    ("2026-04-22", "09:30", "货款",   "贷", 520000,  "安科电子科技有限公司", "6222 08** **** 1194"),
]
cmb_rows, bal = [], 5000000.0
for d, t, memo, flag, amt, party, pacct in cmb_rows_raw:
    bal += amt if flag == "贷" else -amt
    cmb_rows.append([d, t, memo, flag, money(amt), money(bal), party, pacct])
cmb_in = sum(float(r[4].replace(",", "")) for r in cmb_rows if r[3] == "贷")
cmb_out = sum(float(r[4].replace(",", "")) for r in cmb_rows if r[3] == "借")

# 工商银行：华辰精密一般户（收入/支出两列 + 日期 20260402 无分隔 + 无交易时间）
icbc_rows_raw = [
    ("20260401", "货款",   "安科电子科技有限公司", "6222 08** **** 1194", 800000,  0),
    ("20260403", "采购款", "博远原材料有限公司",   "6222 08** **** 2703", 0,       350000),
    ("20260407", "往来款", "张*栋",                "6216 61** **** 7412", 0,       400000),
    ("20260409", "往来款", "张*栋",                "6216 61** **** 7412", 0,       400000),
    ("20260411", "往来款", "张*栋",                "6216 61** **** 7412", 0,       400000),
    ("20260415", "报销",   "李*敏",                "6217 00** **** 5561", 0,       200000),
    ("20260418", "货款",   "安科电子",             "6222 08** **** 1194", 1200000, 0),
    ("20260420", "服务费", "辰源贸易",             "6217 50** **** 0533", 0,       150000),
    ("20260423", "备用金", "本行现金",             "————",                0,       60000),
    ("20260425", "货款",   "安科电子科技有限公司", "6222 08** **** 1194", 500000,  0),
]
icbc_rows, bal = [], 3000000.0
for d, memo, party, pacct, inc, out in icbc_rows_raw:
    bal += inc - out
    icbc_rows.append([d, memo, party, pacct, money(inc), money(out), money(bal)])
icbc_in = sum(float(r[4].replace(",", "")) for r in icbc_rows)
icbc_out = sum(float(r[5].replace(",", "")) for r in icbc_rows)

# 建设银行：辰源贸易/关联企业（日期 2026/4/10 斜杠格式，列顺序不同）
ccb_rows_raw = [
    ("2026/4/10", "14:05", "华辰精密制造股份有限公司", "货款",   2000000, 0),
    ("2026/4/13", "10:22", "张*栋",                    "往来款", 0,       1500000),
    ("2026/4/16", "09:47", "博远原材料",               "材料款", 0,       450000),
    ("2026/4/18", "15:31", "华辰精密制造股份有限公司", "回款",   600000,  0),
    ("2026/4/20", "11:08", "张*栋",                    "往来款", 0,       500000),
]
ccb_rows, bal = [], 1000000.0
for d, t, party, memo, inc, out in ccb_rows_raw:
    bal += inc - out
    ccb_rows.append([d, t, party, memo, money(inc), money(out), money(bal)])
ccb_in = sum(float(r[4].replace(",", "")) for r in ccb_rows)
ccb_out = sum(float(r[5].replace(",", "")) for r in ccb_rows)

# 中国银行：张*栋 个人卡（转出/转入列 + 交易类型列，补 R1 取现 / R3 深夜 / 配偶往来）
boc_rows_raw = [
    ("2026-04-07", "10:05", "转账", "华辰精密制造股份有限公司", "往来款",  0,       600000),
    ("2026-04-09", "14:22", "转账", "张*华",                    "家庭支出", 200000, 0),
    ("2026-04-13", "09:15", "转账", "华辰精密制造股份有限公司", "往来款",  1500000, 0),
    ("2026-04-13", "16:50", "转账", "辰源贸易有限公司",         "往来款",  0,       1500000),
    ("2026-04-14", "23:40", "转账", "王*",                      "其他",    600000,  0),
    ("2026-04-15", "10:30", "取现", "本行现金",                 "备用金",  620000,  0),
    ("2026-04-19", "09:12", "理财", "恒益资产管理有限公司",     "产品申购", 300000, 0),
    ("2026-04-21", "20:15", "代发", "华辰精密制造股份有限公司", "工资",    0,       50000),
]
boc_rows, bal = [], 2000000.0
for d, t, typ, party, memo, out, inc in boc_rows_raw:
    bal += inc - out
    boc_rows.append([d, t, typ, party, memo, money(out), money(inc), money(bal)])
boc_in = sum(float(r[6].replace(",", "")) for r in boc_rows)
boc_out = sum(float(r[5].replace(",", "")) for r in boc_rows)

BANKS = [
    dict(
        file="招商银行_华辰精密_对账单.pdf",
        bank="招商银行", sub="CMB UNITS 对私客户历史交易明细",
        color=colors.HexColor("#B01F24"), headbg=colors.HexColor("#FBE9EA"),
        acct_name="华辰精密制造股份有限公司", acct_no="7559 21** **** 3621",
        open_bal=5000000.0, close_bal=float(cmb_rows[-1][5].replace(",", "")),
        cols=["交易日期", "交易时间", "摘要", "借贷", "交易金额(元)", "账户余额(元)", "对方户名", "对方账号"],
        widths=[22*mm, 15*mm, 16*mm, 10*mm, 26*mm, 28*mm, 34*mm, 33*mm],
        rows=cmb_rows,
        total="本页合计  借方(支出) %s 元   贷方(收入) %s 元" % (money(cmb_out), money(cmb_in)),
        note="借贷标志说明：借=资金流出账户，贷=资金流入账户。",
    ),
    dict(
        file="工商银行_华辰精密_对账单.pdf",
        bank="中国工商银行", sub="客户存款对账单",
        color=colors.HexColor("#C8000A"), headbg=colors.HexColor("#FDECEA"),
        acct_name="华辰精密制造股份有限公司", acct_no="0200 12** **** 8876",
        open_bal=3000000.0, close_bal=float(icbc_rows[-1][6].replace(",", "")),
        cols=["交易日期", "摘要", "对方户名", "对方账号", "收入(元)", "支出(元)", "余额(元)"],
        widths=[24*mm, 16*mm, 42*mm, 38*mm, 26*mm, 26*mm, 28*mm],
        rows=icbc_rows,
        total="本页合计  收入 %s 元   支出 %s 元" % (money(icbc_in), money(icbc_out)),
        note="本对账单日期格式为 YYYYMMDD。",
    ),
    dict(
        file="建设银行_辰源贸易_对账单.pdf",
        bank="中国建设银行", sub="对私客户账户明细清单",
        color=colors.HexColor("#0066B3"), headbg=colors.HexColor("#E7F0F9"),
        acct_name="辰源贸易有限公司", acct_no="6217 50** **** 0533",
        open_bal=1000000.0, close_bal=float(ccb_rows[-1][6].replace(",", "")),
        cols=["交易日期", "交易时间", "对方户名", "摘要", "收入(元)", "支出(元)", "余额(元)"],
        widths=[24*mm, 16*mm, 52*mm, 16*mm, 26*mm, 26*mm, 28*mm],
        rows=ccb_rows,
        total="本页合计  收入 %s 元   支出 %s 元" % (money(ccb_in), money(ccb_out)),
        note="",
    ),
    dict(
        file="中国银行_张栋_个人流水.pdf",
        bank="中国银行", sub="个人活期存款交易明细单",
        color=colors.HexColor("#A6093D"), headbg=colors.HexColor("#FAE8EE"),
        acct_name="张*栋", acct_no="6216 61** **** 7412",
        open_bal=2000000.0, close_bal=float(boc_rows[-1][7].replace(",", "")),
        cols=["交易日期", "交易时间", "交易类型", "对方户名", "摘要", "转出(元)", "转入(元)", "余额(元)"],
        widths=[22*mm, 15*mm, 14*mm, 42*mm, 16*mm, 25*mm, 25*mm, 25*mm],
        rows=boc_rows,
        total="本页合计  转入 %s 元   转出 %s 元" % (money(boc_in), money(boc_out)),
        note="交易类型说明：转账/取现/理财/代发。",
    ),
]

# ---------------- 渲染 ----------------
TITLE = ParagraphStyle("t", fontName=FB, fontSize=10.5, alignment=TA_CENTER, spaceAfter=2)
CELL = ParagraphStyle("c", fontName=F, fontSize=7.6, leading=10)
CELLR = ParagraphStyle("cr", parent=CELL, alignment=TA_RIGHT)
CELLC = ParagraphStyle("cc", parent=CELL, alignment=TA_CENTER)


def footer_and_stamp(canvas, doc):
    canvas.saveState()
    w, h = A4
    # 页脚
    canvas.setFont(F, 7)
    canvas.setFillColor(colors.HexColor("#888888"))
    canvas.drawString(15*mm, 12*mm, "测试样本：本对账单交易数据为模拟生成，姓名/账号已脱敏，仅用于系统功能测试，不作为任何真实交易凭证。")
    canvas.drawRightString(w - 15*mm, 12*mm, "第 %d 页" % doc.page)
    # 模拟业务专用章（红色圆章）
    cx, cy, r = w - 42*mm, 42*mm, 17*mm
    canvas.setStrokeColor(colors.Color(0.78, 0.12, 0.12, alpha=0.85))
    canvas.setFillColor(colors.Color(0.78, 0.12, 0.12, alpha=0.85))
    canvas.setLineWidth(1.6)
    canvas.circle(cx, cy, r, stroke=1, fill=0)
    canvas.setLineWidth(0.6)
    canvas.circle(cx, cy, r - 2.2, stroke=1, fill=0)
    canvas.setFont(FB, 8)
    canvas.drawCentredString(cx, cy + 4.2*mm, "模拟业务")
    canvas.drawCentredString(cx, cy - 1.2*mm, "专用章")
    canvas.setFont(F, 5.5)
    canvas.drawCentredString(cx, cy - 8*mm, "仅供测试 · 非真实凭证")
    # 五角星
    import math
    pts = []
    for i in range(10):
        ang = math.pi / 2 + i * math.pi / 5
        rad = 2.6*mm if i % 2 == 0 else 1.1*mm
        pts.append((cx + rad * math.cos(ang), cy + 7.5*mm + rad * math.sin(ang)))
    p = canvas.beginPath()
    p.moveTo(*pts[0])
    for pt in pts[1:]:
        p.lineTo(*pt)
    p.close()
    canvas.drawPath(p, stroke=0, fill=1)
    canvas.restoreState()


def render(b):
    doc = SimpleDocTemplate(os.path.join(OUT, b["file"]), pagesize=A4,
                            leftMargin=15*mm, rightMargin=15*mm, topMargin=14*mm, bottomMargin=18*mm,
                            title="%s对账单(测试样本)" % b["bank"], author="测试数据生成器")
    story = []
    # 表头：银行名 + 产品名
    story.append(Paragraph('<font size="16" color="%s"><b>%s</b></font>' % ("#" + b["color"].hexval()[2:], b["bank"]),
                           ParagraphStyle("bn", fontName=FB, fontSize=16, leading=22, alignment=TA_CENTER, spaceAfter=2)))
    story.append(Paragraph(b["sub"], ParagraphStyle("sb", parent=TITLE, textColor=colors.HexColor("#555555"))))
    story.append(Spacer(1, 3))
    # 账户信息块
    info = Table([
        ["客户名称", b["acct_name"], "账　　号", b["acct_no"]],
        ["币　　种", "人民币（本位币）", "对账周期", "2026-04-01 至 2026-04-30"],
        ["期初余额", money(b["open_bal"]) + " 元", "打印日期", "2026-09-01"],
    ], colWidths=[24*mm, 70*mm, 24*mm, 62*mm])
    info.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), F), ("FONTSIZE", (0, 0), (-1, -1), 8.2),
        ("FONTNAME", (0, 0), (0, -1), FB), ("FONTNAME", (2, 0), (2, -1), FB),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FAFAFA")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#BBBBBB")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    story.append(info)
    story.append(Spacer(1, 5))
    # 主表
    header = [Paragraph('<font color="#333333"><b>%s</b></font>' % c, CELLC) for c in b["cols"]]
    data = [header] + b["rows"]
    aligns = []
    for i, c in enumerate(b["cols"]):
        if "元" in c:
            aligns.append("RIGHT")
        elif c in ("借贷", "交易时间", "交易日期", "交易类型"):
            aligns.append("CENTER")
        else:
            aligns.append("LEFT")
    tstyle = [
        ("FONTNAME", (0, 0), (-1, -1), F), ("FONTSIZE", (0, 0), (-1, -1), 7.6),
        ("FONTNAME", (0, 0), (-1, 0), FB),
        ("BACKGROUND", (0, 0), (-1, 0), b["headbg"]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CFCFCF")),
        ("TOPPADDING", (0, 0), (-1, -1), 2.4), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.4),
        ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F7F7")]),
    ]
    for i, a in enumerate(aligns):
        tstyle.append(("ALIGN", (i, 0), (i, -1), a))
    main = Table(data, colWidths=b["widths"], repeatRows=1, style=TableStyle(tstyle))
    story.append(main)
    story.append(Spacer(1, 5))
    # 合计行
    close = b["close_bal"]
    tot = Table([[Paragraph('<b>%s</b>' % b["total"], ParagraphStyle("tt", parent=CELL, fontSize=8)),
                  Paragraph('<b>期末余额： %s 元</b>' % money(close), ParagraphStyle("te", parent=CELLR, fontSize=8))]],
                colWidths=[122*mm, 72*mm])
    tot.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F0F0F0")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#999999")),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(tot)
    story.append(Spacer(1, 4))
    if b["note"]:
        story.append(Paragraph(b["note"], ParagraphStyle("n", fontName=F, fontSize=7.5, textColor=colors.HexColor("#666666"))))
    story.append(Paragraph("经办：0001　　复核：0002　　机构号：测试网点 0110", ParagraphStyle("o", fontName=F, fontSize=7.5, textColor=colors.HexColor("#666666"))))
    doc.build(story, onFirstPage=footer_and_stamp, onLaterPages=footer_and_stamp)
    print("OK", b["file"])


for b in BANKS:
    render(b)

# ---------------- 关联方清单 ----------------
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "关联方清单"
ws.append(["关联方名称", "关联关系", "证件号码（已打码）"])
for c in ws[1]:
    c.font = Font(bold=True)
    c.fill = PatternFill("solid", fgColor="D9E1F2")
for r in [
    ("张*栋", "实际控制人", "3501**********1234"),
    ("李*敏", "财务总监（董监高）", "3501**********5678"),
    ("张*华", "实控人配偶", "3501**********9012"),
    ("辰源贸易有限公司", "关联企业（实控人控制）", "91350100MA****XY3F"),
]:
    ws.append(list(r))
for i, col in enumerate(ws.columns, 1):
    ws.column_dimensions[get_column_letter(i)].width = max(len(str(c.value or "")) + 4, 14)
wb.save(os.path.join(OUT, "关联方清单.xlsx"))
print("OK 关联方清单.xlsx")
print("DONE:", os.listdir(OUT))
