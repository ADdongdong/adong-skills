#!/usr/bin/env python3
"""
vendor.py — 拉取上游 Beautiful UI 源码到 skill 的 assets/ 目录。

为什么不用 git clone:
  本机 github.com 连接不稳定（Recv failure / Connection reset），
  api.github.com 完全不可达。cdn.jsdelivr.net 实测稳定，且支持 @<sha> 锁定版本。

用法:
  python vendor.py [--ref main] [--dest <skill_dir>]

产物:
  <dest>/assets/upstream/**        保真基准源码（tsx / css / lib）
  <dest>/assets/registry/*.json    public/r/*.json 原样（27 项 + registry.json）
  <dest>/assets/upstream/PROVENANCE.json
  <dest>/assets/upstream/LICENSE
"""
from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request

REPO = "slev12397/beautiful-ui"
JSD_BASE = "https://cdn.jsdelivr.net/gh"
DATA_API = "https://data.jsdelivr.com/v1/packages/gh"

# 不依赖沙箱代理：本机 127.0.0.1:13715 已失效
_NO_PROXY = urllib.request.ProxyHandler({})

_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE


def _opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(_NO_PROXY, urllib.request.HTTPSHandler(context=_CTX))


def fetch(path: str, ref: str, tries: int = 6, timeout: int = 45) -> bytes | None:
    """从 jsdelivr 拉单个文件，带指数退避重试。"""
    url = f"{JSD_BASE}/{REPO}@{ref}/{path.lstrip('/')}"
    op = _opener()
    last: Exception | None = None
    for i in range(tries):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0", "Accept": "*/*"}
            )
            with op.open(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None  # 真正的缺失，不重试
            last = e
        except Exception as e:  # noqa: BLE001
            last = e
        time.sleep(min(1.5 * (2**i), 20))
    print(f"  !! FAIL {path}: {last}", file=sys.stderr)
    return None


def list_tree(ref: str) -> list[str]:
    """用 jsdelivr data API 枚举仓库文件；失败则抛错由调用方兜底。"""
    url = f"{DATA_API}/{REPO}@{ref}?structure=flat"
    op = _opener()
    for i in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with op.open(req, timeout=45) as r:
                data = json.loads(r.read().decode("utf-8"))
            return [f["name"].lstrip("/") for f in data.get("files", [])]
        except Exception as e:  # noqa: BLE001
            if i == 3:
                raise
            time.sleep(2 * (i + 1))
    return []


def write(dest_root: str, rel: str, data: bytes) -> None:
    out = os.path.join(dest_root, rel)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "wb") as fh:
        fh.write(data)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="main", help="git ref / commit sha")
    ap.add_argument(
        "--dest",
        default=os.path.join(os.path.expanduser("~"), ".workbuddy", "skills", "beautifului"),
    )
    args = ap.parse_args()

    dest = os.path.abspath(args.dest)
    up = os.path.join(dest, "assets", "upstream")
    reg = os.path.join(dest, "assets", "registry")
    os.makedirs(up, exist_ok=True)
    os.makedirs(reg, exist_ok=True)

    print(f"[vendor] repo={REPO} ref={args.ref}")
    print(f"[vendor] dest={dest}")

    # ---- 1. 枚举仓库文件（用于发现 tsx / css / lib） ----
    tree: list[str] = []
    try:
        tree = list_tree(args.ref)
        print(f"[vendor] tree: {len(tree)} files  (via jsdelivr data API)")
    except Exception as e:  # noqa: BLE001
        print(f"[vendor] !! data API 不可用（{e}）；改用 registry 驱动 + 已知路径清单")

    # ---- 2. registry 索引 ----
    idx_raw = fetch("public/r/registry.json", args.ref)
    if not idx_raw:
        print("[vendor] FATAL: 拿不到 public/r/registry.json", file=sys.stderr)
        return 1
    write(reg, "registry.json", idx_raw)
    index = json.loads(idx_raw.decode("utf-8"))
    slugs = [it["name"] for it in index["items"]]
    print(f"[vendor] registry items: {len(slugs)}")

    # ---- 3. 逐个拉 registry 条目 ----
    ok, miss = 0, []
    for s in slugs:
        d = fetch(f"public/r/{s}.json", args.ref)
        if d is None:
            miss.append(s)
            continue
        write(reg, f"{s}.json", d)
        ok += 1
    print(f"[vendor] registry files: {ok}/{len(slugs)} ok" + (f"  missing={miss}" if miss else ""))

    # ---- 4. 拉源码：优先按 tree 过滤，否则用已知路径清单 ----
    want: list[str] = []
    if tree:
        for p in tree:
            if p.startswith(("components/primitives/", "components/atoms/")) and p.endswith(".tsx"):
                want.append(p)
            elif p.startswith("app/beautifui/") and p.endswith(".css"):
                want.append(p)
            elif p in ("app/globals.css", "lib/utils.ts", "lib/meta.ts", "LICENSE"):
                want.append(p)
    if not want:
        # 兜底：由 registry 条目的 files[].path 反推（这覆盖了 registry 里的全部源码）
        seen: set[str] = set()
        for s in slugs:
            fp = os.path.join(reg, f"{s}.json")
            if not os.path.exists(fp):
                continue
            with open(fp, encoding="utf-8") as fh:
                item = json.load(fh)
            for f in item.get("files", []):
                p = f.get("path", "")
                if p and p not in seen:
                    seen.add(p)
                    want.append(p)
        want += ["lib/utils.ts", "lib/meta.ts", "LICENSE", "app/globals.css"]

    # AgentScreen 不在 registry，必须显式补
    for extra in (
        "components/primitives/AgentScreen.tsx",
        "components/atoms/Button.tsx",
        "components/atoms/EntityChip.tsx",
        "components/atoms/ValuePill.tsx",
        "components/atoms/Shimmer.tsx",
        "components/atoms/StreamText.tsx",
        "components/primitives/GlideMenu.tsx",
    ):
        if extra not in want:
            want.append(extra)

    got, lost = [], []
    for p in want:
        d = fetch(p, args.ref)
        if d is None:
            lost.append(p)
            continue
        write(up, p, d)
        got.append(p)
    print(f"[vendor] source files: {len(got)} ok, {len(lost)} missing")
    for p in lost:
        print(f"    missing: {p}")

    # ---- 5. PROVENANCE ----
    sha = args.ref
    if args.ref == "main" and tree:
        # jsdelivr 的 flat API 不带 sha；留 main 并标注解析时间
        sha = "main(unpinned)"
    prov = {
        "repo": f"https://github.com/{REPO}",
        "ref": args.ref,
        "resolved": sha,
        "mirror": f"{JSD_BASE}/{REPO}@{args.ref}",
        "license": "MIT",
        "copyright": "Shane Levine (Turbo) — https://turbodesign.co",
        "homepage": "https://www.beautifului.dev",
        "registry_items": len(slugs),
        "source_files": len(got),
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    write(up, "PROVENANCE.json", json.dumps(prov, indent=2, ensure_ascii=False).encode("utf-8"))
    print("[vendor] PROVENANCE.json written")
    print(f"[vendor] done -> {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
