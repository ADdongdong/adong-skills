"""
基金持仓分析报告生成工具
输入 Excel 持仓 → 默认输出 HTML，可按需同步生成 PDF
"""
import os
import html
from datetime import datetime
from collections import defaultdict

import openpyxl

# ─── 1. 路径配置 ────────────────────────────────────────────────────────────────
# 使用时替换为用户实际提供的 Excel 文件路径和期望的输出目录。
EXCEL_PATH = '<用户提供的持仓Excel文件路径>'
OUT_DIR = '<输出目录路径>'
TODAY = datetime.now().strftime('%Y%m%d')
TODAY_DISP = datetime.now().strftime('%Y-%m-%d')
HTML_PATH = os.path.join(OUT_DIR, f'基金持仓分析报告_{TODAY}.html')
PDF_PATH = os.path.join(OUT_DIR, f'基金持仓分析报告_{TODAY}.pdf')

os.makedirs(OUT_DIR, exist_ok=True)

# ─── 2. 读取 Excel ──────────────────────────────────────────────────────────────
wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
print('所有Sheet:', wb.sheetnames)
sheet_name = '当前记录' if '当前记录' in wb.sheetnames else wb.sheetnames[0]
ws = wb[sheet_name]
print(f'读取Sheet: {ws.title}，行数: {ws.max_row}，列数: {ws.max_column}')

rows = list(ws.iter_rows(min_row=2, values_only=True))
holdings = []
for r in rows:
    name = r[0]
    cost = r[1]
    value = r[2]
    pnl_r = r[3]
    note = r[4] if len(r) > 4 else None
    if not name:
        continue
    if str(cost) == '/':
        cost = None
    holdings.append({
        'name': name,
        'cost': float(cost) if cost and cost != '/' else None,
        'value': float(value) if value else 0.0,
        'pnl_r': float(pnl_r) if pnl_r else 0.0,
        'note': note or '',
    })

print(f'共读取 {len(holdings)} 条持仓记录')

# ─── 3. 衍生指标 ────────────────────────────────────────────────────────────────
total_value = sum(h['value'] for h in holdings)
total_cost = sum(h['cost'] for h in holdings if h['cost'] is not None)
total_pnl = total_value - total_cost
total_pnl_r = (total_pnl / total_cost * 100) if total_cost else 0.0

for h in holdings:
    h['weight'] = h['value'] / total_value * 100 if total_value else 0
    h['pnl_abs'] = h['value'] - h['cost'] if h['cost'] is not None else 0.0


def classify_asset(name):
    """根据基金名称关键字识别资产类别"""
    name_lower = name.lower() if name else ''
    if '余额宝' in name or '货币' in name:
        return '货币/现金'
    if '短债' in name or '纯债' in name or '利率债' in name:
        return '固收'
    if '固收' in name or '可转债' in name or '二级债' in name or '偏债' in name:
        return '固收+'
    if 'qdii' in name_lower or '海外' in name or '恒生' in name or '纳指' in name or '标普' in name:
        return '海外权益'
    if '黄金' in name or '上海金' in name or '另类' in name:
        return '另类/黄金'
    return 'A股权益'


def classify_suggestion(pnl_r):
    """根据收益率给出操作建议分类"""
    if pnl_r > 15:
        return '获利减仓', 'take-profit'
    if pnl_r < -5:
        return '关注风控/切换', 'stop'
    return '持仓观望', 'hold'


for h in holdings:
    h['category'] = classify_asset(h['name'])
    h['suggestion'], h['suggestion_cls'] = classify_suggestion(h['pnl_r'])

category_totals = defaultdict(float)
for h in holdings:
    category_totals[h['category']] += h['value']


# ─── 4. HTML 生成（默认正式交付） ───────────────────────────────────────────────
def _safe_html(s):
    return html.escape(str(s))


def _color_class(v):
    return 'up' if v >= 0 else 'down'


