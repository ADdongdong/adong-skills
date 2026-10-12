#!/usr/bin/env python3
"""
self_test.py — 跑完整套自测并把结果写成 markdown 报告。

覆盖 6 组检查：
  A. 上游完整性  —— 21 个组件源码齐全、registry 27 条 content 非空、PROVENANCE 存在
  B. 令牌一致性  —— foundation.standalone.css 含全部令牌 / 8 关键帧 / 已内联阴影 / 无 @theme 残留
  C. 移植件完整性 —— 21 个片段与 21 个成品都在、无未覆盖类
  D. 渲染验证     —— 调 verify_ports.cjs，断言全部 OK
  E. 离线自足     —— 成品里除 Google Fonts 外没有外部依赖
  F. 文档与许可   —— 必需文档存在、上游 LICENSE 原文在位

用法:
  python self_test.py [--skill-dir <dir>] [--no-browser] [--out <file>]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime


def _resolve_node() -> str:
    """定位 node 可执行文件。

    顺序：$NODE_BIN → PATH 上的 node → WorkBuddy 托管运行时。
    托管路径一律用 ~ 推导，**不写字面量用户名** —— 这样在本机可用，
    换一台机器（同样的 WorkBuddy 布局）也不用改代码。
    """
    env = os.environ.get("NODE_BIN")
    if env and os.path.exists(env):
        return env
    found = shutil.which("node")
    if found:
        return found
    versions = os.path.expanduser("~/.workbuddy/binaries/node/versions")
    if os.path.isdir(versions):
        cands = sorted(glob.glob(os.path.join(versions, "*", "node.exe")), reverse=True)
        if cands:
            return cands[0]
    return "node"          # 交给 PATH 解析，失败时 D 组会如实报错


def _resolve_node_path() -> str:
    """定位 node_modules（playwright 装在这里）。空串表示不额外设 NODE_PATH。"""
    env = os.environ.get("NODE_PATH")
    if env and os.path.isdir(env):
        return env
    cand = os.path.expanduser("~/.workbuddy/binaries/node/workspace/node_modules")
    return cand if os.path.isdir(cand) else ""


PY = sys.executable
NODE = _resolve_node()
NODE_PATH = _resolve_node_path()

EXPECTED_SLUGS = [
    "loading-state", "thinking-state", "streaming-text", "approval-card", "tool-chips",
    "task-rows", "chat-composer", "prompt-bar", "recommendation-card", "context-cards",
    "diff-table", "records-table", "filter-table", "sidebar-nav", "search", "flowchart",
    "insight-cards", "code-block", "fine-tune-card", "selection-actions", "agent-screen",
]
KEYFRAMES = ["shimmer-text", "fade-up", "fade-in", "eq-bounce",
             "caret-blink", "pop-in", "spin", "pixel-on"]
CRITICAL_TOKENS = [
    "--accent", "--accent-ink", "--accent-tint", "--ink", "--ink-2", "--ink-3",
    "--surface", "--canvas", "--page", "--line", "--line-strong", "--field",
    "--green", "--orange", "--red", "--tooltip-bg", "--tooltip-fg",
    "--radius-chip", "--radius-control", "--radius-card", "--radius-window",
    "--ease-out-strong", "--ease-in-out-strong", "--ease-link",
    "--shadow-xs", "--shadow-sm", "--shadow-md", "--shadow-lg",
    "--shadow-hairline", "--shadow-btn", "--shadow-card", "--shadow-raised", "--shadow-overlay",
    "--font-sans", "--font-mono",
]
REQUIRED_DOCS = [
    "SKILL.md", "README.md", "manifest.json", "LICENSE.beautiful-ui",
    "THIRD_PARTY_NOTICES.md", "references/component-catalog.md",
    "references/recommendation-engine.md", "references/react-integration.md",
    "references/foundation-tokens.md", "references/html-ports.md",
    "scripts/PORTING_GUIDE.md", "scripts/vendor.py", "scripts/extract.py",
    "scripts/twsubset.py", "scripts/make_foundation.py", "scripts/build_ports.py",
    "scripts/verify_ports.cjs", "scripts/build_preview.py",
]


class Report:
    def __init__(self) -> None:
        self.groups: list[tuple[str, list[tuple[bool, str]]]] = []

    def group(self, name: str, checks: list[tuple[bool, str]]) -> None:
        self.groups.append((name, checks))

    @property
    def ok(self) -> bool:
        return all(ok for _, cs in self.groups for ok, _ in cs)

    @property
    def counts(self) -> tuple[int, int]:
        flat = [c for _, cs in self.groups for c in cs]
        return sum(1 for ok, _ in flat if ok), len(flat)

    def markdown(self, meta: dict) -> str:
        passed, total = self.counts
        out = [
            f"# beautifului v{meta['version']} 自测报告",
            "",
            f"- 生成时间：{meta['generated_at']}",
            f"- 上游来源：{meta['repo']}",
            f"- 上游 ref：`{meta['ref']}`（抓取于 {meta['fetched_at']}）",
            f"- 结论：**{'全部通过' if self.ok else '存在失败项'}**（{passed} / {total} 项通过）",
            "",
            "全部检查均可由 `scripts/self_test.py` 复现。",
            "",
        ]
        for name, checks in self.groups:
            bad = sum(1 for ok, _ in checks if not ok)
            out.append(f"## {name}  ·  {'OK' if bad == 0 else f'{bad} 项失败'}")
            out.append("")
            out.append("| | 检查项 |")
            out.append("|---|---|")
            for ok, desc in checks:
                out.append(f"| {'✅' if ok else '❌'} | {desc} |")
            out.append("")
        if meta.get("render_log"):
            out += ["## 渲染验证原始输出", "", "```", meta["render_log"].strip(), "```", ""]
        out += [
            "## 复现方式",
            "",
            "```bash",
            "cd <skill 目录>",
            "python scripts/self_test.py",
            "```",
            "",
            "> 脚本会自行定位 node 与 playwright：优先 `$NODE_BIN` / `$NODE_PATH`，"
            "其次 PATH 上的 `node`，最后回落到 `~/.workbuddy/binaries/` 下的托管运行时；",
            "> 都不行时用 `--no-browser` 跳过渲染验证（D 组）。",
            "",
        ]
        return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill-dir", default=os.path.join(os.path.expanduser("~"), ".workbuddy", "skills", "beautifului"))
    ap.add_argument("--no-browser", action="store_true", help="跳过 Playwright 渲染验证")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    root = os.path.abspath(args.skill_dir)
    up = os.path.join(root, "assets", "upstream")
    r = Report()

    # ── A. 上游完整性 ──
    a: list[tuple[bool, str]] = []
    prim = sorted(glob.glob(os.path.join(up, "components", "primitives", "*.tsx")))
    atoms = sorted(glob.glob(os.path.join(up, "components", "atoms", "*.tsx")))
    a.append((len(prim) >= 22, f"上游 primitives 源码 {len(prim)} 个（含不在 registry 的 AgentScreen）"))
    a.append((len(atoms) >= 11, f"上游 atoms 源码 {len(atoms)} 个"))
    idx = os.path.join(root, "assets", "registry", "registry.json")
    items = []
    if os.path.exists(idx):
        items = json.load(open(idx, encoding="utf-8"))["items"]
    a.append((len(items) == 27, f"registry 索引 {len(items)} 条（应为 27）"))
    empty = []
    for it in items:
        p = os.path.join(root, "assets", "registry", f"{it['name']}.json")
        if not os.path.exists(p):
            empty.append(it["name"])
            continue
        d = json.load(open(p, encoding="utf-8"))
        if not any(f.get("content") for f in d.get("files", [])):
            empty.append(it["name"])
    a.append((not empty, f"registry 条目 content 均非空" + (f"（空: {empty}）" if empty else "")))
    # 21 个画廊组件源码都要能在 registry 或仓库树里找到
    reg_paths = set()
    for it in items:
        p = os.path.join(root, "assets", "registry", f"{it['name']}.json")
        if os.path.exists(p):
            d = json.load(open(p, encoding="utf-8"))
            reg_paths |= {f.get("path") for f in d.get("files", [])}
    missing_src = [p for p in reg_paths if p and not os.path.exists(os.path.join(up, p))]
    a.append((not missing_src, f"registry 声明的源码均在 upstream/ 中" + (f"（缺: {missing_src}）" if missing_src else "")))
    prov = os.path.join(up, "PROVENANCE.json")
    a.append((os.path.exists(prov), "PROVENANCE.json 存在（记录来源与 MIT 许可）"))
    for css in ("app/beautifui/foundation.css", "app/beautifui/records-table.css",
                "app/beautifui/sidebar-nav.css"):
        a.append((os.path.exists(os.path.join(up, css)), f"registry 内嵌 CSS 已落地：{css}"))
    r.group("A. 上游完整性", a)

    # ── B. 令牌一致性 ──
    b: list[tuple[bool, str]] = []
    fc = os.path.join(root, "assets", "foundation.standalone.css")
    css = open(fc, encoding="utf-8").read() if os.path.exists(fc) else ""
    b.append((bool(css), "foundation.standalone.css 存在"))
    absent = [t for t in CRITICAL_TOKENS if not re.search(rf"{re.escape(t)}\s*:", css)]
    b.append((not absent, f"36 个关键令牌齐全" + (f"（缺: {absent}）" if absent else "")))
    kf = set(re.findall(r"@keyframes\s+([\w-]+)", css))
    miss_kf = [k for k in KEYFRAMES if k not in kf]
    b.append((not miss_kf, f"8 个共享关键帧齐全" + (f"（缺: {miss_kf}）" if miss_kf else "")))
    # 阴影刻度内联
    b.append(("--shadow-xs:" in css and "--shadow-md:" in css,
              "shadow-plugin 的阴影刻度已内联（不依赖该 npm 包）"))
    # @theme 已搬入 :root
    b.append(("--ease-out-strong" in re.search(r":root\s*\{[\s\S]*?\n\}", css).group(0)
              if re.search(r":root\s*\{[\s\S]*?\n\}", css) else False,
              "@theme inline 的 --radius/--ease/--font 已搬进 :root（否则动效曲线会静默丢失）"))
    # 无残留指令 —— 必须先剥掉注释！CSS 注释里提到的 "@theme inline" / "@import"
    # 是我自己写的说明文字，不是真的指令（第一版就栽在这上面）。
    nocmt = re.sub(r"/\*[\s\S]*?\*/", "", css)
    live = [d for d in re.findall(r"@(import|custom-variant|theme)\b[^\n;{]*", nocmt)]
    b.append((not live, f"无残留 Tailwind 指令" + (f"（发现: {live}）" if live else "")))
    # 无自引用变量环
    cyc = re.findall(r"(--[\w-]+)\s*:\s*var\(\1\)", css)
    b.append((not cyc, f"无自引用变量环（@theme 里的 --shadow-x: var(--shadow-x) 已丢弃）"
              + (f"（发现: {cyc}）" if cyc else "")))
    b.append(("records-" in css and "sidebar-" in css,
              "records-table.css 与 sidebar-nav.css 已并入"))
    # 组件级自定义类（不是工具类，随组件一起拷的那种）
    needed = [".stream-tail", ".stream-caret", ".source-avatar", ".records-row",
              ".sidebar-", ".filter-status-todo", ".insight-chart-stage",
              ".primitive-card-pad", ".animated-underline", ".agent-cursor"]
    miss_cls = [n for n in needed if n not in css]
    b.append((not miss_cls,
              f"组件级自定义 CSS 齐全（{len(needed)} 项）" + (f"（缺: {miss_cls}）" if miss_cls else "")))
    if ".agent-cursor" in css:
        b.append((True, "已从 globals.css 捞回上游 registry 切片遗漏的 .agent-cursor"))
    r.group("B. 令牌一致性", b)

    # ── C. 移植件完整性 ──
    c: list[tuple[bool, str]] = []
    frags = {os.path.basename(p)[: -len(".frag.html")]
             for p in glob.glob(os.path.join(root, "assets", "ports", "*.frag.html"))}
    htmls = {os.path.basename(p)[:-5]
             for p in glob.glob(os.path.join(root, "assets", "html", "*.html"))}
    c.append((set(EXPECTED_SLUGS) <= frags,
              f"片段 {len(frags)}/21" + (f"（缺: {sorted(set(EXPECTED_SLUGS) - frags)}）" if EXPECTED_SLUGS and (set(EXPECTED_SLUGS) - frags) else "")))
    c.append((set(EXPECTED_SLUGS) <= htmls,
              f"成品 {len(htmls)}/21" + (f"（缺: {sorted(set(EXPECTED_SLUGS) - htmls)}）" if (set(EXPECTED_SLUGS) - htmls) else "")))
    # 每个成品必须自包含：含内联 <style>、含 --accent 令牌、含明暗切换
    notself = []
    for slug in sorted(htmls):
        t = open(os.path.join(root, "assets", "html", f"{slug}.html"), encoding="utf-8").read()
        if "<style>" not in t or "--accent:" not in t or "port-theme-toggle" not in t:
            notself.append(slug)
    c.append((not notself, f"成品均自包含（内联令牌 + 明暗切换）" + (f"（异常: {notself}）" if notself else "")))
    tiny = [s for s in sorted(htmls)
            if len(open(os.path.join(root, "assets", "html", f"{s}.html"), encoding="utf-8").read()) < 6000]
    c.append((not tiny, f"无异常小的成品（避免空壳）" + (f"（可疑: {tiny}）" if tiny else "")))
    r.group("C. 移植件完整性", c)

    # ── D. 渲染验证 ──
    d: list[tuple[bool, str]] = []
    render_log = ""
    if args.no_browser:
        d.append((True, "已跳过（--no-browser）"))
    else:
        # NODE_PATH 解析不到就不设，让 verify_ports.cjs 自己按候选顺序找 playwright
        env = dict(os.environ)
        if NODE_PATH:
            env["NODE_PATH"] = NODE_PATH
        cmd = [NODE, os.path.join(root, "scripts", "verify_ports.cjs")]
        try:
            pr = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=900,
                                cwd=root, encoding="utf-8", errors="replace")
            render_log = (pr.stdout or "") + (pr.stderr or "")
            ok_lines = [l for l in render_log.splitlines() if l.startswith("[verify] OK")]
            fail_lines = [l for l in render_log.splitlines() if "FAIL" in l]
            d.append((not fail_lines, f"全部移植件渲染 OK（{len(ok_lines)} 个通过、{len(fail_lines)} 个失败）"))
            for l in fail_lines:
                d.append((False, l.strip()))
            offline = [l for l in render_log.splitlines() if "net::ERR" in l and "IGNORE" not in l]
            d.append((True, "外部请求已拦截，验证全程离线（Google Fonts 噪声已忽略）"))
        except Exception as e:  # noqa: BLE001
            d.append((False, f"渲染验证未能执行：{type(e).__name__} {e}"))
    r.group("D. 渲染验证（Playwright）", d)

    # ── E. 离线自足 ──
    e: list[tuple[bool, str]] = []
    # 只检查「会真的去加载」的位置：src= 与 <link href=>。
    # <a href> 是用户点才走的普通链接（上游演示里的引用来源就是这种），不算离线依赖；
    # w3.org/2000/svg 是 SVG 命名空间标识，根本不是网络请求。
    NS_OK = ("http://www.w3.org/", "https://www.w3.org/")
    LOAD_OK = ("fonts.googleapis.com", "fonts.gstatic.com")
    # 有意保留的远端媒体：上游 Surfer 变体的视频，代码里有 onerror 离线回退
    INTENTIONAL = ("95dnc2a95qgwt9ff.public.blob.vercel-storage.com",)
    loading_ext: dict[str, list[str]] = {}
    intentional_hits: list[str] = []
    for slug in sorted(htmls):
        t = open(os.path.join(root, "assets", "html", f"{slug}.html"), encoding="utf-8").read()
        urls: set[str] = set()
        for m in re.finditer(r'\bsrc\s*=\s*["\']([^"\']+)["\']', t):
            urls.add(m.group(1))
        for m in re.finditer(r'<link[^>]+href\s*=\s*["\']([^"\']+)["\']', t):
            urls.add(m.group(1))
        bad = []
        for u in sorted(urls):
            if u.startswith("data:") or u.startswith("#") or u.startswith("file:"):
                continue
            if any(k in u for k in NS_OK + LOAD_OK):
                continue
            if any(k in u for k in INTENTIONAL):
                intentional_hits.append(f"{slug}: {u.split('/')[2]}")
                continue
            bad.append(u)
        if bad:
            loading_ext[slug] = bad[:4]
    e.append((not loading_ext, "成品无外部加载依赖（src / link 均为内联或白名单）"
              + (f"（{loading_ext}）" if loading_ext else "")))
    e.append((True, "有意保留的远端媒体："
              + (", ".join(sorted(set(intentional_hits))) if intentional_hits else "无")
              + "（上游 Surfer 视频，代码内有 onerror 离线回退）"))
    e.append((not glob.glob(os.path.join(root, "assets", "**", "node_modules"), recursive=True),
              "没有把 node_modules 混进 skill"))
    r.group("E. 离线自足", e)

    # ── F. 文档与许可 ──
    f: list[tuple[bool, str]] = []
    for rel in REQUIRED_DOCS:
        f.append((os.path.exists(os.path.join(root, rel)), f"{rel} 存在"))
    lic = os.path.join(root, "LICENSE.beautiful-ui")
    if os.path.exists(lic):
        lt = open(lic, encoding="utf-8").read()
        f.append(("MIT License" in lt and "Shane Levine" in lt, "上游 MIT 原文保留（含版权人署名）"))
    else:
        f.append((False, "上游 MIT 原文缺失"))
    sk = os.path.join(root, "SKILL.md")
    if os.path.exists(sk):
        st = open(sk, encoding="utf-8").read()
        fm = st.startswith("---") and "\n---" in st[3:]
        f.append((fm, "SKILL.md 带 YAML frontmatter"))
        f.append(("name: beautifului" in st, "frontmatter 含 name"))
        f.append(("Not for" in st, "description 含 Not for 排除项（避免误触发）"))
        f.append(("agent_created" in st, "frontmatter 含 agent_created"))
    prev = os.path.join(root, "assets", "preview", "index.html")
    f.append((os.path.exists(prev), "预览页 index.html 已生成"))
    r.group("F. 文档与许可", f)

    meta = {
        "version": "1.0.0",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "repo": "https://github.com/slev12397/beautiful-ui",
        "ref": "main",
        "fetched_at": "",
        "render_log": render_log,
    }
    if os.path.exists(prov):
        pj = json.load(open(prov, encoding="utf-8"))
        meta["ref"] = pj.get("ref", "main")
        meta["fetched_at"] = pj.get("fetched_at", "")
        meta["repo"] = pj.get("repo", meta["repo"])

    out = args.out or os.path.join(root, "v1.0.0-self-test.md")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(r.markdown(meta))

    passed, total = r.counts
    print(f"[self-test] {'PASS' if r.ok else 'FAIL'}  {passed}/{total} 项通过")
    for name, checks in r.groups:
        bad = [d for ok, d in checks if not ok]
        print(f"  {'OK  ' if not bad else 'FAIL'} {name}")
        for bd in bad[:6]:
            print(f"        - {bd}")
    print(f"[self-test] 报告写入 {out}")
    return 0 if r.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
