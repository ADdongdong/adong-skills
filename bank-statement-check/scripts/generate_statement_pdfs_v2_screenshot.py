# -*- coding: utf-8 -*-
"""按用户提供的 4 张真实截图版式，生成银行流水核查 skill 的打印版测试数据（v2）。

复刻版式（严格对照截图）：
1) 招商银行 户口历史交易明细表（横版，无余额列，粉色顶带，客户协议号列）
2) 中国农业银行 银行卡交易明细清单（竖版，日期 YYYYMMDD，交易地点/对方账号和户名列）
3) 中国工商银行 理财金账户历史明细清单（横版，工作日期/渠道/序号/币种/钞汇/地区，金额带+/-）
4) 中国农业银行 金穗借记卡明细对账单（横版虚线框，打印机构/柜员/页码头）

场景（与 v1 一致）：实控人 张*栋、财务总监 李*敏、配偶 张*华、关联企业 辰源贸易、
主要客户 安科电子、相关人员 王*。账户：李*敏招行个人卡、张*栋工行理财金账户、
张*华农行卡、王*农行借记卡。

埋点（answer key）：
- R1 大额取现：工行 ATM取款 -520,000（04-15）
- R2 高频往来：李*敏招行 4-06/4-08/4-10 收张*栋 45+40+35=120万（7天）；
  张*栋工行 与辰源贸易 4-06 支60万、4-13 收150万（7天累计210万）；
  张*栋工行 与王* 4-11 支45万、4-14 支60万（7天累计105万）
- R3 深夜交易：工行 04-11 23:52 卡取、04-14 23:39 转支；农行对账单 04-14 23:40 网银转账 +600,000
- R4 敏感摘要：农行清单 04-12 摘要"借款"；农行清单 04-25 摘要"往来款"
- 资金闭环：张*栋(4-06 支60万→辰源)→(4-13 收150万)→(4-14 支150万→华辰精密)；
  张*栋(4-14 23:39 支60万→王*)；张*栋(4-09 中行? 无，本批为 4-12 支90万→李*敏，
  李*敏 4-06~4-10 收张*栋 120万，4-15 支20万→张*华)

所有数据为模拟生成，姓名/账号已打码，页脚带"测试样本"标识。
"""
import os
import math
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

OUT = os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUT, exist_ok=True)

pdfmetrics.registerFont(TTFont("msyh", r"C:\Windows\Fonts\msyh.ttc", subfontIndex=0))
pdfmetrics.registerFont(TTFont("msyhbd", r"C:\Windows\Fonts\msyhbd.ttc", subfontIndex=0))
pdfmetrics.registerFont(TTFont("simhei", r"C:\Windows\Fonts\simhei.ttf"))
pdfmetrics.registerFont(TTFont("simsun", r"C:\Windows\Fonts\simsun.ttc", subfontIndex=0))
pdfmetrics.registerFont(TTFont("simsunbd", r"C:\Windows\Fonts\simsun.ttc", subfontIndex=1))  # 新宋体当粗体

FS = "simsun"      # 正文宋体（接近打印扫描件）
FSG = "simsunbd"   # 表头/强调
FH = "simhei"      # 标题黑体
FY = "msyh"        # 辅助

RED = colors.Color(0.78, 0.12, 0.12, alpha=0.85)
GRAY = colors.HexColor("#888888")


def money(x, signed=False):
    if signed:
        return ("+" if x > 0 else "") + f"{x:,.2f}"
    return f"{x:,.2f}"