def build_html_report(holdings, output_path):
    """按 references/portfolio_report_template.html 结构生成自包含 HTML。"""
    table_rows = []
    for h in holdings:
        cost_s = f"¥{h['cost']:.2f}" if h['cost'] is not None else '/'
        table_rows.append(
            f"<tr>"
            f"<td>{_safe_html(h['name'])}</td>"
            f"<td>{_safe_html(h['category'])}</td>"
            f"<td>¥{h['value']:.2f}</td>"
            f"<td>{h['weight']:.1f}%</td>"
            f"<td>{cost_s}</td>"
            f"<td class='{_color_class(h['pnl_r'])}'>{h['pnl_r']:+.1f}%</td>"
            f"<td><span class='tag {h['suggestion_cls']}'>{_safe_html(h['suggestion'])}</span></td>"
            f"</tr>"
        )

    cat_rows = []
    for cat, val in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
        pct = val / total_value * 100 if total_value else 0
        cat_rows.append(f"<tr><td>{_safe_html(cat)}</td><td>¥{val:.2f}</td><td>{pct:.1f}%</td><td></td></tr>")

    suggest_lines = []
    for h in holdings:
        suggest_lines.append(
            f"<p style='font-size:0.9rem;margin-bottom:6px'>"
            f"<strong>{_safe_html(h['name'])}</strong> — "
            f"<span class='tag {h['suggestion_cls']}'>{_safe_html(h['suggestion'])}</span>"
            f"（收益率 {h['pnl_r']:+.1f}%）</p>"
        )

    # 内联样式与模板保持一致，便于浏览器直接打开 / 打印
    doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>基金持仓分析报告 — {TODAY_DISP}</title>
