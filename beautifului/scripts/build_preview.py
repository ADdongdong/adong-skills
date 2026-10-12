#!/usr/bin/env python3
"""
build_preview.py — 生成 assets/preview/index.html（单文件、零构建、断网可开）。

设计取舍:
  需求是「单文件、离线可开」，所以 21 个移植件必须**内嵌**而不是外链
  （file:// 下 fetch 受同源限制，且用户可能只把这一个文件拷走）。
  但 21 个内联 iframe 同时跑动画会明显吃 CPU，所以：
    · 把每个移植件的 HTML 以 JSON 字符串塞进一段 JS（`</` 转义为 `<\\/`，避免提前闭合 script）
    · 卡片进入视口时才写入 iframe.srcdoc（IntersectionObserver 懒加载）
  这样既真正自包含，又不至于一开页面就 21 个动画齐飞。

用法:
  python build_preview.py [--skill-dir <dir>]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from datetime import date

# slug / 中文名 / 一句话用途 / 场景标签 / 保真备注 / 分层
# 中文用途与 references/component-catalog.md 保持一致（这里取精简版）
CATALOG = [
    ("loading-state", "Loading State", "加载状态", "像素网格加载器 + 微光标签 + 实时计时器",
     ["等待态", "不确定时长"], "", "状态与过程"),
    ("thinking-state", "Thinking", "思考轨迹", "可展开的推理轨迹：步骤 / 推理 / 搜索 / 编码",
     ["可解释", "推理过程"], "", "状态与过程"),
    ("tool-chips", "Tool Chips", "工具调用芯片", "工具调用与代码改动压缩成紧凑芯片，hover 预览 diff",
     ["工具使用", "代码改动"], "", "状态与过程"),
    ("task-rows", "Task Rows", "任务进度行", "实时任务状态：运行中 / 失败 / 已完成，可展开详情",
     ["多步任务", "进度"], "", "状态与过程"),
    ("streaming-text", "Streaming Text", "流式回答", "逐字流式输出 + 尾部模糊消解 + 内联来源 + 追问",
     ["流式", "核心"], "", "对话与输出"),
    ("chat-composer", "Chat", "聊天面板", "带标签页的聊天面板，含推理回复与底部输入区",
     ["对话容器"], "", "对话与输出"),
    ("prompt-bar", "Prompt Bar", "提示栏", "@ 引用来源、/ 命令、模型选择器、附件与发送",
     ["主输入区"], "glimm → 原生 textarea", "对话与输出"),
    ("code-block", "Code Block", "代码块", "带行号的代码列表与统一 diff（词级高亮）",
     ["代码答案"], "", "对话与输出"),
    ("selection-actions", "Selection Actions", "选区操作", "高亮一段文字交给 Agent 重写，原地流式返回",
     ["选中即改", "写作"], "iconoir-react → 内联 SVG", "对话与输出"),
    ("approval-card", "Approval Card", "审批卡片", "Agent 动手前先问用户，单选/多选 + 自定义答案",
     ["人机协同", "不可逆动作"], "", "人机协同"),
    ("recommendation-card", "Recommendation Card", "推荐卡片", "Agent 建议 + 置信度仪表 + 备选抽屉",
     ["建议", "拍板"], "", "人机协同"),
    ("context-cards", "Context Cards", "上下文卡片", "检索到的知识片段与来源 favicon",
     ["RAG", "引用"], "", "知识与数据"),
    ("records-table", "Records Table", "记录表格", "CRM 风格网格：标签、排序、关系状态、计算列提案",
     ["业务数据", "最复杂"], "", "知识与数据"),
    ("diff-table", "Diff Table", "差异表格", "AI 提议的表格增删，逐格 diff 扫过",
     ["数据改动"], "", "知识与数据"),
    ("filter-table", "Filter Table", "筛选表格", "状态芯片实时重组数据",
     ["看板", "筛选"], "", "知识与数据"),
    ("insight-cards", "Insight Cards", "洞察卡片", "分页洞察 + 可拖动 scrub 的实时图表",
     ["洞察", "图表"], "liveline → 自绘 SVG", "知识与数据"),
    ("sidebar-nav", "Sidebar Nav", "侧边导航", "可折叠工作区/聊天导航，滑动 hover 高亮",
     ["应用外壳"], "付费图标 → lucide", "导航与检索"),
    ("search", "Search", "命令搜索", "命令面板式搜索：实时过滤、空状态、键盘导航",
     ["⌘K", "跳转"], "", "导航与检索"),
    ("flowchart", "Flowchart", "流程图", "点阵画布上的触发器与条件步骤（If/Else、and/or）",
     ["编排可视化"], "", "开发与流程"),
    ("fine-tune-card", "Fine-tune Card", "微调卡片", "Agent 在检查器里调 W/H/圆角/透明度，可拖动",
     ["参数面板"], "", "开发与流程"),
    ("agent-screen", "Agent Screen", "智能体屏幕", "观看 Agent 的屏幕：open / teach / record",
     ["操作可视化"], "占位图为自绘", "开发与流程"),
]

# 无上游共享依赖
NO_DEP = "—"

TOKEN_GROUPS = [
    ("表面 / 墨色", ["--page", "--canvas", "--surface", "--inset", "--hover", "--hover-2",
                    "--ink", "--ink-2", "--ink-3"]),
    ("描边", ["--line", "--line-strong", "--line-soft", "--field", "--grid-line"]),
    ("强调与语义", ["--accent", "--accent-ink", "--accent-tint", "--green", "--green-tint",
                  "--orange", "--orange-tint", "--red", "--red-tint"]),
    ("圆角", ["--radius-chip", "--radius-control", "--radius-card", "--radius-window"]),
    ("缓动", ["--ease-out-strong", "--ease-in-out-strong", "--ease-link"]),
    ("阴影", ["--shadow-hairline", "--shadow-btn", "--shadow-card", "--shadow-raised",
             "--shadow-overlay"]),
]

KEYFRAMES = [
    ("pixel-on", "像素网格加载器", "逐格错开 delay 形成波浪"),
    ("shimmer-text", "微光文字", "background-position 150% → -50%"),
    ("fade-up", "上浮入场", "opacity 0→1 + translateY(8px)→0"),
    ("fade-in", "淡入", "仅 opacity"),
    ("pop-in", "弹出", "opacity + scale(.95)→1"),
    ("spin", "旋转", "rotate(360deg)"),
    ("eq-bounce", "均衡器跳动", "scaleY(.35)→1→.35"),
    ("caret-blink", "光标闪烁", "step-end，1s"),
]


def slug_cn(slug: str) -> str:
    for row in CATALOG:
        if row[0] == slug:
            return row[2]
    return slug


def build(skill: str) -> str:
    html_dir = os.path.join(skill, "assets", "html")
    ports: dict[str, str] = {}
    for p in sorted(glob.glob(os.path.join(html_dir, "*.html"))):
        slug = os.path.basename(p)[:-5]
        with open(p, encoding="utf-8") as fh:
            ports[slug] = fh.read()

    # 内嵌 JSON：</ 转义，避免在 <script> 里提前闭合
    payload = json.dumps(ports, ensure_ascii=False).replace("</", "<\\/")

    found = set(ports)
    missing = [r[0] for r in CATALOG if r[0] not in found]

    cards = []
    for slug, en, cn, purpose, tags, degrade, group in CATALOG:
        has = slug in found
        badge = ("<span class=\"badge ok\">✓ 已移植</span>" if has
                 else "<span class=\"badge miss\">未生成</span>")
        deg = f'<span class="badge warn">{degrade}</span>' if degrade else ""
        taghtml = "".join(f'<span class="tag">{t}</span>' for t in tags)
        size = f"{len(ports.get(slug, '')) / 1024:.0f} KB" if has else "—"
        cards.append(f"""
  <article class="card" data-slug="{slug}" data-group="{group}"
           data-search="{slug} {en} {cn} {' '.join(tags)} {purpose}">
    <header class="card-hd">
      <div>
        <h3>{cn} <span class="en">{en}</span></h3>
        <p class="purpose">{purpose}</p>
      </div>
      <div class="badges">{badge}{deg}</div>
    </header>
    <div class="tags">{taghtml}</div>
    <div class="demo" data-slug="{slug}">
      <div class="demo-ph">进入视口后加载真动效 demo…</div>
    </div>
    <footer class="card-ft">
      <code class="path">assets/html/{slug}.html</code>
      <span class="size">{size}</span>
      <button type="button" class="copy" data-copy="assets/html/{slug}.html">复制路径</button>
    </footer>
  </article>""")

    groups = []
    for g in dict.fromkeys(r[6] for r in CATALOG):
        groups.append(f'<option value="{g}">{g}</option>')

    token_html = []
    for gname, toks in TOKEN_GROUPS:
        sw = "".join(
            f'<div class="sw"><span class="chip" style="background:var({t})"></span>'
            f'<code>{t}</code></div>'
            for t in toks
        )
        token_html.append(f'<div class="tgroup"><h4>{gname}</h4><div class="sws">{sw}</div></div>')

    kf_html = "".join(
        f'<div class="kf"><div class="kf-demo" style="animation:{k} 1.4s infinite"></div>'
        f'<div><code>{k}</code><p>{desc}<br><span class="dim">{note}</span></p></div></div>'
        for k, desc, note in KEYFRAMES
    )

    route_rows = "".join(
        f"<tr><td>{a}</td><td><code>{b}</code></td><td><code>{c}</code></td></tr>"
        for a, b, c in [
            ("对话/问答容器", "chat-composer, streaming-text", "prompt-bar"),
            ("流式答案", "streaming-text", "code-block"),
            ("思考/推理轨迹", "thinking-state", "tool-chips"),
            ("工具调用/代码改动", "tool-chips", "diff-table, code-block"),
            ("人类审批（不可逆）", "approval-card", "selection-actions"),
            ("多步任务进度", "task-rows", "loading-state"),
            ("RAG 引用", "context-cards", "streaming-text（来源）"),
            ("表格数据改动", "diff-table", "records-table"),
            ("业务数据主视图", "records-table", "filter-table"),
            ("Agent 建议", "recommendation-card", "insight-cards"),
            ("命令面板", "search", "sidebar-nav"),
            ("应用外壳", "sidebar-nav", "search"),
            ("流程编排", "flowchart", "task-rows"),
            ("选中即改", "selection-actions", "approval-card"),
            ("Agent 操作可视化", "agent-screen", "task-rows"),
        ]
    )

    dep_rows = "".join(
        f"<tr><td><code>{r[0]}</code></td><td>{r[2]}</td>"
        f"<td>{r[4] if r[4] else NO_DEP}</td><td>{r[5] or '—'}</td></tr>"
        for r in CATALOG
    )

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Beautiful UI · 21 个 AI 原生组件（离线预览）</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {{
  --page: #f7f8fa; --canvas: #eef0f4; --surface: #ffffff; --inset: #f4f5f7;
  --hover: #f0f1f4; --ink: #1b2130; --ink-2: #5b6478; --ink-3: #8b93a5;
  --line: #e3e6ec; --line-strong: #d2d7e0; --field: #f2f3f6;
  --accent: #0285FF; --accent-ink: #0166c8; --accent-tint: #e8f2ff;
  --green: #1f9d5c; --orange: #d97706; --red: #d93f3f;
  --radius-chip: 6px; --radius-control: 8px; --radius-card: 10px; --radius-window: 14px;
  --ease-out-strong: cubic-bezier(0.23, 1, 0.32, 1);
  --shadow-card: 0 0 0 1px var(--line), 0 1px 2px rgba(16,24,40,.04);
  --shadow-raised: 0 0 0 1px var(--line), 0 2px 10px rgba(16,24,40,.06);
  --font-sans: 'Inter', ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif;
  --font-mono: 'JetBrains Mono', ui-monospace, 'SF Mono', Menlo, Consolas, monospace;
}}
html.dark {{
  --page: #14171d; --canvas: #191d24; --surface: #21252d; --inset: #1d2128;
  --hover: #262b34; --ink: #eef1f6; --ink-2: #a8b0bf; --ink-3: #7c8494;
  --line: #2c313a; --line-strong: #3a404a; --field: #262b33;
  --accent: #4da3ff; --accent-ink: #8cc2ff; --accent-tint: rgba(77,163,255,.16);
  --green: #4ec38a; --orange: #f0a94a; --red: #f27272;
  --shadow-card: 0 0 0 1px var(--line), 0 1px 2px rgba(0,0,0,.3);
  --shadow-raised: 0 0 0 1px var(--line), 0 2px 10px rgba(0,0,0,.35);
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0; background: var(--page); color: var(--ink);
  font-family: var(--font-sans); font-size: 14px; line-height: 1.5;
  letter-spacing: -0.01em;
}}
code {{ font-family: var(--font-mono); font-size: .92em; }}
.wrap {{ max-width: 1100px; margin: 0 auto; padding: 36px 24px 80px; }}
h1 {{ margin: 0 0 6px; font-size: 26px; letter-spacing: -0.02em; }}
h2 {{ margin: 44px 0 14px; font-size: 17px; letter-spacing: -0.01em; }}
h3 {{ margin: 0; font-size: 15px; }}
h4 {{ margin: 0 0 8px; font-size: 12px; color: var(--ink-2); text-transform: uppercase;
      letter-spacing: .06em; font-weight: 600; }}
.lede {{ margin: 0 0 4px; color: var(--ink-2); max-width: 62ch; }}
.meta {{ margin: 14px 0 0; padding: 10px 14px; border: 1px solid var(--line);
         border-radius: var(--radius-card); background: var(--surface); color: var(--ink-2);
         font-size: 12.5px; max-width: 70ch; }}
.meta b {{ color: var(--ink); font-weight: 600; }}
.toolbar {{ display: flex; gap: 10px; flex-wrap: wrap; align-items: center; margin: 22px 0 18px;
            position: sticky; top: 0; z-index: 20; padding: 12px 0;
            background: color-mix(in srgb, var(--page) 88%, transparent);
            backdrop-filter: blur(8px); }}
input[type=search], select {{
  height: 32px; padding: 0 10px; border: 1px solid var(--line-strong);
  border-radius: var(--radius-control); background: var(--surface); color: var(--ink);
  font-family: inherit; font-size: 13px;
}}
input[type=search] {{ min-width: 260px; }}
button.tb {{
  height: 32px; padding: 0 12px; border: 1px solid var(--line-strong);
  border-radius: var(--radius-control); background: var(--surface); color: var(--ink);
  font: inherit; font-size: 13px; cursor: pointer;
  transition: background-color 150ms var(--ease-out-strong);
}}
button.tb:hover {{ background: var(--hover); }}
.count {{ color: var(--ink-3); font-size: 12.5px; margin-left: auto; }}
.grid {{ display: grid; gap: 18px; grid-template-columns: repeat(auto-fill, minmax(330px, 1fr)); }}
.card {{
  display: flex; flex-direction: column; border: 1px solid var(--line);
  border-radius: var(--radius-window); background: var(--surface);
  box-shadow: var(--shadow-card); overflow: hidden;
}}
.card.hide {{ display: none; }}
.card-hd {{ display: flex; justify-content: space-between; gap: 10px; padding: 14px 14px 8px; }}
.en {{ color: var(--ink-3); font-size: 12px; font-weight: 400; margin-left: 4px; }}
.purpose {{ margin: 5px 0 0; color: var(--ink-2); font-size: 12.5px; }}
.badges {{ display: flex; flex-direction: column; gap: 4px; align-items: flex-end; flex: 0 0 auto; }}
.badge {{ padding: 2px 7px; border-radius: 9999px; font-size: 10.5px; white-space: nowrap;
          font-weight: 500; }}
.badge.ok {{ color: var(--green); background: color-mix(in srgb, var(--green) 12%, var(--surface)); }}
.badge.warn {{ color: var(--orange); background: color-mix(in srgb, var(--orange) 14%, var(--surface)); }}
.badge.miss {{ color: var(--red); background: color-mix(in srgb, var(--red) 12%, var(--surface)); }}
.tags {{ display: flex; gap: 5px; flex-wrap: wrap; padding: 0 14px 10px; }}
.tag {{ padding: 2px 7px; border: 1px solid var(--line); border-radius: var(--radius-chip);
        color: var(--ink-2); font-size: 10.5px; background: var(--field); }}
.demo {{ height: 240px; border-top: 1px solid var(--line); border-bottom: 1px solid var(--line);
         background: var(--inset); position: relative; }}
.demo iframe {{ width: 100%; height: 100%; border: 0; display: block; background: var(--surface); }}
.demo-ph {{ display: grid; place-items: center; height: 100%; color: var(--ink-3); font-size: 12px; }}
.card-ft {{ display: flex; align-items: center; gap: 8px; padding: 10px 14px; }}
.path {{ flex: 1; color: var(--ink-2); font-size: 11.5px; overflow: hidden;
         text-overflow: ellipsis; white-space: nowrap; }}
.size {{ color: var(--ink-3); font-size: 11px; }}
.copy {{ padding: 3px 9px; border: 1px solid var(--line-strong); border-radius: var(--radius-chip);
         background: var(--surface); color: var(--ink-2); font: inherit; font-size: 11px;
         cursor: pointer; }}
.copy:hover {{ background: var(--hover); }}
table {{ width: 100%; border-collapse: collapse; font-size: 12.5px;
         border: 1px solid var(--line); border-radius: var(--radius-card);
         background: var(--surface); overflow: hidden; }}
th, td {{ padding: 9px 11px; text-align: left; border-bottom: 1px solid var(--line);
          vertical-align: top; }}
th {{ color: var(--ink-2); font-size: 11px; text-transform: uppercase;
      letter-spacing: .05em; background: var(--inset); }}
tr:last-child td {{ border-bottom: 0; }}
.tgroup {{ margin-bottom: 16px; }}
.sws {{ display: flex; gap: 12px; flex-wrap: wrap; }}
.sw {{ display: flex; align-items: center; gap: 6px; }}
.chip {{ width: 18px; height: 18px; border-radius: 4px; box-shadow: 0 0 0 1px var(--line);
         flex: 0 0 18px; }}
.sw code {{ color: var(--ink-2); font-size: 11px; }}
.kfs {{ display: grid; gap: 12px; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); }}
.kf {{ display: flex; align-items: center; gap: 12px; padding: 12px; border: 1px solid var(--line);
       border-radius: var(--radius-card); background: var(--surface); }}
.kf-demo {{ width: 34px; height: 34px; flex: 0 0 34px; border-radius: var(--radius-control);
            background: var(--accent); }}
.kf p {{ margin: 3px 0 0; color: var(--ink-2); font-size: 11.5px; }}
.dim {{ color: var(--ink-3); }}
footer.pg {{ margin-top: 56px; padding-top: 18px; border-top: 1px solid var(--line);
             color: var(--ink-3); font-size: 12px; }}
footer.pg a {{ color: var(--accent-ink); }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Beautiful UI · 21 个 AI 原生组件</h1>
  <p class="lede">下面每个卡片里的 demo 都是**真的在跑**的组件（内嵌自包含 HTML），
     不是截图。动效、缓动曲线、颜色与上游 beautifului.dev 一致。</p>
  <div class="meta">
    <b>离线预览页</b>：单文件、零构建、断网可开。
    21 个 demo 会在卡片进入视口时才加载（<code>IntersectionObserver</code> 懒加载），避免一开页面 21 个动画齐飞。
    右上角可切明暗主题。<br>
    上游：<b>Beautiful UI</b> by Shane Levine (Turbo) — <b>MIT</b> ·
    <a href="https://www.beautifului.dev">beautifului.dev</a> ·
    <a href="https://github.com/slev12397/beautiful-ui">GitHub</a> · 生成于 {date.today().isoformat()}
  </div>

  <div class="toolbar">
    <input type="search" id="q" placeholder="搜索组件 / 场景（如 流式、审批、表格）…">
    <select id="g"><option value="">全部分组</option>{''.join(groups)}</select>
    <button type="button" class="tb" id="theme">切换明暗</button>
    <span class="count" id="count"></span>
  </div>

  <div class="grid" id="grid">{''.join(cards)}
  </div>

  <h2>场景 → 组件路由表</h2>
  <table>
    <thead><tr><th>AI 产品表面</th><th>主推</th><th>备选</th></tr></thead>
    <tbody>{route_rows}</tbody>
  </table>

  <h2>组件清单：依赖与降级</h2>
  <table>
    <thead><tr><th>slug</th><th>中文名</th><th>上游共享依赖</th><th>本 skill 的降级</th></tr></thead>
    <tbody>{dep_rows}</tbody>
  </table>

  <h2>设计令牌</h2>
  <p class="lede">组件只通过令牌取色，所以换肤 = 只改 <code>:root</code> 与 <code>.dark</code> 两个块。
     下面的色块直接读当前主题的令牌值，切换明暗即可看到整套令牌翻转。</p>
  {''.join(token_html)}

  <h2>关键帧</h2>
  <p class="lede">上游一共 8 个关键帧（另有 <code>records-pulse</code> 仅归记录表格）。
     这套 UI 的"手感"主要靠它们 + 三条强缓动曲线。</p>
  <div class="kfs">{kf_html}</div>

  <footer class="pg">
    <b>Beautiful UI</b> — Crafted primitives for AI-native interfaces ·
    © 2026 Shane Levine (Turbo) · MIT License ·
    本页由 <code>scripts/build_preview.py</code> 生成 · 组件源码与移植件见 skill 目录。
  </footer>
</div>

<script>
var PORTS = {payload};
var LOADED = {{}};

/* 懒加载：卡片进入视口才注入 srcdoc，避免 21 个动画同时跑 */
function loadDemo(slug) {{
  if (LOADED[slug]) return;
  var host = document.querySelector('.demo[data-slug="' + slug + '"]');
  var html = PORTS[slug];
  if (!host || !html) return;
  LOADED[slug] = true;
  var f = document.createElement('iframe');
  f.setAttribute('title', slug + ' demo');
  f.setAttribute('loading', 'lazy');
  f.srcdoc = html;
  host.innerHTML = '';
  host.appendChild(f);
}}

var io = new IntersectionObserver(function (entries) {{
  entries.forEach(function (e) {{
    if (e.isIntersecting) {{
      loadDemo(e.target.getAttribute('data-slug'));
      io.unobserve(e.target);
    }}
  }});
}}, {{ rootMargin: '240px' }});
document.querySelectorAll('.demo').forEach(function (el) {{ io.observe(el); }});

/* 搜索 + 分组过滤 */
var q = document.getElementById('q');
var g = document.getElementById('g');
var count = document.getElementById('count');
function apply() {{
  var s = (q.value || '').toLowerCase().trim();
  var grp = g.value;
  var shown = 0;
  document.querySelectorAll('.card').forEach(function (c) {{
    var hitS = !s || (c.getAttribute('data-search') || '').toLowerCase().indexOf(s) >= 0;
    var hitG = !grp || c.getAttribute('data-group') === grp;
    var ok = hitS && hitG;
    c.classList.toggle('hide', !ok);
    if (ok) shown++;
  }});
  count.textContent = '显示 ' + shown + ' / ' + document.querySelectorAll('.card').length;
}}
q.addEventListener('input', apply);
g.addEventListener('change', apply);
apply();

/* 明暗切换（预览页自身 + 已加载的 iframe） */
var dark = false;
document.getElementById('theme').addEventListener('click', function () {{
  dark = !document.documentElement.classList.toggle('dark');
  document.querySelectorAll('.demo iframe').forEach(function (f) {{
    try {{
      var d = f.contentDocument;
      if (d) d.documentElement.classList.toggle('dark', dark);
    }} catch (e) {{ /* file:// 下可能受限，忽略 */ }}
  }});
}});

/* 复制路径 */
document.querySelectorAll('.copy').forEach(function (b) {{
  b.addEventListener('click', function () {{
    var t = b.getAttribute('data-copy');
    var done = function () {{ b.textContent = '已复制'; setTimeout(function () {{ b.textContent = '复制路径'; }}, 1200); }};
    if (navigator.clipboard && navigator.clipboard.writeText) {{
      navigator.clipboard.writeText(t).then(done, done);
    }} else {{
      var ta = document.createElement('textarea');
      ta.value = t; document.body.appendChild(ta); ta.select();
      try {{ document.execCommand('copy'); }} catch (e) {{}}
      document.body.removeChild(ta); done();
    }}
  }});
}});
</script>
</body>
</html>
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill-dir", default=os.path.join(os.path.expanduser("~"), ".workbuddy", "skills", "beautifului"))
    args = ap.parse_args()
    skill = os.path.abspath(args.skill_dir)
    out_dir = os.path.join(skill, "assets", "preview")
    os.makedirs(out_dir, exist_ok=True)

    html = build(skill)
    out = os.path.join(out_dir, "index.html")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(html)

    n = len(re.findall(r'class="card"', html))
    have = len(glob.glob(os.path.join(skill, "assets", "html", "*.html")))
    print(f"[preview] 写入 {out}")
    print(f"[preview] {len(html.encode('utf-8')) / 1024:.0f} KB · 卡片 {n} 个 · 实际内嵌移植件 {have} 个")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
