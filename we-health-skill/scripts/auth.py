#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""微医健康技能 — 自动注册（设备机器码兑换 API Key）。

取消首次引导与用户同意流程：无需用户手动配置 API Key。
凭证缺失时自动获取本机机器码，调用微医兑换接口注册并本地保存
（macOS Keychain 优先，加密文件兜底），新用户无感使用。

用法:
  python3 auth.py machine-code   # 查看本机机器码
  python3 auth.py register       # 手动触发机器码兑换注册（query.py 会自动完成，通常无需执行）
  python3 auth.py status         # 查看机器码 + 凭证综合状态
"""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import platform
import subprocess
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

# 同目录导入 credential 模块
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)
credential = importlib.import_module("credential")

# ── 配置 ──────────────────────────────────────────────

# 本地技能版本号的唯一来源为 SKILL.md 的 frontmatter `version`，无任何回退常量。
def skill_version() -> str:
    """返回本地技能版本号（读取 SKILL.md，失败返回空字符串）。"""
    try:
        return importlib.import_module("version_check").local_version()
    except Exception:
        return ""


VERSION = skill_version()  # 兼容既有引用；实际取值以 SKILL.md 为准
EXCHANGE_URL = "https://api-gateway.guahao.com/user/userapikey/getByMachineCode"
EXCHANGE_HEADERS = {
    "Content-Type": "application/json;charset=UTF-8",
    "weiyi-appid": "p_h5_weiyi",
    "weiyi-version": "1.04",
}
EXCHANGE_TIMEOUT_SECONDS = 30
MAX_MACHINE_CODE_LENGTH = 128

# Windows 下强制 UTF-8 输出，避免中文乱码
if sys.platform == "win32":
    for _stream in (sys.stdout, sys.stderr):
        _reconfigure = getattr(_stream, "reconfigure", None)
        if _reconfigure is not None:
            _reconfigure(encoding="utf-8", errors="replace")


# ── 机器码解析 ────────────────────────────────────────

def _sanitize(code: str | None) -> str | None:
    """校验机器码格式：非空、长度受限、仅允许字母数字与 - _ ."""
    if not code or not isinstance(code, str):
        return None
    code = code.strip().strip('"').strip("'")
    if not code or len(code) > MAX_MACHINE_CODE_LENGTH:
        return None
    if not all(c.isalnum() or c in "-_." for c in code):
        return None
    return code


def _macos_serial() -> str | None:
    """macOS：IOPlatformSerialNumber（与示例 LR4331R4TL 同源）。"""
    try:
        r = subprocess.run(
            ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
            capture_output=True, text=True, timeout=10,
        )
        for line in r.stdout.splitlines():
            if "IOPlatformSerialNumber" in line:
                _, _, value = line.partition("=")
                return _sanitize(value)
    except Exception:
        pass
    return None


def _windows_machine_guid() -> str | None:
    """Windows：注册表 MachineGuid（强制 64 位视图，避免 32 位 Python 被 WOW64 重定向）。"""
    try:
        import winreg
        access = winreg.KEY_READ
        if hasattr(winreg, "KEY_WOW64_64KEY"):
            access |= winreg.KEY_WOW64_64KEY
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography", access=access
        ) as key:
            value, _ = winreg.QueryValueEx(key, "MachineGuid")
            return _sanitize(str(value))
    except Exception:
        return None


def _linux_machine_id() -> str | None:
    """Linux：systemd machine-id（dbus machine-id 兜底）。"""
    for path in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
        try:
            content = Path(path).read_text("utf-8").strip()
            code = _sanitize(content)
            if code:
                return code
        except Exception:
            continue
    return None


def _fallback_code() -> str:
    """兜底：MAC + 主机名 + 平台的哈希，保证同一设备稳定。"""
    raw = f"{uuid.getnode()}-{platform.node()}-{sys.platform}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def _machine_code_file() -> Path:
    return credential.data_dir() / "machine-code"


def _resolve_machine_code() -> str:
    if sys.platform == "darwin":
        code = _macos_serial()
    elif sys.platform == "win32":
        code = _windows_machine_guid()
    else:
        code = _linux_machine_id()
    return code if code else _fallback_code()


def get_machine_code() -> str:
    """返回本机机器码：优先使用已持久化的值（保证稳定），否则解析并持久化。"""
    cached = credential._read_secure(_machine_code_file(), MAX_MACHINE_CODE_LENGTH + 16)
    if cached:
        try:
            value = cached.decode("utf-8").strip()
            if value:
                return value
        except Exception:
            pass
    code = _resolve_machine_code()
    try:
        credential._write_secure(_machine_code_file(), code.encode("utf-8"))
    except Exception:
        pass  # 持久化失败不影响本次使用
    return code


# ── 机器码兑换 API Key ────────────────────────────────

def register() -> dict[str, Any]:
    """用本机机器码兑换 API Key 并存入本地凭证（Keychain 优先，加密文件兜底）。"""
    machine_code = get_machine_code()
    body = json.dumps({"machineCode": machine_code}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        EXCHANGE_URL, data=body, headers=dict(EXCHANGE_HEADERS), method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=EXCHANGE_TIMEOUT_SECONDS) as response:
            if response.status != 200:
                return {"success": False, "message": f"注册接口返回 HTTP {response.status}"}
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"success": False, "message": f"注册接口返回 HTTP {e.code}"}
    except (urllib.error.URLError, TimeoutError) as e:
        reason = getattr(e, "reason", e)
        return {"success": False, "message": f"注册接口请求失败：{reason}"}
    except ValueError:
        return {"success": False, "message": "注册接口响应格式异常"}

    if not isinstance(payload, dict):
        return {"success": False, "message": "注册接口响应格式异常"}
    data = payload.get("data")
    api_key = data.get("apiKey") if isinstance(data, dict) else None
    if str(payload.get("code")) != "0" or not api_key or not str(api_key).strip():
        message = payload.get("message") or "未返回有效凭证"
        return {"success": False, "message": f"注册接口返回异常：{message}"}

    stored = credential.set_key(str(api_key).strip())
    if not stored.get("success"):
        return {"success": False, "message": f"凭证保存失败：{stored.get('message', '未知错误')}"}
    return {
        "success": True,
        "machine_code": machine_code,
        "stored": stored.get("stored"),
        "message": "已通过设备机器码自动注册",
    }


# ── 统一入口 ──────────────────────────────────────────

def ensure_api_key(force: bool = False) -> dict[str, Any]:
    """确保本地存在可用 API Key。

    本地已存且未要求强制重新兑换时直接使用；否则机器码兑换注册。
    全程静默，无需用户介入。
    """
    if not force:
        cred = credential.get_key()
        if cred.get("key"):
            return {"success": True, "key": cred["key"], "source": cred.get("source"), "registered": False}
    result = register()
    if not result.get("success"):
        return result
    cred = credential.get_key()
    if cred.get("key"):
        return {"success": True, "key": cred["key"], "source": cred.get("source"), "registered": True}
    return {"success": False, "message": "注册成功但读取凭证失败"}


# ── CLI 入口 ──────────────────────────────────────────

def _emit(obj: dict[str, Any]) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def main() -> None:
    args = sys.argv[1:]
    cmd = args[0] if args else ""

    if cmd == "machine-code":
        _emit({"success": True, "machine_code": get_machine_code()})
    elif cmd == "register":
        _emit(ensure_api_key(force=True))
    elif cmd == "status":
        cred = credential.get_key()
        machine_code = get_machine_code()
        _emit({
            "success": True,
            "version": VERSION or "unknown",
            "machine_code": machine_code,
            "api_key_configured": bool(cred.get("key")),
            "message": "API Key 已配置" if cred.get("key") else "API Key 未配置（下次查询将自动注册）",
        })
    else:
        _emit({"success": False, "message": "未知命令。可用命令: machine-code, register, status"})
        sys.exit(1)


if __name__ == "__main__":
    main()
