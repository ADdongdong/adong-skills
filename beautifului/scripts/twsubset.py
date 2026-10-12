#!/usr/bin/env python3
"""
twsubset.py — Beautiful UI 的 Tailwind v4 子集编译器（库 + CLI）。

为什么需要它:
  21 个组件全部用 Tailwind 工具类写样式。要移植成零依赖单文件 HTML，有两条路：
  ① 手工把几千个工具类翻译成长写 CSS —— 易错、难维护、必然漂移；
  ② 为本设计系统编译出「刚好覆盖所需工具类」的 CSS —— 本文件。
  选 ②：markup 几乎原样保留（class="flex w-full ..."），CSS 由机器生成，
  颜色/圆角/阴影/缓动一律引用同名 var(--token)，所以动效与官网一致。

关键实现选择:
  - 用属性选择器 `[class~="..."]` 而不是转义类选择器 `.p-3`。
    工具类含 `:` `/` `[` `]` `.` `%`，转义极易出错；[class~=] 天然安全，
    特异性等同单个类。
  - 命名 group（group/row + group-hover/row:）用
    `[class~="group/row"]:hover &` 表达，避免转义。

用法（CLI 用于覆盖面自检）:
  python twsubset.py --skill-dir <dir> [--report]
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys
import tempfile
from collections import OrderedDict

SPACING_REM = 0.25

TEXT_SIZES = {
    "xs": ("0.75rem", "1rem"), "sm": ("0.875rem", "1.25rem"), "base": ("1rem", "1.5rem"),
    "lg": ("1.125rem", "1.75rem"), "xl": ("1.25rem", "1.75rem"), "2xl": ("1.5rem", "2rem"),
    "3xl": ("1.875rem", "2.25rem"), "4xl": ("2.25rem", "2.5rem"),
}
FONT_WEIGHTS = {"thin": 100, "extralight": 200, "light": 300, "normal": 400, "medium": 500,
                "semibold": 600, "bold": 700, "extrabold": 800, "black": 900}
LEADING = {"none": "1", "tight": "1.25", "snug": "1.375", "normal": "1.5",
           "relaxed": "1.625", "loose": "2"}
RADIUS_FIXED = {"none": "0", "sm": "0.125rem", "md": "0.375rem", "lg": "0.5rem",
                "xl": "0.75rem", "2xl": "1rem", "3xl": "1.5rem", "full": "9999px"}

COLOR_TOKENS = {
    "page", "canvas", "surface", "inset", "hover", "hover-2", "ink", "ink-2", "ink-3",
    "line", "line-strong", "line-soft", "field", "accent", "accent-ink", "accent-tint",
    "green", "green-tint", "orange", "orange-tint", "red", "red-tint",
    "tooltip-bg", "tooltip-fg", "tooltip-muted", "tooltip-border", "stripe", "stripe-bg",
    "grid-line",
}
BOOL_COLORS = {"white", "black", "transparent", "current", "inherit"}
SHADOW_TOKENS = {"hairline", "btn", "card", "raised", "overlay", "inset-field",
                 "xs", "sm", "md", "lg", "xl", "2xl"}
RADIUS_TOKENS = {"chip", "control", "card", "window"}

# 变体 → 选择器模板（`&` 代表元素自身；无 `&` 视为祖先/后代模板）
VARIANTS: "OrderedDict[str, str]" = OrderedDict([
    ("first:", "&:first-child"), ("last:", "&:last-child"), ("odd:", "&:nth-child(odd)"),
    ("even:", "&:nth-child(even)"),
    ("placeholder:", "&::placeholder"), ("selection:", "&::selection"),
    ("before:", "&::before"), ("after:", "&::after"),
    ("hover:", "&:hover"), ("focus:", "&:focus"), ("focus-visible:", "&:focus-visible"),
    ("focus-within:", "&:focus-within"), ("active:", "&:active"),
    ("disabled:", "&:disabled"), ("enabled:", "&:enabled"), ("open:", "&[open]"),
    ("sm:", "@media (min-width:40rem)"), ("md:", "@media (min-width:48rem)"),
    ("lg:", "@media (min-width:64rem)"), ("xl:", "@media (min-width:80rem)"),
    ("2xl:", "@media (min-width:96rem)"),
    ("dark:", ".dark &"), ("motion-reduce:", "@media (prefers-reduced-motion:reduce)"),
    ("motion-safe:", "@media (prefers-reduced-motion:no-preference)"),
])

# 方向 → 属性后缀（**不含前导短横**）。
# 之前带短横会让 inset 生成 `-top: 0rem` 这种非法属性名。
SIDES = {"x": ("left", "right"), "y": ("top", "bottom"), "t": ("top",),
         "b": ("bottom",), "l": ("left",), "r": ("right",),
         "s": ("inline-start",), "e": ("inline-end",)}
CORNER = {"t": ("-top-left", "-top-right"), "b": ("-bottom-left", "-bottom-right"),
          "l": ("-top-left", "-bottom-left"), "r": ("-top-right", "-bottom-right"),
          "tl": ("-top-left",), "tr": ("-top-right",),
          "bl": ("-bottom-left",), "br": ("-bottom-right",)}

# ── 不需要生成 CSS 的类 ─────────────────────────────────────────────
# ① 自定义 CSS 已在 foundation / records-table / sidebar-nav 中提供
PASSTHROUGH_EXACT = {
    "stream-tail", "stream-caret", "is-streaming", "source-avatar",
    "primitive-card-pad", "primitive-card-bar", "primitive-card-footer",
    "primitive-table-cell", "primitive-icon-button", "component-nav-scroll",
    "animated-underline", "theme-switching", "home-reveal", "primitive-showcase",
    "filter-status-todo", "filter-status-progress", "filter-status-done",
    "insight-chart-stage", "insight-chart-cursor", "insight-chart-tooltip-anchor",
    "insight-chart-tooltip", "insight-chart-tooltip-item", "insight-chart-tooltip-dot",
    # 命名 group 标记：仅作为祖先钩子，无需样式
    "group/glide", "group/glide-menu", "group/row", "group/screen", "group",
    # AgentScreen 自绘光标的语义钩子（样式由 foundation 提供）
    "agent-cursor",
}
PASSTHROUGH_PREFIX = ("records-", "sidebar-")


def is_passthrough(c: str) -> bool:
    return c in PASSTHROUGH_EXACT or c in _DEFINED or c.startswith(PASSTHROUGH_PREFIX)


# 由上游自定义 CSS 定义的类名（.records-*、.sidebar-*、.is-* 等状态钩子）。
# 这些类**不该**由工具类编译器生成 —— 它们的选择器已经在 foundation /
# records-table.css / sidebar-nav.css 里写好了。
# 不注册的话，它们会被报成「未覆盖类」，把真正需要关注的拼写错误淹没。
_DEFINED: set[str] = set()


def register_defined_classes(css: str) -> int:
    """扫描一段 CSS，记录其中出现的所有类名。返回累计数量。"""
    _DEFINED.update(re.findall(r"\.([A-Za-z_][\w-]*)", css))
    return len(_DEFINED)


def rem(v: float) -> str:
    s = f"{v * SPACING_REM:.4f}".rstrip("0").rstrip(".")
    return f"{s}rem"


def arb(tok: str) -> str | None:
    if tok.startswith("[") and tok.endswith("]"):
        return tok[1:-1].replace("_", " ")
    return None


def size_value(tok: str) -> str | None:
    if not tok:
        return None
    a = arb(tok)
    if a is not None:
        return a
    fixed = {"full": "100%", "screen": "100vh", "svh": "100svh", "dvh": "100dvh",
             "min": "min-content", "max": "max-content", "fit": "fit-content",
             "px": "1px", "auto": "auto"}
    if tok in fixed:
        return fixed[tok]
    m = re.fullmatch(r"(\d+)/(\d+)", tok)
    if m:
        return f"{int(m.group(1)) / int(m.group(2)) * 100:.6f}".rstrip("0").rstrip(".") + "%"
    if re.fullmatch(r"\d+(?:\.\d+)?", tok):
        return rem(float(tok))
    return None


def split_opacity(tok: str) -> tuple[str, str | None]:
    """`black/60` → ('black', '60')。"""
    m = re.fullmatch(r"(.+)/(\d{1,3})", tok)
    if m and not m.group(1).endswith("]"):
        return m.group(1), m.group(2)
    return tok, None


def is_length(v: str) -> bool:
    """任意值看起来是不是长度（用来把 `text-[13px]` 和 `border-[1.2px]`
    从"颜色"分支里救出来 —— 否则会被当成 color: 13px 这种废值）。"""
    return bool(re.fullmatch(
        r"-?[\d.]+(px|rem|em|%|vh|vw|svh|dvh|ch|ex|pt|pc|in|cm|mm)?", v.strip()))


def color_value(tok: str) -> str | None:
    a = arb(tok)
    if a is not None:
        return a
    if tok in COLOR_TOKENS:
        return f"var(--{tok})"
    if tok in BOOL_COLORS:
        return "currentColor" if tok == "current" else tok
    return None


def with_alpha(val: str, pct: str | None) -> str:
    if pct is None:
        return val
    return f"color-mix(in srgb, {val} {pct}%, transparent)"


# ══════════════════════════════════════════════════════════════════
def compile_core(c: str) -> list[str] | None:
    """编译「已剥离变体」的工具类 → 声明列表。None = 无法处理。"""
    important = False
    if c.endswith("!") and len(c) > 1:
        important, c = True, c[:-1]
    elif c.startswith("!"):
        important, c = True, c[1:]

    decls: list[str] = []

    def add(prop: str, val: str) -> None:
        decls.append(f"{prop}: {val}{' !important' if important else ''}")

    # 任意属性：[cursor:none]
    a = arb(c)
    if a is not None and ":" in a:
        p, v = a.split(":", 1)
        add(p.strip(), v.strip())
        return decls

    # ── 单个关键字映射 ──
    simple = {
        "flex": "display:flex", "inline-flex": "display:inline-flex",
        "grid": "display:grid", "inline-grid": "display:inline-grid",
        "block": "display:block", "inline-block": "display:inline-block",
        "inline": "display:inline", "hidden": "display:none",
        "contents": "display:contents", "table": "display:table",
        "table-row": "display:table-row", "table-cell": "display:table-cell",
        "flow-root": "display:flow-root", "list-item": "display:list-item",
        "absolute": "position:absolute", "relative": "position:relative",
        "fixed": "position:fixed", "sticky": "position:sticky", "static": "position:static",
        "isolate": "isolation:isolate",
        "flex-row": "flex-direction:row", "flex-col": "flex-direction:column",
        "flex-row-reverse": "flex-direction:row-reverse",
        "flex-col-reverse": "flex-direction:column-reverse",
        "flex-wrap": "flex-wrap:wrap", "flex-nowrap": "flex-wrap:nowrap",
        "flex-wrap-reverse": "flex-wrap:wrap-reverse",
        "flex-1": "flex:1 1 0%", "flex-auto": "flex:1 1 auto",
        "flex-none": "flex:none", "flex-initial": "flex:0 1 auto",
        "grow": "flex-grow:1", "grow-0": "flex-grow:0",
        "shrink": "flex-shrink:1", "shrink-0": "flex-shrink:0",
        "items-start": "align-items:flex-start", "items-end": "align-items:flex-end",
        "items-center": "align-items:center", "items-baseline": "align-items:baseline",
        "items-stretch": "align-items:stretch",
        "justify-start": "justify-content:flex-start", "justify-end": "justify-content:flex-end",
        "justify-center": "justify-content:center",
        "justify-between": "justify-content:space-between",
        "justify-around": "justify-content:space-around",
        "justify-evenly": "justify-content:space-evenly",
        "justify-normal": "justify-content:normal",
        "justify-self-start": "justify-self:start", "justify-self-end": "justify-self:end",
        "justify-self-center": "justify-self:center",
        "justify-self-stretch": "justify-self:stretch",
        "justify-self-auto": "justify-self:auto",
        "self-start": "align-self:flex-start", "self-end": "align-self:flex-end",
        "self-center": "align-self:center", "self-stretch": "align-self:stretch",
        "self-auto": "align-self:auto", "self-baseline": "align-self:baseline",
        "place-items-center": "place-items:center", "place-content-center": "place-content:center",
        "place-self-center": "place-self:center",
        "content-center": "align-content:center", "content-start": "align-content:flex-start",
        "content-end": "align-content:flex-end",
        "content-between": "align-content:space-between",
        "overflow-hidden": "overflow:hidden", "overflow-auto": "overflow:auto",
        "overflow-visible": "overflow:visible", "overflow-scroll": "overflow:scroll",
        "overflow-clip": "overflow:clip",
        "overflow-x-hidden": "overflow-x:hidden", "overflow-y-hidden": "overflow-y:hidden",
        "overflow-x-auto": "overflow-x:auto", "overflow-y-auto": "overflow-y:auto",
        "overflow-x-visible": "overflow-x:visible", "overflow-y-visible": "overflow-y:visible",
        "overflow-x-clip": "overflow-x:clip", "overflow-y-clip": "overflow-y:clip",
        "whitespace-nowrap": "white-space:nowrap", "whitespace-normal": "white-space:normal",
        "whitespace-pre": "white-space:pre", "whitespace-pre-wrap": "white-space:pre-wrap",
        "break-words": "overflow-wrap:break-word", "break-all": "word-break:break-all",
        "break-keep": "word-break:keep-all",
        "tabular-nums": "font-variant-numeric:tabular-nums",
        "select-none": "user-select:none", "select-text": "user-select:text",
        "select-all": "user-select:all", "select-auto": "user-select:auto",
        "pointer-events-none": "pointer-events:none", "pointer-events-auto": "pointer-events:auto",
        "cursor-pointer": "cursor:pointer", "cursor-default": "cursor:default",
        "cursor-grab": "cursor:grab", "cursor-grabbing": "cursor:grabbing",
        "cursor-text": "cursor:text", "cursor-not-allowed": "cursor:not-allowed",
        "cursor-col-resize": "cursor:col-resize", "cursor-row-resize": "cursor:row-resize",
        "cursor-ew-resize": "cursor:ew-resize", "cursor-help": "cursor:help",
        "cursor-move": "cursor:move", "cursor-zoom-in": "cursor:zoom-in",
        "cursor-zoom-out": "cursor:zoom-out", "cursor-none": "cursor:none",
        "resize-none": "resize:none", "resize-y": "resize:vertical", "resize-x": "resize:horizontal",
        "antialiased": "-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale",
        "italic": "font-style:italic", "not-italic": "font-style:normal",
        "underline": "text-decoration-line:underline",
        "no-underline": "text-decoration-line:none",
        "line-through": "text-decoration-line:line-through",
        "underline-offset-1": "text-underline-offset:1px",
        "underline-offset-2": "text-underline-offset:2px",
        "underline-offset-4": "text-underline-offset:4px",
        "uppercase": "text-transform:uppercase", "lowercase": "text-transform:lowercase",
        "capitalize": "text-transform:capitalize", "normal-case": "text-transform:none",
        "text-left": "text-align:left", "text-center": "text-align:center",
        "text-right": "text-align:right", "text-start": "text-align:start",
        "text-end": "text-align:end", "text-justify": "text-align:justify",
        "align-middle": "vertical-align:middle", "align-top": "vertical-align:top",
        "align-bottom": "vertical-align:bottom", "align-baseline": "vertical-align:baseline",
        "align-text-bottom": "vertical-align:text-bottom",
        "align-text-top": "vertical-align:text-top",
        "align-sub": "vertical-align:sub", "align-super": "vertical-align:super",
        "list-none": "list-style-type:none", "list-disc": "list-style-type:disc",
        "list-decimal": "list-style-type:decimal",
        "appearance-none": "appearance:none",
        "bg-clip-text": "-webkit-background-clip:text;background-clip:text",
        "bg-clip-border": "background-clip:border-box",
        "bg-clip-padding": "background-clip:padding-box",
        "bg-none": "background-image:none", "bg-fixed": "background-attachment:fixed",
        "bg-local": "background-attachment:local", "bg-scroll": "background-attachment:scroll",
        "bg-cover": "background-size:cover", "bg-contain": "background-size:contain",
        "bg-auto": "background-size:auto", "bg-center": "background-position:center",
        "bg-no-repeat": "background-repeat:no-repeat", "bg-repeat": "background-repeat:repeat",
        "object-cover": "object-fit:cover", "object-contain": "object-fit:contain",
        "object-fill": "object-fit:fill", "object-none": "object-fit:none",
        "object-top": "object-position:top", "object-center": "object-position:center",
        "object-bottom": "object-position:bottom",
        "transform": "transform:translateZ(0)",
        "transform-none": "transform:none",
        "will-change-transform": "will-change:transform",
        "will-change-scroll": "will-change:scroll-position",
        "backface-hidden": "backface-visibility:hidden",
        "outline-none": "outline:2px solid transparent;outline-offset:2px",
        "invisible": "visibility:hidden", "visible": "visibility:visible",
        "collapse": "visibility:collapse",
        "border-collapse": "border-collapse:collapse", "border-separate": "border-collapse:separate",
        "table-fixed": "table-layout:fixed", "table-auto": "table-layout:auto",
        "box-decoration-clone": "-webkit-box-decoration-break:clone;box-decoration-break:clone",
        "box-decoration-slice": "-webkit-box-decoration-break:slice;box-decoration-break:slice",
        "touch-none": "touch-action:none", "touch-auto": "touch-action:auto",
        "touch-pan-y": "touch-action:pan-y", "touch-pan-x": "touch-action:pan-x",
        "sr-only": ("position:absolute;width:1px;height:1px;padding:0;margin:-1px;"
                    "overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border-width:0"),
        "not-sr-only": ("position:static;width:auto;height:auto;padding:0;margin:0;"
                        "overflow:visible;clip:auto;white-space:normal"),
        "border": "border-width:1px;border-style:solid",
    }
    if c in simple:
        for part in simple[c].split(";"):
            if ":" in part:
                p, v = part.split(":", 1)
                add(p.strip(), v.strip())
        return decls

    # ── vertical-align 任意值：align-[-1px] ──
    m = re.fullmatch(r"align-(\[.+\]|\d+(?:\.\d+)?(?:px|rem|em|%))", c)
    if m:
        add("vertical-align", arb(m.group(1)) or m.group(1))
        return decls

    # ── truncate ──
    if c == "truncate":
        add("overflow", "hidden")
        add("text-overflow", "ellipsis")
        add("white-space", "nowrap")
        return decls
    if c == "text-ellipsis":
        add("text-overflow", "ellipsis")
        return decls

    # ── 间距 / inset ──
    # 三种命名形态各不相同，必须分开匹配（用一个正则必然顾此失彼）：
    #   m/p    → 方向直接后缀：mb-1 / px-2.5 / -ml-2（kind 与 side 之间无短横）
    #   gap/set→ 方向带短横：gap-x-1 / inset-y-0
    #   定位   → top-0 / left-1/2 / bottom-full
    kind = side = tok = None
    neg = bool(re.match(r"^-", c))
    body = c[1:] if neg else c
    m = re.fullmatch(r"([pm])([xytrblse])?-?(.+)", body)
    if m and size_value(m.group(3)):
        kind, side, tok = m.group(1), m.group(2), m.group(3)
    else:
        m = re.fullmatch(r"(gap|inset)(?:-([xytrblse]))?-?(.+)", body)
        if m and size_value(m.group(3)):
            kind, side, tok = m.group(1), m.group(2), m.group(3)
        else:
            m = re.fullmatch(r"(top|right|bottom|left|start|end)-?(.+)", body)
            if m and size_value(m.group(2)):
                kind, side, tok = m.group(1), None, m.group(2)
    if kind and tok:
        val = size_value(tok)
        if val:
            if neg and re.match(r"^[\d.]|^var\(|^calc\(", val):
                val = f"calc({val} * -1)"
            if kind in ("p", "m"):
                if side:
                    for s in SIDES.get(side, ()):
                        add(f"{'padding' if kind == 'p' else 'margin'}-{s}", val)
                else:
                    add("padding" if kind == "p" else "margin", val)
            elif kind == "gap":
                add("gap" if not side else ("column-gap" if side == "x" else "row-gap"), val)
            elif kind == "inset":
                if side in ("x", "y"):
                    for s in SIDES[side]:
                        add(s, val)
                elif side:
                    add(SIDES[side][0], val)
                else:
                    add("inset", val)
            else:
                add(kind, val)
            return decls

    # space-x / space-y
    m = re.fullmatch(r"(-)?space-([xy])-(.+)", c)
    if m:
        neg, ax, tok = m.groups()
        val = size_value(tok)
        if val:
            if neg:
                val = f"calc({val} * -1)"
            decls.append("__SEL__ > * + *")
            add("margin-left" if ax == "x" else "margin-top", val)
            return decls

    # ── 尺寸 ──
    m = re.fullmatch(r"(min-|max-)?(w|h|size|basis)-(.+)", c)
    if m:
        pre, kind, tok = m.groups()
        val = size_value(tok)
        if val:
            if kind == "size":
                add("width", val)
                add("height", val)
            elif kind == "basis":
                add("flex-basis", val)
            else:
                add(f"{pre or ''}{'width' if kind == 'w' else 'height'}", val)
            return decls

    # ── border + 方向 + 颜色：border-t-ink-2（必须早于通用颜色规则和宽度规则）──
    m = re.fullmatch(r"border-([trblxy])-(.+)", c)
    if m:
        side, raw = m.groups()
        tok, pct = split_opacity(raw)
        val = color_value(tok)
        if val:
            val = with_alpha(val, pct)
            if side in ("x", "y"):
                for s in SIDES[side]:
                    add(f"border-{s}-color", val)
            else:
                add(f"border-{SIDES[side][0]}-color", val)
            add("border-style", "solid")
            return decls

    # ── text-<尺寸> vs text-<颜色> 消歧（必须在通用颜色规则之前）──
    # `text-[13px]` 是字号，`text-[#0285FF]` 是颜色。只看值形态判断。
    m = re.fullmatch(r"text-(.+)", c)
    if m:
        tok = m.group(1)
        a = arb(tok)
        if a is not None:
            is_len = bool(re.fullmatch(
                r"-?[\d.]+(px|rem|em|%|vh|vw|svh|dvh)?", a.strip()))
            if is_len:
                add("font-size", a)
                return decls
        elif tok in TEXT_SIZES:
            add("font-size", TEXT_SIZES[tok][0])
            add("line-height", TEXT_SIZES[tok][1])
            return decls

    # ── 颜色（含 /透明度 修饰符）──
    m = re.fullmatch(
        r"(bg|text|border|fill|stroke|divide|ring|outline|decoration|accent|caret|placeholder)-(.+)", c)
    if m:
        kind, raw = m.groups()
        tok, pct = split_opacity(raw)
        a = arb(tok)
        # `border-[1.2px]` 是宽度而不是颜色；不分流出去会生成 `border-color: 1.2px`
        if kind == "border" and a is not None and is_length(a):
            add("border-width", a)
            add("border-style", "solid")
            return decls
        val = color_value(tok)
        if val:
            val = with_alpha(val, pct)
            prop = {
                "bg": "background-color", "text": "color", "border": "border-color",
                "fill": "fill", "stroke": "stroke", "divide": "border-color",
                "ring": "--tw-ring-color", "outline": "outline-color",
                "decoration": "text-decoration-color", "accent": "accent-color",
                "caret": "caret-color", "placeholder": "color",
            }[kind]
            add(prop, val)
            if kind in ("border", "divide"):
                add("border-style", "solid")
            if kind == "outline":
                add("outline-style", "solid")
            return decls

    # ── 阴影 ──
    m = re.fullmatch(r"shadow(?:-(.+))?", c)
    if m:
        tok = m.group(1)
        if tok is None:
            add("box-shadow", "var(--shadow-card)")
            return decls
        a = arb(tok)
        add("box-shadow", a if a is not None else f"var(--shadow-{tok})")
        return decls

    # ── ring（简化为 1px 外描边，与 Tailwind 的 ring 视觉一致）──
    m = re.fullmatch(r"ring(?:-(inset))?-(\d+)", c)
    if m:
        add("box-shadow", f"0 0 0 {m.group(2)}px var(--tw-ring-color, currentColor)")
        return decls
    if c == "ring":
        add("box-shadow", "0 0 0 1px var(--tw-ring-color, currentColor)")
        return decls

    # ── 边框宽度 ──
    m = re.fullmatch(r"border-([trblxy])?-?(\d+|\[.+\])?", c)
    if m and (m.group(1) or m.group(2)):
        side, tok = m.groups()
        val = arb(tok) if tok and tok.startswith("[") else (f"{tok}px" if tok else "1px")
        val = val or "1px"
        if side in ("x", "y"):
            for s in SIDES[side]:
                add(f"border-{s}-width", val)
        elif side in ("t", "b", "l", "r"):
            add(f"border-{SIDES[side][0]}-width", val)
        else:
            add("border-width", val)
        add("border-style", "solid")
        return decls

    # ── 圆角 ──
    m = re.fullmatch(r"rounded(?:-(.+))?", c)
    if m:
        tok = m.group(1)
        if tok is None:
            add("border-radius", "0.25rem")
            return decls
        for key, corners in CORNER.items():
            if tok == key or tok.startswith(key + "-"):
                sub = tok[len(key) + 1:] if tok != key else ""
                if not sub:
                    val = "0.25rem"
                else:
                    a = arb(sub)
                    val = a or RADIUS_FIXED.get(sub) or (
                        f"var(--radius-{sub})" if sub in RADIUS_TOKENS else None)
                if val:
                    for cnr in corners:
                        add(f"border{cnr}-radius", val)
                    return decls
        a = arb(tok)
        if a is not None:
            add("border-radius", a)
            return decls
        if tok in RADIUS_FIXED:
            add("border-radius", RADIUS_FIXED[tok])
            return decls
        if tok in RADIUS_TOKENS:
            add("border-radius", f"var(--radius-{tok})")
            return decls

    # ── 字号 / 字重 / 行高 / 字距 ──
    m = re.fullmatch(r"text-(.+)", c)
    if m:
        tok = m.group(1)
        a = arb(tok)
        if a is not None:
            add("font-size", a)
            return decls
        if tok in TEXT_SIZES:
            add("font-size", TEXT_SIZES[tok][0])
            add("line-height", TEXT_SIZES[tok][1])
            return decls
    m = re.fullmatch(r"font-(.+)", c)
    if m:
        tok = m.group(1)
        a = arb(tok)
        if a is not None:
            add("font-family", a)
            return decls
        if tok in FONT_WEIGHTS:
            add("font-weight", str(FONT_WEIGHTS[tok]))
            return decls
        if tok in ("sans", "mono", "serif"):
            add("font-family", f"var(--font-{tok})")
            return decls
    m = re.fullmatch(r"leading-(.+)", c)
    if m:
        tok = m.group(1)
        a = arb(tok)
        if a is not None:
            add("line-height", a)
            return decls
        if tok in LEADING:
            add("line-height", LEADING[tok])
            return decls
        if re.fullmatch(r"\d+(\.\d+)?", tok):
            add("line-height", rem(float(tok)))
            return decls
    m = re.fullmatch(r"tracking-(.+)", c)
    if m:
        tok = m.group(1)
        a = arb(tok)
        if a is not None:
            add("letter-spacing", a)
            return decls
        tbl = {"tighter": "-0.05em", "tight": "-0.025em", "normal": "0em",
               "wide": "0.025em", "wider": "0.05em", "widest": "0.1em"}
        if tok in tbl:
            add("letter-spacing", tbl[tok])
            return decls

    # ── 数值型工具 ──
    m = re.fullmatch(r"opacity-(.+)", c)
    if m:
        tok = m.group(1)
        a = arb(tok)
        add("opacity", a if a is not None else str(int(tok) / 100))
        return decls
    m = re.fullmatch(r"(-)?z-(.+)", c)
    if m:
        neg, tok = m.groups()
        a = arb(tok)
        val = a or (tok if tok.isdigit() else None)
        if val:
            add("z-index", f"calc({val} * -1)" if neg else val)
            return decls
    m = re.fullmatch(r"(-)?order-(.+)", c)
    if m:
        neg, tok = m.groups()
        if tok.isdigit():
            add("order", f"calc({tok} * -1)" if neg else tok)
            return decls
        if tok in ("first", "last", "none"):
            add("order", {"first": "-9999", "last": "9999", "none": "0"}[tok])
            return decls
    m = re.fullmatch(r"(-)?rotate-(.+)", c)
    if m:
        neg, tok = m.groups()
        a = arb(tok)
        if a is not None:
            add("rotate", f"calc({a} * -1)" if neg else a)
            return decls
        if re.fullmatch(r"\d+(\.\d+)?", tok):
            add("rotate", f"-{tok}deg" if neg else f"{tok}deg")
            return decls
    m = re.fullmatch(r"(-)?scale(?:-([xy]))?-(.+)", c)
    if m:
        neg, ax, tok = m.groups()
        a = arb(tok)
        v = a if a is not None else (str(int(tok) / 100) if tok.isdigit() else None)
        if v:
            if neg:
                v = f"calc({v} * -1)"
            # `scale: x 0.96` 是非法写法；轴向用 1 占位
            add("scale", v if not ax else (f"{v} 1" if ax == "x" else f"1 {v}"))
            return decls
    m = re.fullmatch(r"(-)?(translate|skew)-([xy])-(.+)", c)
    if m:
        neg, op, ax, tok = m.groups()
        a = arb(tok)
        v = a or size_value(tok)
        if v:
            if neg:
                v = f"calc({v} * -1)"
            # 同理：单轴必须补零轴，否则 `translate: x 50%` 非法
            add(op, v if not ax else (f"{v} 0" if ax == "x" else f"0 {v}"))
            return decls

    # ── 滤镜 ──
    m = re.fullmatch(r"(brightness|contrast|saturate|grayscale|invert|sepia|blur)-(?:\[(.+)\]|(\d+))", c)
    if m:
        fn, ab, num = m.groups()
        v = ab if ab is not None else str(int(num) / 100)
        add("filter", f"{fn}({v})")
        return decls
    if c.startswith("backdrop-"):
        return None

    # ── transition / duration / ease / animate ──
    if c == "transition":
        add("transition-property",
            "color, background-color, border-color, box-shadow, opacity, transform")
        add("transition-duration", "150ms")
        add("transition-timing-function", "cubic-bezier(0.4, 0, 0.2, 1)")
        return decls
    m = re.fullmatch(r"transition-(all|colors?|opacity|shadow|transform|none|\[.+\])", c)
    if m:
        tok = m.group(1)
        a = arb(tok)
        props = {"all": "all", "color": "color, background-color, border-color, text-decoration-color, fill, stroke",
                 "colors": "color, background-color, border-color, text-decoration-color, fill, stroke",
                 "opacity": "opacity", "shadow": "box-shadow",
                 "transform": "transform, translate, scale, rotate", "none": "none"}
        add("transition-property", a if a is not None else props[tok])
        add("transition-duration", "150ms")
        add("transition-timing-function", "cubic-bezier(0.4, 0, 0.2, 1)")
        return decls
    m = re.fullmatch(r"duration-(.+)", c)
    if m:
        tok = m.group(1)
        a = arb(tok)
        if a is not None:
            add("transition-duration", a)
            return decls
        if re.fullmatch(r"\d+", tok):
            add("transition-duration", f"{tok}ms")
            return decls
    m = re.fullmatch(r"delay-(.+)", c)
    if m:
        tok = m.group(1)
        a = arb(tok)
        if a is not None:
            add("transition-delay", a)
            return decls
        if re.fullmatch(r"\d+", tok):
            add("transition-delay", f"{tok}ms")
            return decls
    m = re.fullmatch(r"ease-(.+)", c)
    if m:
        tok = m.group(1)
        a = arb(tok)
        if a is not None:
            add("transition-timing-function", a)
            return decls
        tbl = {"linear": "linear", "in": "cubic-bezier(0.4,0,1,1)",
               "out": "cubic-bezier(0,0,0.2,1)", "in-out": "cubic-bezier(0.4,0,0.2,1)"}
        if tok in tbl:
            add("transition-timing-function", tbl[tok])
            return decls
    m = re.fullmatch(r"animate-(.+)", c)
    if m:
        tok = m.group(1)
        a = arb(tok)
        if a is not None:
            add("animation", a)
            return decls
        tbl = {"none": "none", "spin": "spin 1s linear infinite",
               "ping": "ping 1s cubic-bezier(0,0,0.2,1) infinite",
               "pulse": "pulse 2s cubic-bezier(0.4,0,0.6,1) infinite",
               "bounce": "bounce 1s infinite"}
        if tok in tbl:
            add("animation", tbl[tok])
            return decls

    # ── 网格 / flex 定位 ──
    m = re.fullmatch(r"grid-cols-(.+)", c)
    if m:
        tok = m.group(1)
        a = arb(tok)
        n = a or (tok if tok.isdigit() else None)
        if n:
            add("grid-template-columns", n if a is not None else f"repeat({n}, minmax(0, 1fr))")
            return decls
    m = re.fullmatch(r"grid-rows-(.+)", c)
    if m:
        tok = m.group(1)
        a = arb(tok)
        n = a or (tok if tok.isdigit() else None)
        if n:
            add("grid-template-rows", n if a is not None else f"repeat({n}, minmax(0, 1fr))")
            return decls
    m = re.fullmatch(r"(col|row)-span-(.+)", c)
    if m:
        kind, tok = m.groups()
        axis = "column" if kind == "col" else "row"
        a = arb(tok)
        if a is not None:
            add(f"grid-{axis}", f"span {a} / span {a}")
            return decls
        if tok == "full":
            # `span full / span full` 是非法值；Tailwind 的 col-span-full 实为 1 / -1
            add(f"grid-{axis}", "1 / -1")
            return decls
        if tok.isdigit():
            add(f"grid-{axis}", f"span {tok} / span {tok}")
            return decls
    m = re.fullmatch(r"(col|row)-(start|end)-(.+)", c)
    if m:
        kind, which, tok = m.groups()
        if tok.isdigit():
            add(f"grid-{'column' if kind == 'col' else 'row'}-{which}", tok)
            return decls
    m = re.fullmatch(r"aspect-(.+)", c)
    if m:
        tok = m.group(1)
        a = arb(tok)
        if a is not None:
            add("aspect-ratio", a)
            return decls
        if tok in ("square", "video"):
            add("aspect-ratio", {"square": "1 / 1", "video": "16 / 9"}[tok])
            return decls
    m = re.fullmatch(r"line-clamp-(.+)", c)
    if m:
        tok = m.group(1)
        if tok.isdigit():
            add("display", "-webkit-box")
            add("-webkit-box-orient", "vertical")
            add("-webkit-line-clamp", tok)
            add("overflow", "hidden")
            return decls
    m = re.fullmatch(r"columns-(.+)", c)
    if m and m.group(1).isdigit():
        add("columns", m.group(1))
        return decls
    if c in ("inset-x-0", "inset-y-0", "inset-0"):
        return None

    return None


def split_variants(cls: str) -> tuple[list[str], str]:
    """`dark:hover:bg-x` → (['dark:','hover:'], 'bg-x')。支持命名 group。"""
    parts: list[str] = []
    rest = cls
    pat = re.compile(
        r"^("
        r"(?:dark|hover|focus|focus-visible|focus-within|active|disabled|enabled|open|"
        r"first|last|odd|even|placeholder|selection|before|after|"
        r"motion-reduce|motion-safe|print|rtl|ltr|"
        r"sm|md|lg|xl|2xl)"
        r"(?:/[A-Za-z0-9_-]+)?"
        r"|group-(?:hover|focus|active|focus-visible|first|last|disabled)(?:/[A-Za-z0-9_-]+)?"
        r"|group-has-\[[^\]]+\](?:/[A-Za-z0-9_-]+)?"
        r"|peer-(?:hover|focus|active|checked|disabled|focus-visible)(?:/[A-Za-z0-9_-]+)?"
        r"|aria-[A-Za-z0-9_=\[\]\"'-]+"
        r"|data-\[[^\]]+\]"
        r"|has-\[[^\]]+\]"
        r"|not-\[[^\]]+\]"
        r"|supports-\[[^\]]+\]"
        r"|\[[^\]]+\]"
        r"):")
    while True:
        m = pat.match(rest)
        if not m:
            break
        parts.append(m.group(1) + ":")
        rest = rest[m.end():]
    return parts, rest


def variant_selector(prefix: str) -> tuple[str, str] | None:
    """变体前缀 → (选择器模板含 &, 媒体包装)。"""
    if prefix in VARIANTS:
        return VARIANTS[prefix], ""
    if prefix.startswith("group-has-["):
        inner = prefix[len("group-has-"):-1]
        name = ""
        if "/" in inner:
            inner, name = inner.split("/", 1)
        g = f'[class~="group/{name}"]' if name else ".group"
        return f"{g}:has({inner}) &", ""
    m = re.match(r"^group-(hover|focus|active|focus-visible|first|last|disabled)(?:/([A-Za-z0-9_-]+))?:$", prefix)
    if m:
        st, name = m.groups()
        g = f'[class~="group/{name}"]' if name else ".group"
        return f"{g}:{st} &", ""
    m = re.match(r"^peer-(hover|focus|active|checked|disabled|focus-visible)(?:/([A-Za-z0-9_-]+))?:$", prefix)
    if m:
        st, name = m.groups()
        p = f'[class~="peer/{name}"]' if name else ".peer"
        return f"{p}:{st} ~ &", ""
    m = re.match(r"^data-\[([^\]]+)\]$", prefix[:-1])
    if m:
        return f"&[{m.group(1)}]", ""
    m = re.match(r"^aria-([A-Za-z0-9_-]+)(=\S+)?$", prefix[:-1])
    if m:
        attr = m.group(1)
        val = m.group(2) or ""
        if attr.startswith("[") and attr.endswith("]"):
            return f"[aria-{attr[1:-1]}]&", ""
        return f"&[aria-{attr}{val}]", ""
    m = re.match(r"^has-\[([^\]]+)\]$", prefix[:-1])
    if m:
        return f"&:has({m.group(1)})", ""
    m = re.match(r"^not-\[([^\]]+)\]$", prefix[:-1])
    if m:
        return f"&:not({m.group(1)})", ""
    m = re.match(r"^supports-\[([^\]]+)\]$", prefix[:-1])
    if m:
        return f"&", f"@supports ({m.group(1)})"
    return None


def build_rule(cls: str) -> list[str] | None:
    """完整编译一个类 → CSS 行。None = 未覆盖；[] = 无需生成。"""
    # 守卫：工具类必然含字母。没有这一层，`...`、`150ms`、`:` 之类
    # 会被某些宽松分支误判成类并生成垃圾规则。
    if not re.search(r"[A-Za-z]", cls):
        return None
    if is_passthrough(cls):
        return []
    variants, core = split_variants(cls)
    decls = compile_core(core)
    if decls is None:
        return None
    if not decls:
        return []

    sub_sel = ""
    out: list[str] = []
    for d in decls:
        if d.startswith("__SEL__"):
            sub_sel = d[len("__SEL__"):]
        else:
            out.append(d)
    if not out:
        return []

    sel = f'[class~="{cls}"]' + sub_sel
    media = ""
    for p in reversed(variants):
        r = variant_selector(p)
        if r is None:
            return None
        tmpl, med = r
        if tmpl == "&":
            pass
        elif "&" in tmpl:
            sel = tmpl.replace("&", sel)
        else:
            sel = f"{tmpl} {sel}"
        if med:
            media = med
    body = "\n".join(f"  {d};" for d in out)
    rule = f"{sel} {{\n{body}\n}}"
    if media:
        rule = f"{media} {{\n{rule}\n}}"
    return rule.split("\n")


# ══════════════════════════════════════════════════════════════════
# 类名提取
#
# 必须用真正的词法扫描，不能用 `"([^"]*)"` 这类正则：
# 源码里同时存在 " ' ` 三种引号 + 正则字面量 + SVG path 数据，
# 朴素正则会把引号跨类型配对，把 SVG 的 d="M12h14…" 当成类名。
# ══════════════════════════════════════════════════════════════════
VALID = re.compile(r"[A-Za-z0-9_:./\[\]%()+,'!=-]+")
DROP = {"true", "false", "null", "undefined", "string", "number", "div", "span", "button",
        "use client", "aria-hidden", "export", "default"}


def _scan_literals(src: str) -> list[tuple[int, int, str]]:
    """扫描 JS/TS 源码，返回 [(起始下标, 结束下标, 字面量内容)]。

    正确处理：三种引号、转义、模板字面量（含 ${} 嵌套）、行/块注释、正则字面量。
    """
    out: list[tuple[int, int, str]] = []
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        # 注释
        if ch == "/" and i + 1 < n and src[i + 1] == "/":
            j = src.find("\n", i)
            i = n if j < 0 else j + 1
            continue
        if ch == "/" and i + 1 < n and src[i + 1] == "*":
            j = src.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        if ch in "\"'`":
            delim, start, buf, j = ch, i, [], i + 1
            while j < n:
                c = src[j]
                if c == "\\":
                    j += 2
                    continue
                if c == delim:
                    break
                if c == "\n" and delim != "`":
                    break
                if c == "$" and delim == "`" and j + 1 < n and src[j + 1] == "{":
                    # 跳过 ${...}（内部可能再有字符串，递归交给主循环）
                    depth, k = 1, j + 2
                    while k < n and depth:
                        if src[k] == "{":
                            depth += 1
                        elif src[k] == "}":
                            depth -= 1
                        k += 1
                    j = k
                    continue
                buf.append(c)
                j += 1
            out.append((start, j, "".join(buf)))
            i = j + 1
            continue
        i += 1
    return out


def _balanced(src: str, start: int) -> tuple[str, int]:
    """从 '(' 之后取配对括号内文本，返回 (内容, 结束下标)。"""
    depth, i = 1, start
    while i < len(src) and depth:
        if src[i] in "([{":
            depth += 1
        elif src[i] in ")]}":
            depth -= 1
        i += 1
    return src[start:i - 1], i


def extract_classes(src: str) -> set[str]:
    lits = _scan_literals(src)
    found: set[str] = set()

    def take(*spans: tuple[int, int]) -> None:
        for s, e, text in lits:
            if any(a <= s < b for a, b in spans):
                for c in text.split():
                    # 类名里不可能出现这些；顺带滤掉代码片段
                    if VALID.fullmatch(c) and not c.startswith("--") and "(" not in c:
                        found.add(c)

    spans: list[tuple[int, int]] = []
    # className= 后的字面量
    for m in re.finditer(r"className\s*=\s*", src):
        i = m.end()
        if i < len(src) and src[i] == "{":
            body, end = _balanced(src, i + 1)
            spans.append((i, end))
        else:
            # 非花括号形式：只取紧邻的那个字面量，不能贪心吃掉后面的 JSX/SVG
            k = i
            while k < len(src) and src[k] in " \t\r\n":
                k += 1
            if k < len(src) and src[k] in "\"'`":
                for s, e, _t in lits:
                    if s == k:
                        spans.append((s, e))
                        break
    # cn / clsx / cva / twMerge 调用的实参
    for fn in ("cn", "clsx", "cva", "twMerge"):
        for m in re.finditer(rf"\b{fn}\s*\(", src):
            body, end = _balanced(src, m.end())
            spans.append((m.end(), end))

    take(*spans)
    return {c for c in found if c not in DROP and len(c) > 1 and not c.startswith("http")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill-dir", default=os.path.join(os.path.expanduser("~"), ".workbuddy", "skills", "beautifului"))
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    root = os.path.abspath(args.skill_dir)
    up = os.path.join(root, "assets", "upstream")

    files = sorted(glob.glob(os.path.join(up, "components", "primitives", "*.tsx")))
    files += sorted(glob.glob(os.path.join(up, "components", "atoms", "*.tsx")))

    allc: set[str] = set()
    for f in files:
        with open(f, encoding="utf-8") as fh:
            allc |= extract_classes(fh.read())

    unhandled = [c for c in sorted(allc) if build_rule(c) is None]
    handled = len(allc) - len(unhandled)
    print(f"files={len(files)} classes={len(allc)} handled={handled} unhandled={len(unhandled)}")
    if args.report:
        # 写系统临时目录，不要硬编码某个人的绝对路径
        out = os.path.join(tempfile.gettempdir(), "beautifului-unhandled.txt")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as fh:
            fh.write("\n".join(unhandled))
        print("报告写入: %s" % out)
        print("\n".join(f"  ? {c}" for c in unhandled))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
