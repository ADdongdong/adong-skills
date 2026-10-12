#!/usr/bin/env python3
"""
extract.py — 从 registry JSON 中抽出「只存在于 registry 里」的源码，并生成离线可用的 registry。

背景（重要，别踩坑）:
  上游仓库 `app/beautifui/*.css`（foundation.css / records-table.css / sidebar-nav.css）
  **不在 git 树里**，它们由上游的 build-registry 脚本生成，只内嵌在 public/r/*.json 的
  files[].content 中。所以这些文件必须从 registry JSON 反向落地。

另外:
  每个 registry 条目的 registryDependencies 指向
  `https://www.beautifului.dev/r/foundation.json` —— 该域名本机不可达。
  因此生成一份 registry-offline/，把绝对 URL 改写成相对文件名，
  让 `npx shadcn add ./assets/registry-offline/<slug>.json` 能离线解析依赖。

用法:
  python extract.py [--skill-dir <skill_dir>]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

# registryDependencies 里指向出题站点的绝对 URL
ABS_DEP = re.compile(r"https?://(?:www\.)?beautifului\.dev/r/([A-Za-z0-9._-]+)\.json")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--skill-dir",
        default=os.path.join(os.path.expanduser("~"), ".workbuddy", "skills", "beautifului"),
    )
    args = ap.parse_args()

    root = os.path.abspath(args.skill_dir)
    reg = os.path.join(root, "assets", "registry")
    off = os.path.join(root, "assets", "registry-offline")
    up = os.path.join(root, "assets", "upstream")
    os.makedirs(off, exist_ok=True)

    if not os.path.isdir(reg):
        print(f"[extract] FATAL: 找不到 {reg}", file=sys.stderr)
        return 1

    files = sorted(f for f in os.listdir(reg) if f.endswith(".json"))
    if not files:
        print(f"[extract] FATAL: {reg} 为空", file=sys.stderr)
        return 1

    idx_path = os.path.join(reg, "registry.json")
    slugs: list[str] = []
    if os.path.exists(idx_path):
        with open(idx_path, encoding="utf-8") as fh:
            slugs = [it["name"] for it in json.load(fh)["items"]]

    materialized: list[str] = []
    rewritten = 0
    tsx_seen: dict[str, int] = {}

    for fn in files:
        with open(os.path.join(reg, fn), encoding="utf-8") as fh:
            item = json.load(fh)

        # ---- 1. 把 files[].content 落地（只补 upstream 里没有的，避免覆盖权威 git 版本）
        for f in item.get("files", []):
            p, content = f.get("path", ""), f.get("content", "")
            if not p or not content:
                continue
            if p.endswith(".tsx"):
                tsx_seen[p] = len(content)
                continue  # tsx 以 git 树版本为准
            dest = os.path.join(up, p)
            if os.path.exists(dest):
                continue
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(content)
            materialized.append(p)

        # ---- 2. 生成离线 registry（依赖改相对路径）
        deps = item.get("registryDependencies") or []
        newdeps = []
        for d in deps:
            m = ABS_DEP.match(d)
            newdeps.append(f"./{m.group(1)}.json" if m else d)
        if newdeps != deps:
            rewritten += 1
        item["registryDependencies"] = newdeps
        with open(os.path.join(off, fn), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(item, fh, indent=2, ensure_ascii=False)
            fh.write("\n")

    # registry 索引也复制过去（shadcn 需要它枚举本地 registry）
    if os.path.exists(idx_path):
        with open(idx_path, encoding="utf-8") as fh:
            idx = json.load(fh)
        with open(os.path.join(off, "registry.json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(idx, fh, indent=2, ensure_ascii=False)
            fh.write("\n")

    # ---- 3. 校验：registry 声明的 tsx 是否都有 git 树版本
    missing_tsx = sorted(p for p in tsx_seen if not os.path.exists(os.path.join(up, p)))

    print(f"[extract] registry 条目: {len(files)}  (索引声明 {len(slugs)})")
    print(f"[extract] 从 registry 落地的新文件: {len(materialized)}")
    for p in materialized:
        print(f"    + {p}")
    print(f"[extract] 依赖改写为相对路径的条目: {rewritten}")
    print(f"[extract] 离线 registry 输出: {off}")
    if missing_tsx:
        print(f"[extract] !! 缺 git 树版本的 tsx ({len(missing_tsx)}):")
        for p in missing_tsx:
            print(f"    ! {p}")
    else:
        print("[extract] tsx 齐全：registry 声明的组件源码均在 upstream/ 中")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
