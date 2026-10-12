#!/usr/bin/env python3
"""
build_ports.py — 把 assets/ports/<slug>.frag.html 组装成自包含的 assets/html/<slug>.html。

为什么要「片段 + 组装」而不是直接写 .html：
  1. 每个移植件的样式只需它自己用到的那批工具类。组装时按片段里出现的 class
     自动裁剪 CSS，单个文件因此只有几 KB 而不是把 36KB 的 foundation 全带上。
  2. class → CSS 由编译器生成（twsubset），不是手抄，改上游后重跑即可。
  3. 每个成品都是**零依赖单文件**：直接丢进 Flask 模板或任意静态页即可用。

片段文件格式（就是 <body> 内部内容）：
    <!-- 说明 -->
    <div class="flex items-center gap-2.5"> ... </div>
    <script> ... </script>

用法:
  python build_ports.py [--skill-dir <dir>] [--only <slug>]
"""
from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_foundation import build_foundation, build_utility_css  # noqa: E402
from twsubset import VALID, build_rule  # noqa: E402

# 主题切换按钮（每个移植件都有，便于直接检验 light/dark 两套令牌）
SHELL_CSS = """/* ── port shell：演示舞台 ─────────────────────────────────── */
html {
  background: var(--canvas);
  color: var(--ink);
  font-family: var(--font-sans);
}
body {
  min-height: 100vh;
  margin: 0;
  background: var(--canvas);
  color: var(--ink);
  font-family: var(--font-sans);
}
.port-stage {
  display: grid;
  min-height: 100vh;
  place-items: center;
  padding: 40px 24px;
}
.port-frame {
  display: flex;
  max-width: 100%;
  flex-direction: column;
  align-items: flex-start;
}
.port-theme-toggle {
  position: fixed;
  z-index: 50;
  top: 12px;
  right: 12px;
  display: inline-flex;
  height: 28px;
  align-items: center;
  gap: 6px;
  padding: 0 10px;
  border: 1px solid var(--line-strong);
  border-radius: var(--radius-control);
  color: var(--ink-2);
  background: var(--surface);
  box-shadow: var(--shadow-btn);
  font-family: var(--font-mono);
  font-size: 11px;
  cursor: pointer;
  transition: color 150ms var(--ease-out-strong), background-color 150ms var(--ease-out-strong);
}
.port-theme-toggle:hover {
  color: var(--ink);
  background: var(--hover);
}

/* ── port-only chrome：变体切换条 ─────────────────────────────
 * 上游画廊里「Drive / Dots / Orbit / Surfer」的切换属于站点外壳，不属于组件。
 * 移植件把它带上，方便一眼看全各变体；样式沿用令牌，不是上游代码。
 * ─────────────────────────────────────────────────────────── */
.port-variants {
  display: inline-flex;
  gap: 2px;
  margin-bottom: 20px;
  padding: 2px;
  border: 1px solid var(--line);
  border-radius: 9999px;
  background: var(--inset);
}
.port-variant-btn {
  padding: 4px 12px;
  border: 0;
  border-radius: 9999px;
  color: var(--ink-2);
  background: transparent;
  font-family: var(--font-sans);
  font-size: 12px;
  font-weight: 500;
  line-height: 1.4;
  cursor: pointer;
  transition: color 150ms var(--ease-out-strong), background-color 150ms var(--ease-out-strong);
}
.port-variant-btn:hover {
  color: var(--ink);
}
.port-variant-btn[aria-pressed="true"] {
  color: var(--ink);
  background: var(--surface);
  box-shadow: var(--shadow-btn);
}
/* 组件说明块（移植件顶部的一段中文用途说明） */
.port-note {
  max-width: 46ch;
  margin-bottom: 20px;
  color: var(--ink-2);
  font-size: 12.5px;
  line-height: 1.6;
}
.port-note code {
  padding: 1px 5px;
  border: 1px solid var(--line);
  border-radius: var(--radius-chip);
  background: var(--field);
  font-family: var(--font-mono);
  font-size: 11.5px;
}
"""

