#!/usr/bin/env python3
"""按中文业务场景词 / 英文关键词搜索图标。

三级检索策略，逐级兜底：
  1. 语义映射表命中   —— 中文业务词直接给业务专家级候选（最准）
  2. 本地名字子串匹配 —— 零网络，扫全量 6286 个名字，比在线搜索更全
  3. Iconify 在线搜索 —— 兜底补充

用法：
    python scripts/icon_search.py "银行"
    python scripts/icon_search.py "审批通过" --limit 16
    python scripts/icon_search.py "bank" --json
    python scripts/icon_search.py "函证 回函" --offline

输出 JSON 时结构固定，便于上层程序消费：
    {"query": "...", "matched_terms": [...], "results": [{"name": "tabler:x", "source": "semantic|local|api"}]}
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

from iconify_api import (  # noqa: E402
    DEFAULT_PREFIX, IconKitError, check_icons, load_index, search_icons,
)

SEMANTIC_PATH = Path(__file__).resolve().parent.parent / "references" / "semantic-map.json"


# --------------------------------------------------------------------------- #
# 策略 1：语义映射表
# --------------------------------------------------------------------------- #
def load_semantic() -> List[dict]:
    if not SEMANTIC_PATH.exists():
        return []
    return json.loads(SEMANTIC_PATH.read_text(encoding="utf-8")).get("groups") or []


def match_semantic(query: str) -> Tuple[List[str], List[str], List[str]]:
    """返回 (命中的中文词, 候选图标名, 命中分组标题)。"""
    hits: List[str] = []
    icons: List[str] = []
    groups: List[str] = []
    for group in load_semantic():
        for item in group.get("items") or []:
            hit = [w for w in (item.get("zh") or []) if w and (w in query or query in w)]
            if hit:
                hits.extend(hit)
                icons.extend(item.get("icons") or [])
                if group.get("title") not in groups:
                    groups.append(group.get("title"))
    return list(dict.fromkeys(hits)), list(dict.fromkeys(icons)), groups


# --------------------------------------------------------------------------- #
# 策略 2：本地名字子串匹配
# --------------------------------------------------------------------------- #
def local_name_search(term: str, limit: int = 40) -> List[str]:
    names = load_index().get("icons") or []
    t = term.lower().strip()
    if not t or not names:
        return []
    exact = [n for n in names if n == t]
    starts = sorted([n for n in names if n.startswith(t) and n != t], key=lambda n: (len(n), n))
    contains = sorted([n for n in names if t in n and n not in exact and n not in starts],
                      key=lambda n: (len(n), n))
    ordered = exact + starts + contains
    return ["%s:%s" % (DEFAULT_PREFIX, n) for n in ordered[:limit]]


def extract_ascii_words(query: str) -> List[str]:
    return [w for w in re.split(r"[\s/、,，+]+", query) if w and w.isascii()]


# --------------------------------------------------------------------------- #
# 策略 3：在线搜索
# --------------------------------------------------------------------------- #
def online_search(term: str, limit: int) -> List[str]:
    try:
        return search_icons(term, prefix=DEFAULT_PREFIX, limit=limit)
    except IconKitError:
        return []


def main() -> int:
    ap = argparse.ArgumentParser(description="搜索图标（中文业务词优先走向语义映射表）")
    ap.add_argument("query", help="中文业务场景词或英文关键词")
    ap.add_argument("--limit", type=int, default=24, help="每级检索返回上限，默认 24")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--offline", action="store_true", help="完全离线，不访问网络")
    args = ap.parse_args()

    query = args.query.strip()
    hits, semantic_icons, groups = match_semantic(query)

    # 本地名字匹配：中文词不会命中（名字是英文），英文词/片段会命中
    local_hits: List[str] = []
    ascii_words = extract_ascii_words(query)
    for word in ascii_words:
        local_hits.extend(local_name_search(word, args.limit))
    # 中文查询未命中语义表时，尝试把整串塞进本地匹配（基本无收获，但零成本）
    if not ascii_words and not semantic_icons:
        local_hits.extend(local_name_search(query, args.limit))

    api_hits: List[str] = []
    if not args.offline and ascii_words:
        api_hits = online_search(" ".join(ascii_words), args.limit)

    # 按优先级合并去重
    ordered: List[str] = []
    seen: set = set()
    sources: Dict[str, str] = {}
    for bucket, tag in ((semantic_icons, "semantic"), (local_hits, "local"), (api_hits, "api")):
        for name in bucket:
            full = name if ":" in name else "%s:%s" % (DEFAULT_PREFIX, name)
            if full not in seen:
                seen.add(full)
                ordered.append(full)
                sources[full] = tag

    if not ordered:
        msg = ("没有匹配到图标。\n"
               "建议：1) 换更具体的业务词（如「函证」「受托管理」「额度」）；"
               "2) 若在离线模式，加 --offline 之外请去掉它；"
               "3) 也支持英文关键词（如 file-check、chart-bar）。")
        if args.json:
            print(json.dumps({"query": query, "matched_terms": [], "results": [],
                              "message": msg}, ensure_ascii=False, indent=2))
        else:
            print(msg)
        return 0

    try:
        found, missing = check_icons(ordered, offline=args.offline)
    except IconKitError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    results = [{"name": n, "source": sources.get(n, "api")} for n in found]

    if args.json:
        print(json.dumps({"query": query, "matched_terms": hits, "groups": groups,
                          "results": results, "missing": missing, "count": len(results)},
                         ensure_ascii=False, indent=2))
        return 0

    if hits:
        print("命中业务词：%s" % "、".join(hits))
    if groups:
        print("所属模块：%s" % " / ".join(groups))
    print("共 %d 个可用图标：\n" % len(results))
    labels = {"semantic": "[业务]", "local": "[名称]", "api": "[检索]"}
    width = max((len(r["name"]) for r in results), default=10) + 2
    for r in results:
        print("  %s %-*s %s" % (labels.get(r["source"], "[?]"), width, r["name"],
                                "https://api.iconify.design/%s.svg" % r["name"].replace(":", "/")))
    if missing:
        print("\n以下名称不存在，已剔除：%s" % ", ".join(missing))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
