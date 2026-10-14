#!/usr/bin/env python3
"""frontend-icon-kit 公共库：Iconify API 访问 + 本地图标索引。

职责：给 skill 内其它脚本提供统一的图标搜索、校验、SVG 获取能力。

踩过的坑（已固化处理）：
1. Iconify API 请求不带 User-Agent 会直接 403 Forbidden，必须带。
2. 本机若存在 .curlrc / 系统级代理残留（如未启动的 127.0.0.1:7890），
   请求会被劫持到死端口而静默返回空。这里在 Python 侧显式禁用代理直连；
   确需代理时用环境变量 ICONKIT_PROXY 显式指定。
3. 仅用标准库，不引入任何第三方依赖，保证在任何 Python 3.9+ 环境可跑。
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

API_BASE = "https://api.iconify.design"
USER_AGENT = "frontend-icon-kit/1.0 (+workbuddy-skill)"
DEFAULT_PREFIX = "tabler"
TIMEOUT = 25
RETRIES = 3

SKILL_DIR = Path(__file__).resolve().parent.parent
INDEX_PATH = SKILL_DIR / "references" / "tabler-index.json"

__all__ = [
    "API_BASE",
    "DEFAULT_PREFIX",
    "SKILL_DIR",
    "INDEX_PATH",
    "api_get_json",
    "search_icons",
    "check_icons",
    "fetch_icon_data",
    "load_index",
    "local_names",
    "normalize_name",
    "split_name",
]


class IconKitError(RuntimeError):
    """网络或数据异常，供 CLI 层转成友好提示。"""


# --------------------------------------------------------------------------- #
# HTTP 层
# --------------------------------------------------------------------------- #
def _build_opener() -> urllib.request.OpenerDirector:
    proxy = os.environ.get("ICONKIT_PROXY", "").strip()
    if proxy:
        handler = urllib.request.ProxyHandler({"http": proxy, "https": proxy})
    else:
        # 空 dict = 显式禁用一切代理，直接连网
        handler = urllib.request.ProxyHandler({})
    return urllib.request.build_opener(handler)


def api_get_json(path: str, params: Optional[Dict[str, object]] = None) -> dict:
    """请求 Iconify API 并解析 JSON，失败自动重试 3 次。"""
    url = API_BASE + path
    if params:
        clean = {k: v for k, v in params.items() if v is not None}
        url = url + "?" + urllib.parse.urlencode(clean)

    last_err: Optional[Exception] = None
    for attempt in range(1, RETRIES + 1):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        try:
            opener = _build_opener()
            with opener.open(req, timeout=TIMEOUT) as resp:
                raw = resp.read().decode("utf-8")
            return json.loads(raw)
        except urllib.error.HTTPError as exc:  # 4xx/5xx
            last_err = exc
            if exc.code in (400, 404):
                break  # 请求本身有问题，重试无意义
        except Exception as exc:  # 网络层
            last_err = exc
        if attempt < RETRIES:
            import time

            time.sleep(0.8 * attempt)

    raise IconKitError(
        "无法访问 Iconify API（%s）：%s\n"
        "排查建议：1) 确认本机能访问 api.iconify.design；"
        "2) 若必须走代理，设置环境变量 ICONKIT_PROXY=http://host:port；"
        "3) 也可用 --offline 走本地索引。" % (url, last_err)
    )


# --------------------------------------------------------------------------- #
# 名称工具
# --------------------------------------------------------------------------- #
def normalize_name(name: str, prefix: str = DEFAULT_PREFIX) -> str:
    """把 'building-bank' / 'tabler:building-bank' 统一成 'tabler:building-bank'。"""
    name = name.strip()
    if not name:
        return name
    return name if ":" in name else "%s:%s" % (prefix, name)


def split_name(full_name: str) -> Tuple[str, str]:
    """拆成 (prefix, name)。"""
    if ":" in full_name:
        prefix, _, raw = full_name.partition(":")
        return prefix, raw
    return DEFAULT_PREFIX, full_name


# --------------------------------------------------------------------------- #
# 搜索
# --------------------------------------------------------------------------- #
def search_icons(query: str, prefix: str = DEFAULT_PREFIX, limit: int = 32) -> List[str]:
    """关键词搜索图标，返回 ['tabler:building-bank', ...]。

    Iconify 的检索基于图标名与别名（英文），中文关键词请先用语义映射表转换。
    """
    data = api_get_json("/search", {"query": query, "prefix": prefix, "limit": limit})
    return list(data.get("icons") or [])


# --------------------------------------------------------------------------- #
# 校验（防止 AI 编造不存在的图标名）
# --------------------------------------------------------------------------- #
def local_names() -> Set[str]:
    """读取本地索引里的全部图标名（不带 prefix），用于离线校验。"""
    idx = load_index()
    if not idx:
        return set()
    names: Set[str] = set(idx.get("icons") or [])
    names.update(idx.get("aliases") or [])
    return names


def check_icons(full_names: Sequence[str], offline: bool = False) -> Tuple[List[str], List[str]]:
    """批量校验图标名是否存在，返回 (存在的, 不存在的)。

    优先用本地索引（离线、快、无网络请求）；索引缺失或 offline=False 时可回退 API 复核。
    """
    normalized = [normalize_name(n) for n in full_names if n and n.strip()]
    if not normalized:
        return [], []

    known = local_names()
    if known:
        found = [n for n in normalized if split_name(n)[1] in known]
        missing = [n for n in normalized if split_name(n)[1] not in known]
        if not offline:
            # 本地索引可能落后于 Iconify 线上版本，对未命中的再走一次 API 复核，
            # 避免把「新增图标」误判为不存在。
            if missing:
                by_prefix: Dict[str, List[str]] = {}
                for n in missing:
                    p, raw = split_name(n)
                    by_prefix.setdefault(p, []).append(raw)
                still_missing: List[str] = []
                api_found: List[str] = []
                for p, raws in by_prefix.items():
                    data = api_get_json("/%s.json" % p, {"icons": ",".join(raws)})
                    icons = data.get("icons") or {}
                    aliases = data.get("aliases") or {}
                    hit = set(icons) | set(aliases)
                    for raw in raws:
                        if raw in hit:
                            api_found.append("%s:%s" % (p, raw))
                        else:
                            still_missing.append("%s:%s" % (p, raw))
                return found + api_found, still_missing
        return found, missing

    if offline:
        raise IconKitError("本地索引不存在，无法离线校验。先执行：python scripts/build_index.py")

    # 没有本地索引，直接走 API
    found: List[str] = []
    missing: List[str] = []
    by_prefix: Dict[str, List[str]] = {}
    for n in normalized:
        p, raw = split_name(n)
        by_prefix.setdefault(p, []).append(raw)
    for p, raws in by_prefix.items():
        data = api_get_json("/%s.json" % p, {"icons": ",".join(raws)})
        hit = set(data.get("icons") or {}) | set(data.get("aliases") or {})
        for raw in raws:
            target = "%s:%s" % (p, raw)
            (found if raw in hit else missing).append(target)
    return found, missing


# --------------------------------------------------------------------------- #
# 取图标数据（用于生成内联 SVG）
# --------------------------------------------------------------------------- #
def fetch_icon_data(full_name: str) -> Optional[dict]:
    """取单个图标的原始数据，返回 {'prefix','name','body','width','height'}。"""
    prefix, raw = split_name(full_name)
    data = api_get_json("/%s.json" % prefix, {"icons": raw})
    icons = data.get("icons") or {}
    entry = icons.get(raw)
    if not entry:
        aliases = data.get("aliases") or {}
        if raw in aliases:
            target = aliases[raw]
            entry = icons.get(target.get("parent") if isinstance(target, dict) else str(target))
        if not entry:
            return None
    return {
        "prefix": prefix,
        "name": raw,
        "body": entry.get("body", ""),
        "width": entry.get("width") or data.get("width") or 24,
        "height": entry.get("height") or data.get("height") or 24,
    }


# --------------------------------------------------------------------------- #
# 本地索引
# --------------------------------------------------------------------------- #
def load_index() -> dict:
    if not INDEX_PATH.exists():
        return {}
    try:
        return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


if __name__ == "__main__":
    found, missing = check_icons(["tabler:building-bank", "tabler:user", "tabler:definitely-not-real-xyz"])
    print("found  :", found)
    print("missing:", missing)