# 舞台外的自定义类，组装时直接并入（不属于 Tailwind 工具类）
SHELL_CLASSES = {
    "port-stage", "port-frame", "port-theme-toggle", "port-variants",
    "port-variant-btn", "port-note",
}

TOGGLE_HTML = """<button type="button" class="port-theme-toggle" id="port-theme-toggle" aria-label="切换明暗主题">
  <span id="port-theme-label">dark</span>
</button>
"""

TOGGLE_JS = """<script>
(function () {
  var root = document.documentElement;
  var label = document.getElementById('port-theme-label');
  var btn = document.getElementById('port-theme-toggle');
  if (!btn) return;
  btn.addEventListener('click', function () {
    var dark = root.classList.toggle('dark');
    if (label) label.textContent = dark ? 'light' : 'dark';
  });
})();
</script>
"""

PAGE = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — Beautiful UI port</title>
<!-- 上游设定使用 Inter + JetBrains Mono。离线时会回退到系统字体栈（度量略有差异）。 -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
{foundation}
{shell}
{utilities}
</style>
</head>
<body>
<div class="port-stage">
{body}
</div>
{toggle}
</body>
</html>
"""


# 扫描 `class="..."`，但允许提前在 JS 字符串拼接处收尾：
#   '... class="size-[4px] bg-ink ' + (cond ? 'a' : 'b') + '" ...'
#                                  ↑ 在这里收尾，拿到 size-[4px] bg-ink
# 这样既不会吞掉后面的 JS 代码，也能自动收下拼接前的静态类。
CLASS_ATTR = re.compile(r"""class\s*=\s*"([^"]*?)(?:"|'\s*\+)""")


CLASS_TOKEN = re.compile(r"[A-Za-z0-9_:./\[\]%()+,'!=-]+")


def classes_in(fragment: str) -> set[str]:
    """提取片段需要的 class。

    三个来源：
      ① `class="..."`：静态 markup 与 JS 里写死的属性值
         （扫描器允许在字符串拼接处收尾，避免吞掉后面的 JS 代码）
      ② `<script>` 里的字符串字面量，但**只收编译器认得的 token**
      ③ `<!--@classes: a b c -->` 显式声明

    ② 是关键：JS 里常把类名放在变量/常量里，例如

        var cls = round ? 'rounded-full' : 'rounded-[1px]';   // 不走 class=" 字面量
        body += '<tr class="records-row ' + cls + '">';        // 变量插在 class 值中间

    这类类名既不在 ① 也不在 ③，会被静默漏掉 —— CSS 缺失、元素"没样式"，
    而截图和 JS 报错都看不出来（历史版本就栽在这里：agent-screen 丢了 12 个类）。
    这里改成「扫所有字符串字面量，但用 build_rule() 做准入判断」：
    真正是工具类的收下，`'1.4s'`、`'(p.round'`、`'...'` 这类噪声编译不过、自动被拒。
    最坏情况只是多输出一条用不到的 CSS 规则，无副作用。
    """
    found: set[str] = set()

    for m in CLASS_ATTR.finditer(fragment):
        found.update(m.group(1).split())
    for m in re.finditer(r"<!--\s*@classes:\s*(.*?)\s*-->", fragment, re.S):
        found.update(m.group(1).split())

    for sm in re.finditer(r"<script[^>]*>([\s\S]*?)</script>", fragment):
        for lit in re.findall(r"""['"`]([^'"`\n]*)['"`]""", sm.group(1)):
            for tok in lit.split():
                if tok in found or not re.search(r"[A-Za-z]", tok):
                    continue
                if CLASS_TOKEN.fullmatch(tok) and build_rule(tok):
                    found.add(tok)

    return {c for c in found if c and re.search(r"[A-Za-z]", c)}


