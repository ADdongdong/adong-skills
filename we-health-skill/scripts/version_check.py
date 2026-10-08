#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""微医健康技能 — 版本检查（拉取远端最新版本并与本地对比）。

远端地址返回一个 zip 包，版本号取自包内 we-health-skill/SKILL.md 的
frontmatter `version` 字段；本地版本号同样取自本技能 SKILL.md（唯一版本源）。

用法:
  python3 version_check.py              # 自动检查（默认 3 天 / 72 小时节流）
  python3 version_check.py --force      # 忽略节流，强制访问远端（用户主动询问版本时用）
  python3 version_check.py --json       # 结构化输出（含 local/remote/status）

输出契约:
  默认模式（自动检查）仅在需要升级时输出一行 `UPDATE_AVAILABLE local=<x> remote=<y>`，
  已最新 / 本地较新 / 缓存命中 / 判定失败等一律静默（无输出）。
  --force 模式（用户主动询问）额外输出 `VERSION_UP_TO_DATE local=<x> remote=<y>`
  或 `VERSION_CHECK_UNAVAILABLE`，便于上层按固定话术回复。
  任何异常均静默处理并以退出码 0 结束，不影响主流程、不触发降级。
  去重键 `notified_version` 只由自动模式读写；--force 只读不写，否则自动升级提示会被静默。

安全约束:
  仅匿名 GET/HEAD（不携带 API Key、机器码或任何用户信息）；
  只从 zip 中提取一个版本字符串，不落盘、不解压、不执行包内任何内容；
  接口地址为脚本内常量，不接受外部传入，仅允许通过环境变量调整节流与开关。
