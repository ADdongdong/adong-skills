#!/usr/bin/env python3
"""
make_foundation.py — 生成 assets/foundation.standalone.css（浏览器可直接用的令牌层）。

上游 foundation.css 是 Tailwind v4 语法，原生浏览器跑不了。转换规则：

  @import "tailwindcss";              → 删除，换成一段极简 reset
  @import "shadow-plugin/unprefixed"; → 删除，把 --shadow-2xs…2xl 的字面值内联进 :root
                                        （--shadow-btn/card/raised/overlay 引用它们）
  @custom-variant dark (...);         → 删除（.dark {} 本身就是普通 CSS）
  @theme inline { ... }               → 整块删除，但必须把 --radius-* / --ease-* / --font-*
                                        搬进 :root，否则圆角与缓动曲线全部丢失；
                                        块内 `--shadow-x: var(--shadow-x)` 是自引用别名，
                                        搬进去会造成变量环，必须丢弃。
  --font-sans/-mono                   → 换成字面字体栈（原来依赖 next/font 注入的 --font-inter）

同时导出 build_utility_css()，供移植器按组件裁剪工具类，使每个单文件 HTML 尽量小。

用法:
  python make_foundation.py [--skill-dir <dir>]
"""
from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from twsubset import build_rule, register_defined_classes  # noqa: E402

# shadow-plugin@2.1.0 /dist/shadow-plugin.unprefixed.css 的字面值
# （该插件在 tailwindcss 之后 @import，它的 @theme 覆盖 Tailwind 默认阴影）
SHADOW_SCALE = {
    "--shadow-2xs": "0 1px 2px 0 rgba(0, 0, 0, 0.03)",
    "--shadow-xs": "0 0 4px 0 rgba(0, 0, 0, 0.04)",
    "--shadow-sm": ("0 18px 47px 0 rgba(0, 0, 0, 0.03), 0 7.5px 19px 0 rgba(0, 0, 0, 0.02), "
                    "0 4px 10.5px 0 rgba(0, 0, 0, 0.02), 0 2.3px 5.8px 0 rgba(0, 0, 0, 0.01), "
                    "0 1.2px 3.1px 0 rgba(0, 0, 0, 0.01), 0 0.5px 1.3px 0 rgba(0, 0, 0, 0.01)"),
    "--shadow-md": ("0 17.54px 23.39px 0 rgba(0, 0, 0, 0.04), 0 9.4px 12.5px 0 rgba(0, 0, 0, 0.03), "
                    "0 5.25px 7px 0 rgba(0, 0, 0, 0.02), 0 2.79px 3.72px -2px rgba(0, 0, 0, 0.01), "
                    "0 1.16px 1.5px 0 rgba(0, 0, 0, 0.01)"),
    "--shadow-lg": ("0 25px 50px 0 rgba(0, 0, 0, 0.05), 0 12px 24px 0 rgba(0, 0, 0, 0.04), "
                    "0 6px 12px 0 rgba(0, 0, 0, 0.03), 0 3px 6px 0 rgba(0, 0, 0, 0.02), "
                    "0 1.5px 3px 0 rgba(0, 0, 0, 0.02)"),
    "--shadow-xl": ("0 40px 80px 0 rgba(0, 0, 0, 0.06), 0 20px 40px 0 rgba(0, 0, 0, 0.05), "
                    "0 10px 20px 0 rgba(0, 0, 0, 0.04), 0 5px 10px 0 rgba(0, 0, 0, 0.03), "
                    "0 2px 4px 0 rgba(0, 0, 0, 0.02)"),
    "--shadow-2xl": ("0 60px 120px 0 rgba(0, 0, 0, 0.07), 0 30px 60px 0 rgba(0, 0, 0, 0.06), "
                     "0 15px 30px 0 rgba(0, 0, 0, 0.05), 0 7.5px 15px 0 rgba(0, 0, 0, 0.04), "
                     "0 3px 6px 0 rgba(0, 0, 0, 0.03)"),
}

