#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""微医健康技能 — API Key 凭证管理。

macOS：API Key 直接存入系统 Keychain（受用户登录态保护），不落盘；
      Keychain 不可用时回退到本地加密文件。
Linux/Windows：本地加密文件。

加密实现：SHA-256 CTR + HMAC-SHA256 认证（先验签后解密），格式
nonce(16) + ciphertext + tag(32)，权限 0600。不是 AES-GCM。

降级路径：Keychain 不可用时回退本地加密文件，KEK（`.encryption_key`）与密文同在
用户目录，能读到该用户文件的一方可能同时拿到两者，强度低于 Keychain；恢复
Keychain 后执行 `credential.py set <key>` 可写回。

用法:
  python3 credential.py set <api-key>    # 存储 API Key
  python3 credential.py get              # 读取（不回显完整 Key）
  python3 credential.py delete           # 删除
  python3 credential.py status           # 查看配置状态
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import stat as stat_mod
import sys
from pathlib import Path
from typing import Any

# ── 配置 ──────────────────────────────────────────────

SERVICE = "we-health-skill"
APIKEY_ACCOUNT = "WEDOCTOR_SKILL_APIKEY"          # Keychain 中 API Key 的 account（macOS 主路径）
KEK_ACCOUNT = "WEDOCTOR_SKILL_ENCKEY"      # Keychain 中 KEK 的 account（加密文件兜底时用）
MAX_KEY_LENGTH = 512
KEY_PATTERN = re.compile(r"^[A-Za-z0-9_\-.]+$")

if sys.platform == "win32":
    for _stream in (sys.stdout, sys.stderr):
        _reconfigure = getattr(_stream, "reconfigure", None)
        if _reconfigure is not None:
            _reconfigure(encoding="utf-8", errors="replace")


# ── 校验 ──────────────────────────────────────────────

def validate_key(key: str) -> bool:
    """校验 API Key 格式：仅允许字母、数字、连字符、下划线、点号。"""
    if not key or not isinstance(key, str) or len(key) > MAX_KEY_LENGTH:
        return False
    return bool(KEY_PATTERN.match(key))


# ── 路径 ──────────────────────────────────────────────

def data_dir() -> Path:
    """返回数据目录（环境变量 WY_HEALTH_SKILL_DATA 可覆盖，默认 ~/.wy-health-skill）。"""
    directory = os.environ.get("WY_HEALTH_SKILL_DATA") or str(Path.home() / ".wy-health-skill")
    resolved = Path(directory).resolve()
    home = Path.home().resolve()
    if resolved != home and home not in resolved.parents:
        raise ValueError("数据目录必须在用户主目录下")
    return resolved


def _enc_file() -> Path:
    return data_dir() / "credentials.enc"


def _kek_file() -> Path:
    return data_dir() / ".encryption_key"


# ── 安全文件读写（公共）──────────────────────────────