def stamp(canvas, cx_mm, cy_mm, r_mm=17):
    cx, cy, r = cx_mm * mm, cy_mm * mm, r_mm * mm
    canvas.setStrokeColor(RED)
    canvas.setFillColor(RED)
    canvas.setLineWidth(1.6)
    canvas.circle(cx, cy, r, stroke=1, fill=0)
    canvas.setLineWidth(0.6)
    canvas.circle(cx, cy, r - 2.2, stroke=1, fill=0)
    canvas.setFont("msyhbd", 8)
    canvas.drawCentredString(cx, cy + 4.2 * mm, "模拟业务")
    canvas.drawCentredString(cx, cy - 1.2 * mm, "专用章")
    canvas.setFont("msyh", 5.5)
    canvas.drawCentredString(cx, cy - 8 * mm, "仅供测试 · 非真实凭证")
    pts = []
    for i in range(10):
        ang = math.pi / 2 + i * math.pi / 5
        rad = 2.6 * mm if i % 2 == 0 else 1.1 * mm
        pts.append((cx + rad * math.cos(ang), cy + 7.5 * mm + rad * math.sin(ang)))
    p = canvas.beginPath()
    p.moveTo(*pts[0])
    for pt in pts[1:]:
        p.lineTo(*pt)
    p.close()
    canvas.drawPath(p, stroke=0, fill=1)


def test_note(canvas, page_label="1/1"):
    w = landscape(A4)[0] if landscape(A4)[0] else 0
    canvas.setFont("msyh", 6.5)
    canvas.setFillColor(GRAY)
    canvas.drawString(15 * mm, 8 * mm, "测试样本：本清单交易数据为模拟生成，姓名/账号已脱敏，仅用于系统功能测试，不作为任何真实交易凭证。")
    canvas.drawRightString(282 * mm, 8 * mm, page_label)


# ============================ 数据 ============================
# ---- 1) 招商银行 李*敏 户口历史交易明细表（无余额列，金额不分正负）----
cmb_rows = [
    ("2026/04/02", "CNY", 82000,   "工资", "网上代发代扣", "华辰精密制造股份有限公司"),
    ("2026/04/06", "CNY", 450000,  "转账", "网上代发代扣", "张*栋"),
    ("2026/04/08", "CNY", 400000,  "转账", "网上代发代扣", "张*栋"),
    ("2026/04/10", "CNY", 350000,  "转账", "网上代发代扣", "张*栋"),
    ("2026/04/12", "CNY", 156000,  "奖金", "网上代发代扣", "华辰精密制造股份有限公司"),
    ("2026/04/15", "CNY", 200000,  "转账", "网上代发代扣", "张*华"),
    ("2026/04/16", "CNY", 3200,    "缴费", "网上代发代扣", "中国移动××分公司"),
    ("2026/04/18", "CNY", 300000,  "转账", "网上代发代扣", "华辰精密制造股份有限公司"),
    ("2026/04/22", "CNY", 500000,  "转账", "网上代发代扣", "辰源贸易有限公司"),
    ("2026/04/25", "CNY", 82000,   "工资", "网上代发代扣", "华辰精密制造股份有限公司"),
]
# 方向：招行版式不标正负；这里约定：付给对方(工资/缴费/转出)为支出。为了测试解析器
# 不给方向提示，仅 2026/04/15、04/16、04/22 三行为支出（answer key 说明）。
cmb_pay_out = {"2026/04/15", "2026/04/16", "2026/04/22"}

# ---- 2) 工商银行 张*栋 理财金账户历史明细清单 ----
icbc_start = 985000.00
icbc_rows_raw = [
    # 日期 时间 对方账号 对方户名 摘要 金额(±)
    ("2026-04-02", "100412", "————",             "————",         "卡存",     +2000000),
    ("2026-04-06", "163018", "6217 50** **** 0533", "辰源贸易有限公司", "转支", -600000),
    ("2026-04-08", "110236", "6222 08** **** 1194", "安科电子",        "转存", +800000),
    ("2026-04-11", "235241", "6228 48** **** 0266", "王*",             "卡取", -450000),
    ("2026-04-12", "100005", "6217 00** **** 5561", "李*敏",           "转支", -900000),
    ("2026-04-13", "165000", "6217 50** **** 0533", "辰源贸易有限公司", "卡存", +1500000),
    ("2026-04-14", "093012", "0200 12** **** 8876", "华辰精密制造股份有限公司", "转支", -1500000),
    ("2026-04-14", "233955", "6228 48** **** 0266", "王*",             "转支", -600000),
    ("2026-04-15", "103045", "————",             "————",         "ATM取款", -520000),
    ("2026-04-19", "091230", "6666 88** **** 0271", "恒益资产管理有限公司", "转支", -300000),
    ("2026-04-21", "201540", "0200 12** **** 8876", "华辰精密制造股份有限公司", "转存", +50000),
]
icbc_rows, bal = [], icbc_start
for d, t, acct, name, memo, amt in icbc_rows_raw:
    bal += amt
    icbc_rows.append((d, t, acct, name, "柜面", "0", "RMB", "钞", memo, "0405", money(amt, signed=True), money(bal)))