def extras_for(slug: str, frag: str) -> set[str]:
    """哪些「重量级」附加样式表这个组件真的需要。

    records-table.css 有 825 行（16KB），sidebar-nav.css 有 2KB。
    把 16KB 无关 CSS 塞进 19 个文件里既浪费也难读，所以按需带。
    """
    out: set[str] = set()
    if slug == "records-table" or re.search(r'class="[^"]*\brecords-', frag):
        out.add("records-table.css")
    if slug == "sidebar-nav" or re.search(r'class="[^"]*\bsidebar-', frag):
        out.add("sidebar-nav.css")
    return out


def build_one(slug: str, title: str, frag: str, up: str) -> tuple[str, list[str]]:
    # 顺序很重要：先 build_foundation —— 它会 register_defined_classes()，
    # 把 .records-* / .sidebar-* / .is-* 这些"已由自定义 CSS 定义"的类登记下来。
    # 若先算工具类，那些类会被误报成「未覆盖」。
    foundation = build_foundation(up, extras_for(slug, frag))
    used = classes_in(frag)
    util_css, unhandled = build_utility_css(used)
    html = PAGE.format(
        title=title,
        foundation=foundation,
        shell=SHELL_CSS,
        utilities=util_css,
        body=frag.strip(),
        toggle=TOGGLE_HTML + TOGGLE_JS,
    )
    # 未覆盖的类里剔除舞台自定义类与纯语义钩子
    real_unknown = [c for c in unhandled if c not in SHELL_CLASSES]
    return html, real_unknown