def _write_secure(path: Path, data: bytes) -> bool:
    """写入文件，权限 0600。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    fd = os.open(str(path), flags, 0o600)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass  # Windows 不支持
    return True


def _read_secure(path: Path, max_size: int) -> bytes | None:
    """读取普通文件，校验类型与大小。"""
    if not path.exists():
        return None
    try:
        st = path.stat()
        if not stat_mod.S_ISREG(st.st_mode) or st.st_size > max_size:
            return None
        return path.read_bytes()
    except OSError:
        return None


# ── 加密───────────────────────

def _key_stream(kek: bytes, nonce: bytes, length: int) -> bytes:
    """从 KEK+nonce 派生 SHA-256 密钥流（CTR 模式）。"""
    stream = b""
    for i in range(0, length, 32):
        stream += hashlib.sha256(kek + nonce + i.to_bytes(4, "big")).digest()
    return stream[:length]


def _encrypt(plaintext: str, kek: bytes) -> bytes:
    """SHA-256 CTR 流加密 + HMAC-SHA256 认证，返回 nonce(16) + ciphertext + tag(32)。"""
    data = plaintext.encode("utf-8")
    nonce = os.urandom(16)
    ks = _key_stream(kek, nonce, len(data))
    ct = bytes(a ^ b for a, b in zip(data, ks))
    tag = hmac.new(kek, nonce + ct, hashlib.sha256).digest()
    return nonce + ct + tag


def _decrypt(blob: bytes, kek: bytes) -> str | None:
    """SHA-256 CTR 解密，先验证 HMAC 再解密。"""
    if len(blob) < 49:  # nonce(16) + tag(32) + 至少 1 字节
        return None
    nonce = blob[:16]
    ct = blob[16:-32]
    tag = blob[-32:]
    expected = hmac.new(kek, nonce + ct, hashlib.sha256).digest()
    if not hmac.compare_digest(tag, expected):
        return None
    ks = _key_stream(kek, nonce, len(ct))
    try:
        return bytes(a ^ b for a, b in zip(ct, ks)).decode("utf-8")
    except Exception:
        return None


# ── Keychain 底层（仅 macOS）─────────────────────────

def _is_macos() -> bool:
    return sys.platform == "darwin"


def _kc_run(args: list[str]) -> bool:
    """执行 security 命令，返回是否成功。"""
    if not _is_macos():
        return False
    try:
        import subprocess
        return subprocess.run(["security", *args], capture_output=True).returncode == 0
    except Exception:
        return False


def _kc_get(account: str) -> str | None:
    """从 Keychain 读取密码值。"""
    if not _is_macos():
        return None
    try:
        import subprocess
        r = subprocess.run(
            ["security", "find-generic-password", "-s", SERVICE, "-a", account, "-w"],
            capture_output=True, text=True,
        )
        return r.stdout.strip() if r.returncode == 0 and r.stdout else None
    except Exception:
        return None


# ── API Key Keychain 直存（macOS 主路径）─────────────

def apikey_keychain_set(key: str) -> bool:
    return _kc_run(["add-generic-password", "-s", SERVICE, "-a", APIKEY_ACCOUNT, "-w", key, "-U"])


def apikey_keychain_get() -> str | None:
    raw = _kc_get(APIKEY_ACCOUNT)
    return raw if (raw and validate_key(raw)) else None


def apikey_keychain_delete() -> bool:
    return _kc_run(["delete-generic-password", "-s", SERVICE, "-a", APIKEY_ACCOUNT])


# ── KEK 存储（加密文件兜底用）────────────────────────

def _kek_keychain_set(kek: bytes) -> bool:
    return _kc_run(["add-generic-password", "-s", SERVICE, "-a", KEK_ACCOUNT,
                    "-w", base64.b64encode(kek).decode("ascii"), "-U"])


def _kek_keychain_get() -> bytes | None:
    raw = _kc_get(KEK_ACCOUNT)
    if not raw:
        return None
    try:
        kek = base64.b64decode(raw, validate=True)
        return kek if len(kek) == 32 else None
    except Exception:
        return None


def kek_get() -> bytes | None:
    """获取 KEK：Keychain 优先，文件兜底。"""
    kek = _kek_keychain_get()
    if kek:
        return kek
    data = _read_secure(_kek_file(), 32)
    return data if data and len(data) == 32 else None


def kek_get_or_create() -> bytes | None:
    """获取或生成 KEK 并持久化。"""
    kek = kek_get()
    if kek:
        return kek
    kek = os.urandom(32)
    if _kek_keychain_set(kek) or _write_secure(_kek_file(), kek):
        return kek
    return None


def kek_delete() -> bool:
    """删除 KEK：Keychain + 兜底文件。"""
    deleted = _kc_run(["delete-generic-password", "-s", SERVICE, "-a", KEK_ACCOUNT])
    try:
        _kek_file().unlink()
        deleted = True
    except OSError:
        pass
    return deleted


# ── 加密凭证文件 ────────────────────────────

def enc_set(key: str, kek: bytes) -> bool:
    return _write_secure(_enc_file(), _encrypt(key, kek))


def enc_get(kek: bytes) -> str | None:
    blob = _read_secure(_enc_file(), 4096)
    if blob is None:
        return None
    key = _decrypt(blob, kek)
    return key if (key and validate_key(key)) else None


def enc_delete() -> bool:
    try:
        _enc_file().unlink()
        return True
    except OSError:
        return False


# ── 统一接口 ──────────────────────────────────────────

def set_key(key: str) -> dict[str, Any]:
    """存储 API Key：macOS Keychain 直存优先，失败回退加密文件。"""
    if not key or not key.strip():
        return {"success": False, "message": "API Key 不能为空"}
    trimmed = key.strip()
    if not validate_key(trimmed):
        return {"success": False, "message": "API Key 格式无效（仅允许字母、数字、连字符、下划线、点号）"}

    # macOS 主路径：Keychain 直存，不落盘
    if apikey_keychain_set(trimmed):
        return {"success": True, "stored": "keychain", "message": "API Key 已保存到 macOS Keychain"}

    # 回退：加密文件
    kek = kek_get_or_create()
    if kek is None or not enc_set(trimmed, kek):
        return {"success": False, "message": "API Key 存储失败"}
    return {"success": True, "stored": "file", "message": "API Key 已加密存储到本地文件（Keychain 不可用）"}


def get_key() -> dict[str, Any]:
    """读取 API Key：macOS Keychain 优先，失败回退加密文件。"""
    kc_key = apikey_keychain_get()
    if kc_key:
        return {"key": kc_key, "source": "keychain"}

    kek = kek_get()
    if kek:
        key = enc_get(kek)
        if key:
            return {"key": key, "source": "file"}
    return {"key": None, "source": None}


def delete_key() -> dict[str, Any]:
    """删除所有凭证：Keychain API Key + KEK + 加密文件。

    注意：不能用 or 短路串联三个删除调用——Keychain 删除成功后
    加密文件清理会被跳过，残留的密文会让 get_key() 兜底读回"已删除"的 Key。
    """
    deleted = apikey_keychain_delete()
    deleted = kek_delete() or deleted
    deleted = enc_delete() or deleted
    if deleted:
        return {"success": True, "message": "API Key 已删除"}
    return {"success": False, "message": "未找到已存储的 API Key"}


def status() -> dict[str, Any]:
    """查看状态（不回显完整 Key）。"""
    result = get_key()
    key = result["key"]
    source = result["source"]
    if not key:
        return {"success": True, "configured": False, "message": result.get("error", "未配置 API Key")}
    masked = f"{key[:4]}****{key[-4:]}" if len(key) > 8 else "****"
    source_label = {"keychain": "macOS Keychain", "file": "本地加密文件"}.get(source, source)
    return {
        "success": True, "configured": True, "source": source_label, "key_preview": masked,
        "message": f"API Key 已配置（来源：{source_label}，预览：{masked}）",
    }


# ── CLI 入口 ──────────────────────────────────────────

def _emit(obj: dict[str, Any]) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def main() -> None:
    args = sys.argv[1:]
    if not args:
        _emit({"success": False, "message": "未知命令。可用命令: set <key>, get, delete, status"})
        sys.exit(1)
    cmd = args[0]
    if cmd == "set":
        if len(args) < 2:
            _emit({"success": False, "message": "用法: python3 credential.py set <api-key>"})
            sys.exit(1)
        _emit(set_key(args[1]))
    elif cmd == "get":
        result = get_key()
        _emit({"success": True, "configured": bool(result["key"]), "source": result["source"]})
    elif cmd == "delete":
        _emit(delete_key())
    elif cmd == "status":
        _emit(status())
    else:
        _emit({"success": False, "message": "未知命令。可用命令: set <key>, get, delete, status"})
        sys.exit(1)


if __name__ == "__main__":
    main()
