#!/usr/bin/env python3
"""把语义映射表 + 全量图标名注入 HTML 模板，生成自包含的可视化图标选择器。

产物：assets/icon-picker.html —— 双击即可在浏览器打开，无需服务器。

用法：
    python scripts/build_picker.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
TEMPLATE = BASE / "scripts" / "picker-template.html"
SEMANTIC = BASE / "references" / "semantic-map.json"
INDEX = BASE / "references" / "tabler-index.json"
OUTPUT = BASE / "assets" / "icon-picker.html"


def main() -> int:
    if not TEMPLATE.exists():
        print("找不到模板：%s" % TEMPLATE, file=sys.stderr)
        return 1

    semantic = json.loads(SEMANTIC.read_text(encoding="utf-8"))
    index = json.loads(INDEX.read_text(encoding="utf-8")) if INDEX.exists() else {}
    raw_icons = index.get("icons") or []

    html = TEMPLATE.read_text(encoding="utf-8")
    html = html.replace("/*__ICON_DATA__*/", json.dumps(semantic, ensure_ascii=False))
    html = html.replace("/*__TOTAL_ICONS__*/", str(len(raw_icons)))

    # 全量名字单独注入（体积大，放独立变量减少模板噪音）
    raw_json = json.dumps(raw_icons, ensure_ascii=False)
    html = html.replace(
        "<script>\nconst DATA =",
        "<script>\nwindow.__RAW_ICONS__ = %s;\nconst DATA =" % raw_json,
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(html, encoding="utf-8")
    print("已生成：%s" % OUTPUT)
    print("  业务分组: %d 个" % len(semantic.get("groups") or []))
    print("  精选图标: %d 个" % sum(len(it["icons"]) for g in semantic["groups"] for it in g["items"]))
    print("  全量图标: %d 个" % len(raw_icons))
    print("  文件大小: %.1f KB" % (OUTPUT.stat().st_size / 1024))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