RESET = """/* ── minimal reset（替代 @import "tailwindcss"）─────────────── */
*,
*::before,
*::after {
  box-sizing: border-box;
  border: 0 solid;
}
html {
  -webkit-text-size-adjust: 100%;
  tab-size: 4;
}
body {
  margin: 0;
}
h1, h2, h3, h4, h5, h6, p, figure, blockquote, dl, dd, pre {
  margin: 0;
}
ol, ul, menu {
  margin: 0;
  padding: 0;
  list-style: none;
}
button, input, optgroup, select, textarea {
  margin: 0;
  padding: 0;
  color: inherit;
  font: inherit;
  letter-spacing: inherit;
  background: transparent;
  border-radius: 0;
}
button, [type="button"], [type="reset"], [type="submit"] {
  appearance: button;
}
textarea {
  resize: vertical;
}
img, svg, video, canvas, audio, iframe, embed, object {
  display: block;
  vertical-align: middle;
}
img, video {
  max-width: 100%;
  height: auto;
}
table {
  border-collapse: collapse;
  border-color: inherit;
  text-indent: 0;
}
a {
  color: inherit;
  text-decoration: inherit;
}
:disabled {
  cursor: default;
}
"""

# Tailwind 的 theme 别名 → 必须搬进 :root 的部分（丢掉 --color-* 与自引用 --shadow-*）
MOVE_KEYS = re.compile(r"^--(?:radius|ease|font)-")


def _find_block(css: str, needle: str) -> tuple[int, int] | None:
    """定位 needle 对应的顶层 { ... } 区间，返回 [start, end)（含选择器）。"""
    i = css.find(needle)
    while i >= 0:
        j = css.find("{", i)
        if j < 0:
            return None
        depth, k = 0, j
        while k < len(css):
            if css[k] == "{":
                depth += 1
            elif css[k] == "}":
                depth -= 1
                if depth == 0:
                    return i, k + 1
            k += 1
        return None
    return None


