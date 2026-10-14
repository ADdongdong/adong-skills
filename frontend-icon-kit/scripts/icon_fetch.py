#!/usr/bin/env python3
"""取图标 → 输出可直接粘贴进前端代码的片段。

两种模式（对应交付形态）：
  cdn    输出 <iconify-icon> web component，一行 CDN 引入，代码最干净（原型阶段首选）
  inline 输出内联 <svg>，离线单文件可跑、可直接改色改尺寸（交付阶段首选）

用法：
    python scripts/icon_fetch.py tabler:building-bank
    python scripts/icon_fetch.py tabler:building-bank --mode inline
    python scripts/icon_fetch.py tabler:building-bank tabler:user --mode inline --size 20
    python scripts/icon_fetch.py --file names.txt --mode inline --out icons.html
    python scripts/icon_fetch.py tabler:building-bank --json

输出可直接重定向保存：
    python scripts/icon_fetch.py --file names.txt --mode inline > icons.snippet.html
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parent))

from iconify_api import IconKitError, check_icons, fetch_icon_data, normalize_name  # noqa: E402

CDN_SNIPPET = (
    '<!-- 只需在页面引入一次（放在 </body> 前） -->\n'
    '<script src="https://code.iconify.design/iconify-icon/2.1.0/iconify-icon.min.js"></script>'
)

CDN_USAGE = (
    '<iconify-icon icon="{name}" width="{size}" height="{size}"{extra}></iconify-icon>'
)

INLINE_TMPL = (
    '<svg class="{cls}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}"'
    '{size_attrs}{extra} fill="none">{body}</svg>'
)


def build_cdn(name: str, size: int, label: str | None) -> str:
    extra = ' aria-label="%s" role="img"' % label if label else ""
    return CDN_USAGE.format(name=name, size=size, extra=extra)


def build_inline(name: str, size: int, cls: str, label: str | None, size_attrs: bool) -> str:
    data = fetch_icon_data(name)
    if not data:
        raise IconKitError("取不到图标数据：%s" % name)
    attrs = ' width="%d" height="%d"' % (size, size) if size_attrs else ""
    extra = ' role="img" aria-label="%s"' % label if label else ' aria-hidden="true"'
    return INLINE_TMPL.format(cls=cls, w=data["width"], h=data["height"],
                              size_attrs=attrs, extra=extra, body=data["body"])


def collect(args) -> List[str]:
    names: List[str] = [normalize_name(n) for n in (args.names or [])]
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
        names.extend([normalize_name(l) for l in text.splitlines() if l.strip() and not l.strip().startswith("#")])
    return list(dict.fromkeys(n for n in names if n))


def main() -> int:
    ap = argparse.ArgumentParser(description="生成图标代码片段（CDN / 内联 SVG）")
    ap.add_argument("names", nargs="*", help="图标名，如 tabler:building-bank")
    ap.add_argument("--file", help="从文件读取图标名，每行一个")
    ap.add_argument("--mode", choices=["cdn", "inline"], default="cdn")
    ap.add_argument("--size", type=int, default=24, help="尺寸 px，默认 24")
    ap.add_argument("--cls", default="ti", help="内联 SVG 的 class，默认 ti（建议用 CSS 控制尺寸颜色）")
    ap.add_argument("--label", help="无障碍标签，会写成 aria-label（不传则 aria-hidden）")
    ap.add_argument("--no-size-attrs", action="store_true",
                    help="内联模式不写 width/height 属性，完全交给 CSS（推荐用于设计系统）")
    ap.add_argument("--no-cdn-snippet", action="store_true", help="不额外输出 CDN 引入说明")
    ap.add_argument("--out", help="写入文件而不是打印到终端")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    names = collect(args)
    if not names:
        print("没有提供任何图标名。", file=sys.stderr)
        return 2

    # 硬闸门：无效名一律拒绝生成
    try:
        found, missing = check_icons(names)
    except IconKitError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if missing:
        print("以下图标名不存在，已拒绝生成（请先用 icon_search.py 重新选）：", file=sys.stderr)
        for m in missing:
            print("  ❌ %s" % m, file=sys.stderr)
        return 1

    try:
        if args.mode == "cdn":
            body_lines = [build_cdn(n, args.size, args.label) for n in found]
        else:
            body_lines = [build_inline(n, args.size, args.cls, args.label, not args.no_size_attrs) for n in found]
    except IconKitError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.json:
        payload = {"mode": args.mode, "size": args.size,
                   "icons": [{"name": n, "snippet": s} for n, s in zip(found, body_lines)]}
        text = json.dumps(payload, ensure_ascii=False, indent=2)
    else:
        parts: List[str] = []
        if args.mode == "cdn" and not args.no_cdn_snippet:
            parts.append(CDN_SNIPPET + "\n")
        parts.append("\n".join(body_lines))
        text = "\n".join(parts) + "\n"

    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print("已写入 %s（%d 个图标）" % (args.out, len(found)), file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
