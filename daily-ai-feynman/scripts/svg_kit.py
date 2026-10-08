# -*- coding: utf-8 -*-
"""SVG 插图工具库（清新蓝风格）。

用法：
    from svg_kit import *
    parts = [box(...), line_arrow(...), label(...)]
    open('images/svg_1.svg', 'w', encoding='utf-8').write(svg_doc(620, 440, ''.join(parts)))

所有坐标确定性给出，不依赖浏览器；配合 render_svg.cjs 用 resvg 渲染为 PNG。
"""
FONT = "'Microsoft YaHei','微软雅黑','PingFang SC',sans-serif"
FONTK = "'KaiTi','楷体','STKaiti'," + FONT

# 清新蓝主色板
BLUE   = "#1c5fd9"
PURPLE = "#845ef7"
GREEN  = "#40c057"
AMBER  = "#f2c200"
RED    = "#ff6b6b"
INK    = "#333333"
SUB    = "#666666"

LIGHT_BLUE   = "#e7f0ff"
LIGHT_PURPLE = "#e5dbff"
LIGHT_GREEN  = "#d3f9d8"
LIGHT_AMBER  = "#fff3bf"
LIGHT_RED    = "#ffe3e3"


def defs():
    return f"""<defs>
  <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
    <feDropShadow dx="0" dy="3" stdDeviation="4" flood-color="#000000" flood-opacity="0.12"/>
  </filter>
  <marker id="ah" markerWidth="7" markerHeight="7" refX="5" refY="2.5" orient="auto">
    <path d="M0,0 L5,2.5 L0,5 Z" fill="#5c5f66"/></marker>
  <marker id="ahb" markerWidth="7" markerHeight="7" refX="5" refY="2.5" orient="auto">
    <path d="M0,0 L5,2.5 L0,5 Z" fill="{BLUE}"/></marker>
  <marker id="aho" markerWidth="7" markerHeight="7" refX="5" refY="2.5" orient="auto">
    <path d="M0,0 L5,2.5 L0,5 Z" fill="{AMBER}"/></marker>
  <marker id="ahg" markerWidth="7" markerHeight="7" refX="5" refY="2.5" orient="auto">
    <path d="M0,0 L5,2.5 L0,5 Z" fill="{GREEN}"/></marker>
</defs>"""


def box(cx, cy, w, h, fill, stroke, lines, size=16, tcolor=INK, rx=16, weight="bold"):
    x, y = cx - w / 2, cy - h / 2
    s = (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" ry="{rx}" '
         f'fill="{fill}" stroke="{stroke}" stroke-width="2.5" filter="url(#shadow)"/>')
    n = len(lines)
    lh = size * 1.3
    tsp = ""
    for i, ln in enumerate(lines):
        dy = (-(n - 1) / 2 * lh) if i == 0 else lh
        tsp += f'<tspan x="{cx:.1f}" dy="{dy:.1f}">{ln}</tspan>'
    t = (f'<text x="{cx:.1f}" y="{cy:.1f}" font-family="{FONT}" font-size="{size}" fill="{tcolor}" '
         f'font-weight="{weight}" text-anchor="middle">{tsp}</text>')
    return s + t


def line_arrow(x1, y1, x2, y2, color="#5c5f66", mk="ah"):
    d = f"M{x1:.1f},{y1:.1f} L{x2:.1f},{y2:.1f}"
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.8" marker-end="url(#{mk})"/>'


def label(cx, cy, text, color=SUB, size=13):
    return (f'<text x="{cx:.1f}" y="{cy:.1f}" font-family="{FONTK}" font-size="{size}" '
            f'fill="{color}" font-weight="bold" text-anchor="middle">{text}</text>')


def header(cx, cy, text, color=BLUE, size=17):
    return (f'<text x="{cx:.1f}" y="{cy:.1f}" font-family="{FONT}" font-size="{size}" '
            f'fill="{color}" font-weight="bold" text-anchor="middle">{text}</text>')


def svg_doc(W, H, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'<rect width="{W}" height="{H}" fill="#ffffff"/>{defs()}{body}</svg>')