<style>
  :root {{
    --bg: #f5f6f8; --card: #fff; --text: #1a1a2e; --muted: #6b7280;
    --border: #e5e7eb; --accent: #1e3a5f; --red: #dc2626; --green: #16a34a;
    --amber: #d97706; --blue: #2563eb;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, "PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif;
    background: var(--bg); color: var(--text); line-height: 1.6; padding: 24px 16px;
  }}
  .container {{ max-width: 900px; margin: 0 auto; }}
  .header {{
    background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
    color: #fff; border-radius: 12px; padding: 28px 24px; margin-bottom: 20px;
  }}
  .header h1 {{ font-size: 1.5rem; font-weight: 700; margin-bottom: 6px; }}
  .header .meta {{ opacity: 0.85; font-size: 0.875rem; }}
  h2 {{
    font-size: 1.1rem; font-weight: 600; margin: 28px 0 12px;
    padding-bottom: 6px; border-bottom: 2px solid var(--accent); color: var(--accent);
  }}
  h3 {{ font-size: 0.95rem; font-weight: 600; margin: 14px 0 8px; }}
  .card {{
    background: var(--card); border: 1px solid var(--border);
    border-radius: 10px; padding: 16px 18px; margin-bottom: 12px;
  }}
  .summary {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 10px;
  }}
  .stat .label {{ font-size: 0.8rem; color: var(--muted); }}
  .stat .value {{ font-size: 1.15rem; font-weight: 700; margin-top: 2px; }}
  .up {{ color: var(--red); }} .down {{ color: var(--green); }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.875rem; }}
  th, td {{ padding: 8px 10px; text-align: left; border-bottom: 1px solid var(--border); }}
  th {{ color: var(--muted); font-weight: 500; background: #f9fafb; }}
  .tag {{
    display: inline-block; font-size: 0.75rem; font-weight: 600;
    padding: 2px 8px; border-radius: 4px;
  }}
  .tag.take-profit {{ background: #fef2f2; color: var(--red); }}
  .tag.hold {{ background: #eff6ff; color: var(--blue); }}
  .tag.stop {{ background: #fffbeb; color: var(--amber); }}
  .footer {{
    margin-top: 32px; padding-top: 12px; border-top: 1px solid var(--border);
    color: var(--muted); font-size: 0.75rem; text-align: center;
  }}
  @media print {{ body {{ background: #fff; padding: 0; }} .header {{ border-radius: 0; }} }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>基金持仓分析报告</h1>
    <div class="meta">生成日期：{TODAY_DISP}</div>
  </div>

  <h2>一、持仓概览</h2>
  <div class="card">
    <div class="summary">
      <div class="stat"><div class="label">总市值</div><div class="value">¥{total_value:,.2f}</div></div>
      <div class="stat"><div class="label">总成本</div><div class="value">¥{total_cost:,.2f}</div></div>
      <div class="stat"><div class="label">总盈亏</div><div class="value {_color_class(total_pnl)}">{total_pnl:+,.2f}</div></div>
      <div class="stat"><div class="label">综合收益率</div><div class="value {_color_class(total_pnl_r)}">{total_pnl_r:+.2f}%</div></div>
    </div>
  </div>
  <div class="card" style="padding:0;overflow-x:auto">
    <table>
      <thead>
        <tr>
          <th>基金名称</th><th>资产大类</th><th>市值</th><th>占比</th>
          <th>成本</th><th>收益率</th><th>建议</th>
        </tr>
      </thead>
      <tbody>
        {''.join(table_rows)}
      </tbody>
    </table>
  </div>

  <h2>二、配置诊断（资产类别分布）</h2>
  <div class="card" style="padding:0;overflow-x:auto">
    <table>
      <thead><tr><th>资产大类</th><th>市值</th><th>占比</th><th>诊断</th></tr></thead>
      <tbody>
        {''.join(cat_rows)}
      </tbody>
    </table>
  </div>
  <div class="card">
    <p style="font-size:0.9rem;color:var(--muted)">
      宏观环境、牛市见顶信号、综合调整建议等分析段落由 Agent 按 SKILL 流程补全后写入本报告对应章节。
    </p>
  </div>

  <h2>三、各基金建议</h2>
  <div class="card">
    {''.join(suggest_lines)}
  </div>

  <div class="footer">
    以上分析基于公开数据整理，仅供参考，不构成投资建议。基金过往业绩不代表未来表现，投资有风险，决策需谨慎。
  </div>
</div>
</body>
</html>
"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(doc)
    print(f'HTML 已生成: {output_path}')


# ─── 5. PDF 生成（可选） ────────────────────────────────────────────────────────
def build_pdf_report(holdings, output_path):
    """
    用 reportlab 生成 PDF。
    排版：A4、左边距约 50、标题 18pt、章节 14pt、正文 9–10pt、逐行列表。
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    font_candidates = [
        ('SimHei', 'SimHei.ttf'),
        ('SimHei', '/System/Library/Fonts/STHeiti Light.ttc'),
        ('PingFang', '/System/Library/Fonts/PingFang.ttc'),
        ('MicrosoftYaHei', 'msyh.ttc'),
    ]
    chinese_font = 'Helvetica'
    for name, path in font_candidates:
        try:
            pdfmetrics.registerFont(TTFont(name, path))
            chinese_font = name
            break
        except Exception:
            continue

    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    left = 50

    def check_page(y, need=50):
        if y < need:
            c.showPage()
            c.setFont(chinese_font, 9)
            return height - 50
        return y

    # 标题
    c.setFont(chinese_font, 18)
    c.drawString(left, height - 50, '基金持仓分析报告')
    c.setFont(chinese_font, 10)
    c.drawString(left, height - 70, f'生成日期: {TODAY}')

    # 一、持仓概览
    y = height - 100
    c.setFont(chinese_font, 14)
    c.drawString(left, y, '一、持仓概览')
    y -= 18
    c.setFont(chinese_font, 9)
    c.drawString(left + 10, y, f'总市值:{total_value:.2f} | 总成本:{total_cost:.2f} | 总盈亏:{total_pnl:+.2f} | 综合收益率:{total_pnl_r:+.2f}%')
    y -= 16
    for h in holdings:
        line = f"{h['name']} | 市值:{h['value']:.2f} | 占比:{h['weight']:.1f}% | 收益率:{h['pnl_r']:.1f}%"
        c.drawString(left + 10, y, line[:95])
        y -= 14
        y = check_page(y)

    # 二、配置诊断
    y -= 16
    y = check_page(y, 80)
    c.setFont(chinese_font, 14)
    c.drawString(left, y, '二、配置诊断')
    y -= 18
    c.setFont(chinese_font, 10)
    for cat, val in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
        pct = val / total_value * 100 if total_value else 0
        c.drawString(left + 10, y, f'{cat}: {val:.2f} ({pct:.1f}%)')
        y -= 14
        y = check_page(y)

    # 三、各基金建议
    y -= 16
    y = check_page(y, 80)
    c.setFont(chinese_font, 14)
    c.drawString(left, y, '三、各基金建议')
    y -= 18
    c.setFont(chinese_font, 9)
    for h in holdings:
        line = f"{h['name']}: {h['suggestion']} (收益率:{h['pnl_r']:.1f}%)"
        c.drawString(left + 10, y, line[:95])
        y -= 14
        y = check_page(y)

    # 附注
    y -= 18
    y = check_page(y, 40)
    c.setFont(chinese_font, 8)
    c.drawString(left, y, '免责声明：本报告仅供参考，不构成投资建议。市场有风险，投资需谨慎。')

    c.save()
    print(f'PDF 已生成: {output_path}')


# ─── 6. 执行 ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    build_html_report(holdings, HTML_PATH)
    # PDF 可选：需要时取消下一行注释，或传环境变量 FUND_REPORT_PDF=1
    if os.environ.get('FUND_REPORT_PDF', '').strip() in ('1', 'true', 'yes'):
        build_pdf_report(holdings, PDF_PATH)