# ---- 3) 农业银行 张*华 银行卡交易明细清单 ----
abc1_start = 26318.00
abc1_rows_raw = [
    # 日期 摘要 金额(±) 交易地点/对方账号和户名
    ("20260402", "现存",     +6500,    "6228 4801 6847 0007"),
    ("20260404", "ATM取款",  -4000,    "159998"),
    ("20260409", "网银转账", +200000,  "6216 61** **** 7412 张*栋"),
    ("20260412", "借款",     -120000,  "6228 48** **** 0266 王*"),
    ("20260413", "支付宝",   +1435,    "9663019400500307"),
    ("20260416", "现存",     +5300,    "159999"),
    ("20260418", "往来款",   -80000,   "6217 00** **** 5561 李*敏"),
    ("20260421", "ATM取款",  -5000,    "159998"),
    ("20260425", "短信费",   -2,       "9663019400500307"),
    ("20260428", "结息",     +9.38,    "159999--中心入帐"),
    ("20260428", "利息税",   0.00,     "159999--中心入帐"),
]
abc1_rows, bal = [], abc1_start
for d, memo, amt, where in abc1_rows_raw:
    bal += amt
    abc1_rows.append((d, memo, money(amt), money(bal), where))

# ---- 4) 农业银行 王* 金穗借记卡明细对账单 ----
abc2_start = 79560.00
abc2_rows_raw = [
    ("20260403", "090545", "转支",     -510.00),
    ("20260405", "114112", "超级网银", +3300.00),
    ("20260408", "101916", "转存",     +6800.00),
    ("20260411", "104112", "转支",     -10600.00),
    ("20260414", "234000", "网银转账", +600000.00),  # 深夜，来自张*栋
    ("20260417", "133854", "转存",     +450000.00),  # 辰源贸易
    ("20260419", "091242", "转支",     -300000.00),
    ("20260423", "155716", "现支",     -4000.00),
    ("20260424", "101746", "手续费",   -10.00),
    ("20260426", "084230", "转存",     +2000.00),
    ("20260428", "154610", "转支",     -500.00),
]
abc2_rows, bal = [], abc2_start
for d, t, memo, amt in abc2_rows_raw:
    bal += amt
    abc2_rows.append((d, t, memo, money(amt), money(bal)))


# ============================ 通用构件 ============================
def base_table(rows, widths, aligns, header=None, headbg=None, dashed=False, font_size=8):
    data = []
    if header:
        data.append([Paragraph('<b>%s</b>' % h, ParagraphStyle("h", fontName=FSG, fontSize=font_size, alignment=TA_CENTER)) for h in header])
    data += [list(r) for r in rows]
    cmds = [
        ("FONTNAME", (0, 0), (-1, -1), FS), ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("FONTNAME", (0, 0), (-1, 0), FSG) if header else ("FONTNAME", (0, 0), (0, -1), FS),
        ("TOPPADDING", (0, 0), (-1, -1), 2.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.6),
        ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    if header:
        cmds.append(("BACKGROUND", (0, 0), (-1, 0), headbg or colors.HexColor("#F2F2F2")))
    # 截图复刻：表格内部无横线竖线；仅保留整表级装饰线（表头上下线 + 表尾线，横线 only）
    if header and not dashed:
        cmds.append(("LINEABOVE", (0, 0), (-1, 0), 0.9, colors.HexColor("#555555")))
        cmds.append(("LINEBELOW", (0, 0), (-1, 0), 0.9, colors.HexColor("#555555")))
    if not dashed:
        cmds.append(("LINEBELOW", (0, -1), (-1, -1), 0.9, colors.HexColor("#555555")))
    for i, a in enumerate(aligns):
        cmds.append(("ALIGN", (i, 0), (i, -1), a))
    return Table(data, colWidths=widths, repeatRows=1 if header else 0, style=TableStyle(cmds))


def kv_line(pairs, width_mm, label_font=FSG):
    """一行 '标签: 值' 组合，无边框。"""
    cells, widths = [], []
    for label, value, w in pairs:
        cells.append(Paragraph("<b>%s</b>：%s" % (label, value),
                               ParagraphStyle("kv", fontName=FS, fontSize=8.4)))
        widths.append(w * mm)
    t = Table([cells], colWidths=widths)
    t.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 1.2), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