def _split_decls(body: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for m in re.finditer(r"(--[A-Za-z0-9-]+)\s*:\s*([^;]+);", body):
        out.append((m.group(1), " ".join(m.group(2).split())))
    return out


def build_tokens(foundation_css: str) -> str:
    root_blk = _find_block(foundation_css, ":root {")
    dark_blk = _find_block(foundation_css, ".dark {")
    theme_blk = _find_block(foundation_css, "@theme inline")
    if not (root_blk and dark_blk and theme_blk):
        raise RuntimeError("foundation.css 结构不符合预期（缺 :root / .dark / @theme inline）")

    root_body = foundation_css[foundation_css.find("{", root_blk[0]) + 1:root_blk[1] - 1]
    dark_body = foundation_css[foundation_css.find("{", dark_blk[0]) + 1:dark_blk[1] - 1]
    theme_body = foundation_css[foundation_css.find("{", theme_blk[0]) + 1:theme_blk[1] - 1]

    moved = [(k, v) for k, v in _split_decls(theme_body) if MOVE_KEYS.match(k)]
    root = _split_decls(root_body)
    dark = _split_decls(dark_body)

    # 字面字体栈：上游靠 next/font 注入 --font-inter / --font-mono-face
    def fix_fonts(decls: list[tuple[str, str]]) -> list[tuple[str, str]]:
        out = []
        for k, v in decls:
            if k == "--font-sans":
                v = "'Inter', ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif"
            elif k == "--font-mono":
                v = "'JetBrains Mono', ui-monospace, 'SF Mono', Menlo, Consolas, monospace"
            out.append((k, v))
        return out

    moved = fix_fonts(moved)

    def emit(decls: list[tuple[str, str]], indent: str = "  ") -> str:
        return "\n".join(f"{indent}{k}: {v};" for k, v in decls)

    parts = ["/* ── design tokens ─────────────────────────────────────────── */",
             ":root {",
             "  /* surfaces / ink / borders / accent / semantic（上游原文）*/",
             emit(root),
             "",
             "  /* 从 @theme inline 搬入：不搬的话圆角与缓动曲线会全部丢失 */",
             emit(moved),
             "",
             "  /* 阴影刻度：来自 shadow-plugin@2.1.0/unprefixed（必须内联，不能留 @import）*/",
             emit(list(SHADOW_SCALE.items())),
             "}",
             "",
             ".dark {",
             emit(dark),
             "}"]
    return "\n".join(parts)


def _extract_upstream_gap_rules(up: str) -> str:
    """捞回被上游 registry 切片漏掉的组件级 CSS。

    上游的 build-registry 是按行区间切 `app/globals.css` 的：
      foundation   = globals[0:423] + globals[1331:]
      sidebar-nav  = + globals[424:505]
      records-table= + globals[506:1331]
    `records-table.css` 正好在 `@keyframes records-pulse` 处结束，
    紧跟其后的

        /* agent-screen — a static decorative cursor sitting on the capture */
        .agent-cursor { ... }

    就落在所有区间之外 —— 三个 registry 产物里**都没有它**（实测 grep 全为 0）。
    因为 AgentScreen 本身也不在 registry 里，上游大概没注意到。
    这里把它从 globals.css 原文捞回来，否则移植版的光标会丢投影。
    """
    p = os.path.join(up, "app", "globals.css")
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8") as fh:
        g = fh.read()
    out = []
    for sel, marker in ((".agent-cursor", "/* agent-screen"),):
        if sel in g:
            r = _find_block(g, sel)
            if r:
                start = g.rfind(marker, 0, r[0])
                chunk = g[start if start >= 0 else r[0]:r[1]]
                out.append(chunk.strip())
    return "\n\n".join(out)


def build_foundation(up: str, include_extras: set[str] | None = None) -> str:
    """组装 foundation CSS。

    include_extras 控制是否并入两个「重量级」附加样式表：
      - records-table.css（约 16KB，825 行 .records-*）
      - sidebar-nav.css（约 2KB .sidebar-*）
    只有对应组件需要它们。全量版传 None（两个都带上，供 React 项目与预览页用）；
    build_ports 会按组件只带上真正用到的那份，避免把 16KB 无关 CSS 塞进 19 个文件。
    """
    with open(os.path.join(up, "app", "globals.css"), encoding="utf-8") as fh:
        _globals = fh.read()  # 留作交叉校验用
    with open(os.path.join(up, "app", "beautifui", "foundation.css"), encoding="utf-8") as fh:
        css = fh.read()

    tokens = build_tokens(css)

    # 剥掉 @import / @custom-variant / @theme inline 三块
    body = css
    body = re.sub(r'@import\s+["\'][^"\']+["\']\s*;', "", body)
    body = re.sub(r"@custom-variant[^;]*;", "", body)
    for needle in (":root {", ".dark {", "@theme inline"):
        r = _find_block(body, needle)
        if r:
            body = body[:r[0]] + body[r[1]:]

    want = {"records-table.css", "sidebar-nav.css"} if include_extras is None else include_extras
    extra = []
    gap = _extract_upstream_gap_rules(up)
    if gap:
        extra.append("/* ══ 上游 registry 切片遗漏的组件级 CSS（从 globals.css 原文捞回）══\n"
                     " * 见 _extract_upstream_gap_rules() 的说明。\n * ══ */\n" + gap)
    for name in ("records-table.css", "sidebar-nav.css"):
        if name not in want:
            continue
        p = os.path.join(up, "app", "beautifui", name)
        if os.path.exists(p):
            with open(p, encoding="utf-8") as fh:
                extra.append(f"/* ══ {name}（上游 registry 内嵌，不在 git 树里）══ */\n" + fh.read())

    out = "\n".join([
        "/* ============================================================",
        " * Beautiful UI — foundation.standalone.css",
        " * 由 scripts/make_foundation.py 生成，请勿手改。",
        " * 上游：Beautiful UI by Shane Levine (Turbo) — MIT",
        " * https://github.com/slev12397/beautiful-ui  ·  https://www.beautifului.dev",
        " * ============================================================ */",
        "",
        RESET,
        tokens,
        "",
        body.strip(),
        "",
        "\n\n".join(extra),
        "",
    ])

    # 把本文件里定义过的类名登记给编译器：
    # `.records-*` / `.sidebar-*` / `.is-*` 等状态钩子的选择器已经写在这里，
    # 不该再被当成"工具类"生成一遍，否则 build_ports 会报一堆假的"未覆盖类"，
    # 把真正需要关注的拼写错误淹没。
    register_defined_classes(out)
    register_defined_classes(RESET)
    return out


_DURATION_LIKE = re.compile(r"^(duration|ease|delay|animate)-")


def _order_key(c: str) -> tuple[int, str]:
    """工具类的输出顺序。

    关键：`transition` / `transition-*` 会顺带把 transition-duration 设成默认 150ms，
    必须排在 `duration-*` / `ease-*` / `delay-*` / `animate-*` **之前**，
    否则 `transition-[opacity,transform] duration-300` 这种组合会被 150ms 覆盖掉。
    （按名字纯字母序排时 `duration-300` 会排在 `transition-[…]` 前面，正是这个 bug。）
    """
    if c == "transition" or c.startswith("transition-"):
        return (0, c)
    if _DURATION_LIKE.match(c):
        return (1, c)
    return (2, c)


def build_utility_css(classes: set[str]) -> tuple[str, list[str]]:
    """按给定的类集合生成工具类 CSS，返回 (css, 未覆盖类)。"""
    rules, unhandled = [], []
    for c in sorted(classes, key=_order_key):
        r = build_rule(c)
        if r is None:
            unhandled.append(c)
        elif r:
            rules.append("\n".join(r))
    header = ("/* ── 工具类（Tailwind 子集，由 twsubset.py 编译）───────────────\n"
              " * 颜色/圆角/阴影/缓动全部引用同名 var(--token)，\n"
              " * 因此配色与动效曲线与官网一致。\n"
              " * 选择器一律写成 [class~=] 属性形式而非转义类名：\n"
              " * 工具类含斜杠、冒号、方括号、百分号，转义极易出错。\n"
              " */")
    return header + "\n\n" + "\n\n".join(rules) + "\n", unhandled


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill-dir", default=os.path.join(os.path.expanduser("~"), ".workbuddy", "skills", "beautifului"))
    args = ap.parse_args()
    root = os.path.abspath(args.skill_dir)
    up = os.path.join(root, "assets", "upstream")
    out = os.path.join(root, "assets", "foundation.standalone.css")

    css = build_foundation(up)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(css)

    # 断言：令牌与 keyframe 一个都不能少
    kf_src = set(re.findall(r"@keyframes\s+([\w-]+)", re.search(
        r"@keyframes[\s\S]*?(?=/\* ══ records-table)", css).group(0) if re.search(
        r"@keyframes[\s\S]*?(?=/\* ══ records-table)", css) else css))
    need_kf = {"shimmer-text", "fade-up", "fade-in", "eq-bounce",
               "caret-blink", "pop-in", "spin", "pixel-on"}
    seen = set(re.findall(r"@keyframes\s+([\w-]+)", css))
    missing_kf = need_kf - seen
    for var in ("--ease-out-strong", "--ease-in-out-strong", "--ease-link",
                "--radius-chip", "--radius-control", "--radius-card", "--radius-window",
                "--shadow-xs", "--shadow-sm", "--shadow-md", "--shadow-lg",
                "--accent", "--ink", "--surface", "--line"):
        if var not in css:
            print(f"  !! 缺令牌 {var}", file=sys.stderr)

    print(f"[foundation] 写入 {out}")
    print(f"[foundation] 体积 {len(css)} 字符 / {css.count(chr(10)) + 1} 行")
    print(f"[foundation] keyframes 共 {len(seen)} 个，缺失 {sorted(missing_kf) or '无'}")
    print(f"[foundation] 含 records-table.css: {'records-row' in css}")
    print(f"[foundation] 含 sidebar-nav.css:   {'sidebar-' in css}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
