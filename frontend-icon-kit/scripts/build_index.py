#!/usr/bin/env python3
"""拉取 Tabler 全量图标名，生成本地索引 references/tabler-index.json。

用途：
- 让「校验图标名是否存在」可以离线完成（无网络请求，毫秒级）
- 让「按分类浏览」在选择器里可用

用法：
    python scripts/build_index.py            # 增量刷新
    python scripts/build_index.py --force    # 强制刷新
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from iconify_api import INDEX_PATH, DEFAULT_PREFIX, api_get_json  # noqa: E402


def build(prefix: str = DEFAULT_PREFIX, force: bool = False) -> dict:
    if INDEX_PATH.exists() and not force:
        old = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        if old.get("icons"):
            print("索引已存在（%d 个图标），跳过。加 --force 强制刷新。" % len(old["icons"]))
            return old

    meta = api_get_json("/collection", {"prefix": prefix})
    names = list(meta.get("uncategorized") or [])
    hidden = meta.get("hidden") or []
    aliases = list(meta.get("aliases") or {})

    # 分类信息：Iconify 的 collection 接口对部分图标集给 categories
    categories = {k: v for k, v in (meta.get("categories") or {}).items()}

    index = {
        "prefix": prefix,
        "title": meta.get("title") or prefix,
        "total": meta.get("total") or len(names),
        "generated_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "icons": sorted(set(names) | set(hidden)),
        "aliases": sorted(set(aliases)),
        "categories": categories,
    }
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    print("索引已生成：%s" % INDEX_PATH)
    print("  图标集  : %s (v%s)" % (index["title"], meta.get("version") or "?"))
    print("  图标总数: %d" % len(index["icons"]))
    print("  别名    : %d" % len(index["aliases"]))
    print("  分类    : %d" % len(index["categories"]))
    return index


def main() -> int:
    ap = argparse.ArgumentParser(description="生成 Tabler 图标本地索引")
    ap.add_argument("--prefix", default=DEFAULT_PREFIX)
    ap.add_argument("--force", action="store_true", help="强制重新拉取")
    args = ap.parse_args()
    try:
        build(args.prefix, args.force)
    except Exception as exc:
        print("生成失败：%s" % exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