# ============================ 1) 招商银行 ============================
def gen_cmb():
    from reportlab.lib.pagesizes import landscape
    PAGE = landscape(A4)
    file = os.path.join(OUT, "1_招商银行_户口历史交易明细表_李敏.pdf")

    def on_page(canv, doc):
        canv.saveState()
        w, h = PAGE
        # 顶部粉色带
        canv.setFillColor(colors.HexColor("#D98B93"))
        canv.rect(0, h - 9 * mm, w, 9 * mm, stroke=0, fill=1)
        canv.setFillColor(colors.HexColor("#F3C7CB"))
        canv.rect(0, h - 10.2 * mm, w, 1.2 * mm, stroke=0, fill=1)
        # 右上 logo（带内白字）
        canv.setFillColor(colors.white)
        canv.setFont("simhei", 15)
        canv.drawRightString(w - 14 * mm, h - 6.8 * mm, "招商银行")
        canv.setFont("msyh", 5.5)
        canv.drawCentredString(w - 21 * mm, h - 3 * mm, "CHINA MERCHANTS BANK")
        test_note(canv)
        stamp(canv, 236, 118, 16)
        canv.restoreState()

    doc = SimpleDocTemplate(file, pagesize=PAGE, leftMargin=14 * mm, rightMargin=14 * mm,
                            topMargin=14 * mm, bottomMargin=14 * mm,
                            title="招商银行户口历史交易明细表(测试样本)")
    story = []
    story.append(Paragraph("招商银行户口历史交易明细表",
                           ParagraphStyle("t", fontName=FH, fontSize=14.5, alignment=TA_CENTER, spaceAfter=4)))
    story.append(kv_line([
        ("日　期", '<font color="#BBBBBB">2***33019</font>', 52),
        ("受理行", "××分行××支行", 78),
        ("开 户 行", "××分行××支行", 70),
    ], 267))
    story.append(kv_line([
        ("货　币", "人民币", 52),
        ("凭证种类", "一卡通 M+IC卡", 78),
        ("账户号码", "1219 30** **** 3421", 70),
    ], 267))
    story.append(kv_line([
        ("查询类型", "代发账户", 52),
        ("账号类型", "一卡通", 78),
        ("交易时间", "2026/03/01~2026/04/30", 70),
    ], 267))
    story.append(Spacer(1, 4))
    header = ["记账日期", "交易币种", "交易金额", "交易摘要代理名称", "交易附言", "客户协议号", "对手名称"]
    rows = []
    for d, cur, amt, memo, postscript, party in cmb_rows:
        rows.append((d, cur, money(amt), memo, postscript, "336901", party))
    t = base_table(rows,
                   [26 * mm, 18 * mm, 28 * mm, 34 * mm, 32 * mm, 26 * mm, 103 * mm],
                   ["CENTER", "CENTER", "RIGHT", "CENTER", "CENTER", "CENTER", "LEFT"],
                   header=header, headbg=colors.HexColor("#FBEDEE"))
    story.append(t)
    story.append(Spacer(1, 6))
    foot = Table([[
        Paragraph("经办用户：115326", ParagraphStyle("f1", fontName=FS, fontSize=8)),
        Paragraph("页码：1 / 1", ParagraphStyle("f2", fontName=FS, fontSize=8, alignment=TA_CENTER)),
        Paragraph("招商银行股份有限公司", ParagraphStyle("f3", fontName=FS, fontSize=8, alignment=TA_RIGHT)),
    ]], colWidths=[80 * mm, 107 * mm, 80 * mm])
    foot.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    story.append(foot)
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print("OK", os.path.basename(file))