def write_ports_doc(root: str, rows: list[dict]) -> str:
    """由片段头注释生成 references/html-ports.md —— 文档跟着代码走，不会漂。"""
    out = os.path.join(root, "references", "html-ports.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    lines = [
        "# 21 个 HTML 移植件说明",
        "",
        "> **本文件由 `scripts/build_ports.py` 自动生成**，内容取自每个片段的头注释与实测结果。",
        "> 改完片段重跑脚本即可刷新，不要手改本文件。",
        "",
        "每个移植件都是**零依赖单文件**：内联了设计令牌、该组件所需的工具类 CSS、以及它的 JS 状态机。",
        "动效与上游一致的做法见 `foundation-tokens.md`（时序常量照搬 + 令牌同名引用 + DOM 层级不变）。",
        "",
        "## 总览",
        "",
        "| slug | 中文名 | 文件大小 | 工具类数 | 未覆盖类 | 片段 |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| `{r['slug']}` | {r['cn']} | {r['kb']:.0f} KB | {r['utils']} | "
            f"{len(r['unknown']) or '0'} | `assets/ports/{r['slug']}.frag.html` |"
        )
    lines += ["", "## 逐个说明", "", "以下「保真说明」摘自各片段头注释。", ""]
    for r in rows:
        lines += [
            f"### `{r['slug']}` — {r['cn']}",
            "",
            f"- 成品：`assets/html/{r['slug']}.html`（{r['kb']:.1f} KB）",
            f"- 源片段：`assets/ports/{r['slug']}.frag.html`",
            f"- 编译进 CSS 的工具类：{r['utils']} 个",
        ]
        if r["unknown"]:
            lines.append(f"- ⚠️ 未覆盖类：`{'`, `'.join(r['unknown'])}`")
        else:
            lines.append("- 未覆盖类：无")
        if r["notes"]:
            lines += ["", r["notes"].strip(), ""]
        lines.append("")
    lines += [
        "---",
        "",
        "## 重新生成",
        "",
        "```bash",
        "cd <skill 目录>",
        "python scripts/build_ports.py            # 重新组装全部移植件并刷新本文件",
        "NODE_PATH=$(npm root -g) node scripts/verify_ports.cjs   # 渲染验证 + 截图到 _verify/",
        "```",
        "",
        "> 脚本会自动找运行时：优先 `$NODE_BIN` / `$NODE_PATH`，其次 PATH 上的 `node`，",
        "> 最后回落到 `~/.workbuddy/binaries/` 下的托管运行时。",
        "> 若渲染验证需要浏览器而当前环境受限，可先跳过它。",
        "",
        "改上游之后的完整重生成流程见 `README.md`。",
        "",
    ]
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill-dir", default=os.path.join(os.path.expanduser("~"), ".workbuddy", "skills", "beautifului"))
    ap.add_argument("--only", default=None)
    args = ap.parse_args()
    root = os.path.abspath(args.skill_dir)
    src = os.path.join(root, "assets", "ports")
    dst = os.path.join(root, "assets", "html")
    os.makedirs(dst, exist_ok=True)

    # 片段文件名即 slug；标题取自首行注释 `<!-- title: XXX -->`
    frags = sorted(f for f in os.listdir(src) if f.endswith(".frag.html")) if os.path.isdir(src) else []
    if not frags:
        print(f"[ports] 没有找到片段：{src}")
        return 1

    # 组装不需要完整 foundation（令牌+base+组件 CSS 已在页面里），
    # 但工具类要按组件裁剪，所以走同一个 build_foundation
    up = os.path.join(root, "assets", "upstream")

    total = 0
    problems: dict[str, list[str]] = {}
    rows: list[dict] = []
    for fn in frags:
        slug = fn[: -len(".frag.html")]
        if args.only and args.only != slug:
            continue
        with open(os.path.join(src, fn), encoding="utf-8") as fh:
            frag = fh.read()
        m = re.search(r"<!--\s*title:\s*(.+?)\s*-->", frag)
        title = m.group(1) if m else slug
        html, unknown = build_one(slug, title, frag, up)
        with open(os.path.join(dst, f"{slug}.html"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(html)
        kb = len(html.encode("utf-8")) / 1024
        n_utils = len({x for x in re.findall(r'\[class~="([^"]*)"\]', html)})
        print(f"[ports] {slug:<20} {kb:6.1f} KB  工具类 {n_utils:>3}  未覆盖 {len(unknown)}")
        if unknown:
            problems[slug] = unknown

        # 头注释（title / @classes 之后的正文）作为本组件的保真说明
        notes = re.sub(r"<!--\s*(?:title:|@classes:)[^>]*?-->", "", frag, count=2)
        nm = re.search(r"<!--([\s\S]*?)-->", notes)
        rows.append({
            "slug": slug, "title": title, "cn": _cn(slug), "kb": kb,
            "utils": n_utils, "unknown": unknown,
            "notes": (nm.group(1).strip() if nm else ""),
        })
        total += 1

    print(f"[ports] 共生成 {total} 个 → {dst}")
    if problems:
        print("[ports] !! 以下类的 CSS 没生成，请检查拼写：")
        for slug, cs in problems.items():
            print(f"    {slug}: {cs}")

    # --only 时不要覆盖整篇文档，避免把未构建的组件写丢
    if not args.only and rows:
        doc = write_ports_doc(root, rows)
        print(f"[ports] 已刷新 {doc}")
    return 0


_CN = {
    "loading-state": "加载状态", "thinking-state": "思考轨迹", "streaming-text": "流式回答",
    "approval-card": "审批卡片", "tool-chips": "工具调用芯片", "task-rows": "任务进度行",
    "chat-composer": "聊天面板", "prompt-bar": "提示栏", "recommendation-card": "推荐卡片",
    "context-cards": "上下文卡片", "diff-table": "差异表格", "records-table": "记录表格",
    "filter-table": "筛选表格", "sidebar-nav": "侧边导航", "search": "命令搜索",
    "flowchart": "流程图", "insight-cards": "洞察卡片", "code-block": "代码块",
    "fine-tune-card": "微调卡片", "selection-actions": "选区操作", "agent-screen": "智能体屏幕",
}


def _cn(slug: str) -> str:
    return _CN.get(slug, slug)


if __name__ == "__main__":
    raise SystemExit(main())