"""

from __future__ import annotations

import importlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

# 说明：zipfile / tempfile 为按需导入。该模块会被 query.py 在每次查询时导入，
# 而 zipfile 只在远端包真的变化时才需要，故不放在模块顶部。
# pathlib 由 credential 一并加载，放顶部零额外开销。

# 同目录导入 credential 模块（复用数据目录与 0600 安全读写）
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)
credential = importlib.import_module("credential")

# ── 配置 ──────────────────────────────────────────────

UPDATE_URL = "https://kano.guahao.com/NKd979871945"
LOCAL_SKILL_MD = os.path.join(_script_dir, "..", "SKILL.md")
VERSION_MEMBER = "we-health-skill/SKILL.md"      # 远端包内 SKILL.md 的固定路径
CHECK_TIMEOUT_SECONDS = 15
CHECK_TTL_SECONDS = 24 * 3600 * 3                # 默认 3 天节流
FAILURE_BACKOFF_SECONDS = 30 * 60                # 网络失败退避窗口（避免每次查询重复等超时）
MAX_PACKAGE_BYTES = 2 * 1024 * 1024              # 整包上限 2MB（实测约 106KB）
MAX_SKILL_MD_BYTES = 512 * 1024
MAX_ZIP_MEMBERS = 500
MAX_CLOCK_SKEW_SECONDS = 300                     # 时钟回拨容忍上限；大幅回拨视为时间戳不可信
CACHE_SCHEMA = 1
ENV_TTL = "WY_HEALTH_SKILL_UPDATE_TTL"
ENV_SWITCH = "WY_HEALTH_SKILL_UPDATE_CHECK"
REQUEST_HEADERS = {
    "User-Agent": "we-health-skill-version-check",
    "Accept": "application/zip,*/*",
}
VERSION_PATTERN = re.compile(r"^\d+(\.\d+){0,3}(-[0-9A-Za-z.\-]{1,32})?$")

# Windows 下强制 UTF-8 输出，避免中文乱码
if sys.platform == "win32":
    for _stream in (sys.stdout, sys.stderr):
        _reconfigure = getattr(_stream, "reconfigure", None)
        if _reconfigure is not None:
            _reconfigure(encoding="utf-8", errors="replace")


# ── 版本号解析与比较 ──────────────────────────────────

def read_frontmatter_version(text: str) -> str:
    """从 SKILL.md 文本中提取 frontmatter 的 version 值（不依赖 PyYAML）。

    非法值（不匹配 VERSION_PATTERN）一律返回空字符串，避免误报版本差异。
    """
    if not isinstance(text, str):
        return ""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    end = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() in ("---", "..."):
            end = idx
            break
    if end is None:
        return ""
    block = "\n".join(lines[1:end])
    match = re.search(r'^version\s*:\s*["\']?([^"\'\s#]+)', block, re.M)
    if not match:
        return ""
    value = match.group(1).strip()
    return value if VERSION_PATTERN.match(value) else ""


def parse_version(value: str) -> tuple[int, ...] | None:
    """解析为数字元组（不足 3 段补 0）；非法或超长返回 None。"""
    if not isinstance(value, str) or not VERSION_PATTERN.match(value):
        return None
    parts = [int(p) for p in value.split("-", 1)[0].split(".")]
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)


def compare_versions(left: str, right: str) -> int | None:
    """比较版本号：left > right 返回 1，相等 0，left < right 返回 -1；无法比较返回 None。

    预发布后缀（如 1.5.0-beta.1）遵循 semver：低于同号正式版。
    """
    lv = parse_version(left)
    rv = parse_version(right)
    if lv is None or rv is None:
        return None
    if lv != rv:
        return 1 if lv > rv else -1
    lp = "-" in left
    rp = "-" in right
    if lp == rp:
        return 0
    return -1 if lp else 1


def _max_version(left: str, right: str) -> str:
    """返回两者中较大的合法版本号（用于缓存单调性保护）。"""
    if not left:
        return right
    if not right:
        return left
    cmp = compare_versions(left, right)
    if cmp is None:
        return right
    return left if cmp >= 0 else right


# ── 本地版本 ──────────────────────────────────────────

def local_version() -> str:
    """本地技能版本号（取自 SKILL.md frontmatter）；读取/解析失败返回空字符串。"""
    try:
        path = Path(LOCAL_SKILL_MD).resolve()
        if not path.is_file() or path.stat().st_size > MAX_SKILL_MD_BYTES:
            return ""
        return read_frontmatter_version(path.read_text("utf-8"))
    except Exception:
        return ""


# ── 缓存（节流与单调性保护）──────────────────────────

def _cache_file() -> Path:
    return credential.data_dir() / "version-check.json"


def load_cache() -> dict[str, Any]:
    try:
        raw = credential._read_secure(_cache_file(), 8192)
        if not raw:
            return {}
        data = json.loads(raw.decode("utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_cache(cache: dict[str, Any]) -> None:
    """原子写缓存：先写同目录临时文件，再 rename 覆盖目标文件。

    多个 query.py 进程并发读写时，读者要么读到完整旧文件、要么读到完整新文件，
    不会出现半写状态（TTL 期间并发查询是常态）。写入失败不影响本次检查结果。
    """
    import tempfile
    try:
        blob = json.dumps(cache, ensure_ascii=False, indent=2).encode("utf-8")
        target = _cache_file()
        target.parent.mkdir(parents=True, exist_ok=True)
        # mkstemp 默认 0600，且与目标同目录保证 rename 原子性
        fd, tmp_name = tempfile.mkstemp(dir=str(target.parent), prefix=".version-check-", suffix=".tmp")
        try:
            view = memoryview(blob)
            while view:
                written = os.write(fd, view)
                view = view[written:]
        finally:
            os.close(fd)
        try:
            os.chmod(tmp_name, 0o600)
            os.replace(tmp_name, str(target))
        except OSError:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
    except Exception:
        pass  # 缓存写入失败不影响本次检查结果


def check_enabled() -> bool:
    """版本检查开关（WY_HEALTH_SKILL_UPDATE_CHECK=off 可关闭）。"""
    return os.environ.get(ENV_SWITCH, "").strip().lower() not in ("off", "0", "false", "no")


def check_ttl() -> int:
    """节流窗口秒数（WY_HEALTH_SKILL_UPDATE_TTL 可覆盖，<=0 表示每次强制检查）。"""
    raw = os.environ.get(ENV_TTL)
    if raw is not None:
        try:
            return max(0, int(raw))
        except ValueError:
            pass
    return CHECK_TTL_SECONDS


def _cache_fresh(cache: dict[str, Any], now: int) -> bool:
    ttl = check_ttl()
    if ttl <= 0:
        return False
    last = cache.get("checked_at_epoch")
    if not isinstance(last, (int, float)):
        return False
    delta = now - int(last)
    if delta < -MAX_CLOCK_SKEW_SECONDS:
        # 时钟大幅回拨：时间戳不可信，不据此抑制检查
        return False
    return delta < ttl


def _recent_failure(cache: dict[str, Any], now: int) -> bool:
    """最近一次尝试是否刚失败（退避窗口内不重复发起网络请求）。

    没有这个退避，离线环境下每次查询都会重新等待一次超时。
    """
    last = cache.get("last_failure_epoch")
    if not isinstance(last, (int, float)):
        return False
    delta = now - int(last)
    if delta < -MAX_CLOCK_SKEW_SECONDS:
        # 时钟大幅回拨：时间戳不可信，不据此延长退避
        return False
    return delta < FAILURE_BACKOFF_SECONDS


# ── 远端探测（匿名 GET/HEAD）─────────────────────────

def remote_headers(timeout: int = CHECK_TIMEOUT_SECONDS) -> tuple[dict[str, str] | None, bool]:
    """HEAD 探测远端包元信息（Last-Modified / Content-Length）。

    返回 (headers, head_fallback)：
    - 成功 → (dict, False)
    - 服务端有响应但 HEAD 未被正常处理（非 200 状态或任意 4xx/5xx）→ (None, True)，
      调用方回退整包 GET——网络路径已验证可达，GET 失败也会快速返回，不会叠加超时
    - 网络层失败（超时/不可达/DNS 等）→ (None, False)，调用方直接放弃，
      避免在断网时连续等待两次超时（内置调用场景尤为重要）
    """
    try:
        req = urllib.request.Request(UPDATE_URL, headers=dict(REQUEST_HEADERS), method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                return None, True
            return {"last_modified": resp.headers.get("Last-Modified", "") or ""}, False
    except urllib.error.HTTPError:
        return None, True
    except Exception:
        return None, False


def fetch_raw(timeout: int = CHECK_TIMEOUT_SECONDS) -> bytes:
    """匿名下载远端版本包（大小受限）；失败返回空字节。"""
    try:
        req = urllib.request.Request(UPDATE_URL, headers=dict(REQUEST_HEADERS), method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                return b""
            declared = resp.headers.get("Content-Length", "")
            if declared and declared.isdigit() and int(declared) > MAX_PACKAGE_BYTES:
                return b""
            raw = resp.read(MAX_PACKAGE_BYTES + 1)
    except Exception:
        return b""
    return raw if len(raw) <= MAX_PACKAGE_BYTES else b""


def extract_version_from_zip(raw: bytes) -> str:
    """从 zip 包内存中提取 SKILL.md 版本号：不落盘、不解压、不执行任何内容。"""
    if not raw:
        return ""
    import zipfile
    from io import BytesIO
    try:
        with zipfile.ZipFile(BytesIO(raw)) as zf:
            members = zf.infolist()
            if len(members) > MAX_ZIP_MEMBERS:
                return ""
            for info in members:
                name = info.filename
                if name != VERSION_MEMBER:
                    continue
                # 固定成员路径，仍校验绝对路径与目录穿越
                if name.startswith("/") or ".." in name.split("/"):
                    return ""
                if info.file_size > MAX_SKILL_MD_BYTES:
                    return ""
                with zf.open(info) as fp:
                    text = fp.read(MAX_SKILL_MD_BYTES).decode("utf-8", "replace")
                return read_frontmatter_version(text)
    except Exception:
        return ""
    return ""


def fetch_remote_version(timeout: int = CHECK_TIMEOUT_SECONDS) -> str:
    return extract_version_from_zip(fetch_raw(timeout))


# ── 结果判定 ──────────────────────────────────────────

def _resolve_status(local: str, remote: str, cached_remote: str = "") -> tuple[str, str]:
    """判定状态，返回 (status, 生效的远端版本)。

    单调性保护：远端回源到更旧包时，以缓存中已知的较高版本为生效版本再与本地统一比较：
    - 本地落后 → 照常提示升级（升到较低的新版也优于不升级，用较高版本号提示）；
    - 本地不落后 → 静默，避免因回源产生回滚误报。
    """
    if not remote:
        return "unknown", ""
    effective = remote
    if cached_remote:
        cmp_cached = compare_versions(cached_remote, remote)
        if cmp_cached is not None and cmp_cached > 0:
            effective = cached_remote
    cmp = compare_versions(local, effective)
    if cmp is None:
        return "unknown", effective
    if cmp < 0:
        return "update_available", effective
    if cmp == 0:
        return "up_to_date", effective
    return "ahead", effective


def _result(status: str, local: str, remote: str, source: str, now: int,
            message: str = "") -> dict[str, Any]:
    return {
        "status": status,
        "local": local,
        "remote": remote,
        "source": source,
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
        "message": message,
    }


def check(force: bool = False, timeout: int = CHECK_TIMEOUT_SECONDS) -> dict[str, Any]:
    """执行版本检查。

    force=False（自动检查）：受节流约束，命中缓存时不访问远端。
    force=True（用户主动询问）：忽略节流，不做「已提示过」去重。
    timeout：单次网络请求超时（秒）；内置于查询流程时传入更小预算，避免拖慢主回答。
    """
    now = int(time.time())
    cache = load_cache()
    # 本地版本唯一来源为 SKILL.md；读取/解析失败得到空串，
    # 后续比较会判为 unknown（不提示），绝不使用回退常量猜测版本号
    local = local_version()

    if not force and not check_enabled():
        return _result("disabled", local, "", "none", now, "版本检查已关闭")

    cached_remote = cache.get("remote_version")
    cached_remote = cached_remote if isinstance(cached_remote, str) else ""
    notified = cache.get("notified_version")
    notified = notified if isinstance(notified, str) else ""

    # ── 节流：TTL 内（或刚失败处于退避窗口内）且本地版本未变，直接复用缓存，零网络请求 ──
    if (
        not force
        and cache.get("local_version") == local
        and (_cache_fresh(cache, now) or _recent_failure(cache, now))
    ):
        remote = cached_remote
        status, remote = _resolve_status(local, remote, cached_remote)
        if status == "update_available" and notified == remote:
            status = "update_notified"
        return _result(status, local, remote, "cache", now)

    # ── 远端探测：HEAD 门控，包未变则 0 字节下载 ──
    headers, head_fallback = remote_headers(timeout)
    if headers is not None:
        unchanged = (
            bool(headers["last_modified"])
            and headers["last_modified"] == cache.get("remote_last_modified")
            and bool(cached_remote)
        )
        remote = cached_remote if unchanged else fetch_remote_version(timeout)
    elif head_fallback:
        # 服务端可达但 HEAD 未被正常处理（非 200/4xx/5xx）：回退整包 GET
        remote = fetch_remote_version(timeout)
    else:
        # 网络层失败（超时/不可达）：直接放弃，避免再次等待一次超时
        remote = ""

    if not remote:
        # 远端不可达或无法解析：记录失败时间进入退避窗口（避免每次查询都重复等待超时），
        # 并退回缓存中已知的远端版本，使离线期间仍可沿用既有判定。
        # local_version 必须一并写入，否则节流条件（本地版本未变）不成立，退避无法命中。
        cache["schema"] = CACHE_SCHEMA
        cache["local_version"] = local
        cache["last_failure_epoch"] = now
        save_cache(cache)
        if cached_remote:
            status, _ = _resolve_status(local, cached_remote, cached_remote)
            if status == "update_available" and not force and notified == cached_remote:
                status = "update_notified"
            return _result(status, local, cached_remote, "cache", now, "暂时无法获取版本信息")
        return _result("unknown", local, "", "remote", now, "暂时无法获取版本信息")

    status, remote = _resolve_status(local, remote, cached_remote)
    if status == "update_available" and not force and notified == remote:
        status = "update_notified"

    last_modified = headers["last_modified"] if headers else ""
    if not last_modified and isinstance(cache.get("remote_last_modified"), str):
        last_modified = cache["remote_last_modified"]

    # 去重键只由自动路径消费：force（用户主动查询）不得占用，否则手动查一次后，
    # 后续自动检查会一直判为「已提示过」而静默跳过。
    if not force and status in ("update_available", "update_notified"):
        notified_version = remote
    else:
        notified_version = notified

    save_cache({
        "schema": CACHE_SCHEMA,
        "checked_at_epoch": now,
        "remote_last_modified": last_modified,
        "remote_version": _max_version(cached_remote, remote),
        "local_version": local,
        "status": status,
        "notified_version": notified_version,
    })
    return _result(status, local, remote, "remote", now)


# ── CLI 入口 ──────────────────────────────────────────

def _emit(obj: dict[str, Any]) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def main() -> None:
    args = sys.argv[1:]
    if "--help" in args or "-h" in args:
        print((__doc__ or "").strip())
        return

    force = "--force" in args
    result = check(force=force)

    if "--json" in args:
        _emit(result)
        return

    status = result.get("status")
    if status == "update_available" and result.get("remote"):
        print(f"UPDATE_AVAILABLE local={result['local']} remote={result['remote']}")
    elif force:
        if status in ("up_to_date", "ahead"):
            print(f"VERSION_UP_TO_DATE local={result['local']} remote={result.get('remote') or result['local']}")
        elif status in ("unknown", "disabled"):
            print("VERSION_CHECK_UNAVAILABLE")
    # 自动检查模式：仅 UPDATE_AVAILABLE 有输出，其余静默


if __name__ == "__main__":
    main()