# ============================ 2) 工商银行 ============================
def gen_icbc():
    from reportlab.lib.pagesizes import landscape
    PAGE = landscape(A4)
    file = os.path.join(OUT, "2_工商银行_理财金账户历史明细清单_张栋.pdf")

    def on_page(canv, doc):
        canv.saveState()
        test_note(canv)
        stamp(canv, 250, 74, 15)
        canv.restoreState()

    doc = SimpleDocTemplate(file, pagesize=PAGE, leftMargin=12 * mm, rightMargin=12 * mm,
                            topMargin=12 * mm, bottomMargin=14 * mm,
                            title="工商银行理财金账户历史明细清单(测试样本)")
    story = []
    head = Table([[
        Paragraph('<font color="#C8000A" size="13"><b>ICBC 中国工商银行</b></font>',
                  ParagraphStyle("lg", fontName=FH, alignment=TA_LEFT)),
        Paragraph('<font color="#999999">凭证</font>',
                  ParagraphStyle("vch", fontName=FS, fontSize=10, alignment=TA_RIGHT)),
    ]], colWidths=[200 * mm, 67 * mm])
    head.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
    story.append(head)
    story.append(Paragraph("理财金账户历史明细清单",
                           ParagraphStyle("t", fontName=FH, fontSize=13, alignment=TA_CENTER, spaceBefore=2, spaceAfter=3)))
    story.append(kv_line([
        ("××路支行", "", 44),
        ("柜员号", "000704", 40),
        ("起始日期", "2026-04-01", 44),
        ("结束日期", "2026-04-30", 44),
        ("打印时间", "10:21:36", 95),
    ], 267))
    story.append(kv_line([
        ("卡号", "6222 30** **** 1187", 84),
        ("户名", "张*栋", 60),
        ("币种", "RMB（人民币）", 123),
    ], 267))
    story.append(Spacer(1, 3))
    header = ["工作日期", "工作时间", "对方账户账号", "对方账户名", "渠道", "序号", "币种", "钞汇", "摘要", "地区", "收入/卖出金额", "余额"]
    t = base_table(icbc_rows,
                   [21 * mm, 17 * mm, 34 * mm, 42 * mm, 11 * mm, 9 * mm, 11 * mm, 9 * mm, 18 * mm, 11 * mm, 32 * mm, 30 * mm],
                   ["CENTER", "CENTER", "CENTER", "LEFT", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "RIGHT", "RIGHT"],
                   header=header, headbg=colors.HexColor("#FDECEA"), dashed=True, font_size=7.8)
    t.hAlign = "LEFT"
    # 表头上下虚线（模拟截图针式打印风）
    t.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 1.1, colors.HexColor("#444444"), None, (3, 2)),
        ("LINEBELOW", (0, 0), (-1, 0), 0.7, colors.HexColor("#444444"), None, (2, 2)),
    ]))
    story.append(t)
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print("OK", os.path.basename(file))


