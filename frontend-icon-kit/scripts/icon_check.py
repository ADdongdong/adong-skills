#!/usr/bin/env python3
"""校验图标名是否真实存在 —— 这是本 skill 的防错闸门。

规则：任何写进交付代码的图标名，都必须先过这里。
本地索引命中即离线通过；未命中会回查 Iconify 线上接口复核（避免索引滞后误杀新增图标）。

用法：
    python scripts/icon_check.py tabler:building-bank tabler:user
    python scripts/icon_check.py building-bank user            # 省略 prefix 默认 tabler
    python scripts/icon_check.py --file names.txt
    echo "tabler:user" | python scripts/icon_check.py --stdin
    python scripts/icon_check.py tabler:xxx --offline --json

退出码：全部存在 = 0；存在无效名 = 1；网络/索引异常 = 2。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parent))

from iconify_api import IconKitError, check_icons  # noqa: E402


def collect(args) -> List[str]:
    names: List[str] = list(args.names or [])
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
        names.extend([line.strip() for line in text.splitlines()])
    if args.stdin:
        names.extend([line.strip() for line in sys.stdin.read().splitlines()])
    # 去空、去重保序
    cleaned = [n for n in (x.strip() for x in names) if n and not n.startswith("#")]
    return list(dict.fromkeys(cleaned))


def main() -> int:
    ap = argparse.ArgumentParser(description="校验图标名是否存在")
    ap.add_argument("names", nargs="*", help="图标名，如 tabler:building-bank 或 building-bank")
    ap.add_argument("--file", help="从文件读取，每行一个")
    ap.add_argument("--stdin", action="store_true", help="从标准输入读取")
    ap.add_argument("--offline", action="store_true", help="只用本地索引，不联网复核")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    names = collect(args)
    if not names:
        print("没有提供任何图标名。", file=sys.stderr)
        return 2

    try:
        found, missing = check_icons(names, offline=args.offline)
    except IconKitError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({"valid": found, "invalid": missing,
                          "ok": not missing, "checked": len(names)},
                         ensure_ascii=False, indent=2))
    else:
        print("校验 %d 个图标名：" % len(names))
        for n in found:
            print("  ✅ %s" % n)
        for n in missing:
            print("  ❌ %s   ← 不存在，禁止写入代码" % n)
        if missing:
            print("\n结论：有 %d 个无效名称。请改用搜索脚本重新选图标："
                  "\n  python scripts/icon_search.py \"业务场景词\"" % len(missing))
        else:
            print("\n结论：全部有效 ✅")

    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