# ============================ 3) 农业银行 银行卡交易明细清单 ============================
def gen_abc1():
    PAGE = A4
    file = os.path.join(OUT, "3_农业银行_银行卡交易明细清单_张华.pdf")

    def on_page(canv, doc):
        canv.saveState()
        canv.setFont("msyh", 6.5)
        canv.setFillColor(GRAY)
        canv.drawString(15 * mm, 8 * mm, "测试样本：本清单交易数据为模拟生成，姓名/账号已脱敏，仅用于系统功能测试，不作为任何真实交易凭证。")
        canv.drawRightString(195 * mm, 8 * mm, "第 1 页")
        stamp(canv, 150, 165, 16)
        canv.restoreState()

    doc = SimpleDocTemplate(file, pagesize=PAGE, leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=14 * mm, bottomMargin=14 * mm,
                            title="农业银行银行卡交易明细清单(测试样本)")
    story = []
    story.append(Paragraph("中国农业银行银行卡交易明细清单",
                           ParagraphStyle("t", fontName=FH, fontSize=12.5, alignment=TA_CENTER, spaceAfter=4)))
    story.append(kv_line([
        ("账号客户", "955998 02** **** 6666 张*华", 92),
        ("序号", "0000", 30),
        ("币种", "人民币 钞", 58),
    ], 180))
    story.append(kv_line([
        ("起止日期", "20260401~20260430", 92),
        ("", "", 30),
        ("页次", "第1页", 58),
    ], 180))
    story.append(Spacer(1, 3))
    header = ["交易日期", "摘要", "交易金额", "余额", "交易地点/对方账号和户名"]
    t = base_table(abc1_rows,
                   [26 * mm, 28 * mm, 28 * mm, 30 * mm, 68 * mm],
                   ["CENTER", "LEFT", "RIGHT", "RIGHT", "LEFT"],
                   header=header, headbg=colors.HexColor("#F2F2F2"), font_size=8.2)
    story.append(t)
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print("OK", os.path.basename(file))


# ============================ 4) 农业银行 金穗借记卡明细对账单 ============================
def gen_abc2():
    from reportlab.lib.pagesizes import landscape
    PAGE = landscape(A4)
    file = os.path.join(OUT, "4_农业银行_金穗借记卡明细对账单_王强.pdf")

    def on_page(canv, doc):
        canv.saveState()
        test_note(canv)
        stamp(canv, 240, 112, 15)
        canv.restoreState()

    doc = SimpleDocTemplate(file, pagesize=PAGE, leftMargin=14 * mm, rightMargin=14 * mm,
                            topMargin=12 * mm, bottomMargin=14 * mm,
                            title="农业银行金穗借记卡明细对账单(测试样本)")
    story = []
    story.append(Paragraph("中国农业银行", ParagraphStyle("t1", fontName=FH, fontSize=12, alignment=TA_CENTER, spaceAfter=1)))
    story.append(Paragraph("金穗借记卡明细对账单", ParagraphStyle("t2", fontName=FH, fontSize=11.5, alignment=TA_CENTER, spaceAfter=4)))
    story.append(kv_line([
        ("打印机构", "中国农业银行××支行", 88),
        ("柜员", "191q", 40),
        ("打印日期", "2026年09月01日", 70),
        ("页码", "9", 69),
    ], 267))
    story.append(kv_line([
        ("姓名", "王*", 88),
        ("卡号", "955998 18** **** 1111", 110),
        ("账户序号", "0000", 34),
        ("币种", "人民币", 35),
    ], 267))
    story.append(Spacer(1, 3))
    header = ["交易日期", "交易时间", "摘要", "交易金额", "账户余额"]
    t = base_table(abc2_rows,
                   [30 * mm, 26 * mm, 45 * mm, 36 * mm, 34 * mm],
                   ["CENTER", "CENTER", "LEFT", "RIGHT", "RIGHT"],
                   header=header, headbg=colors.HexColor("#F2F2F2"), dashed=True, font_size=8.6)
    t.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 1.3, colors.HexColor("#333333"), None, (4, 2)),
        ("LINEBELOW", (0, -1), (-1, -1), 1.3, colors.HexColor("#333333"), None, (4, 2)),
    ]))
    t.hAlign = "LEFT"
    story.append(t)
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print("OK", os.path.basename(file))


gen_cmb()
gen_icbc()
gen_abc1()
gen_abc2()
print("DONE:", sorted(os.listdir(OUT)))
