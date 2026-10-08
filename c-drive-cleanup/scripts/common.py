#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公共工具库（c-drive-cleanup skill v1.2）

所有脚本共用：路径归一化、junction 判定、原子写、**安全门 guard**。

设计背景（v1.2 安全加固）：
  一起真实事故中，agent 把 robocopy /MOVE 和 /MIR 用在了正在被微信写入的迁移源目录上，
  导致聊天记录分裂丢失。根因是"哪些命令能用于哪些路径"只写在文档里，代码层没有任何拦截。
  guard() 就是代码层的强制拦截点——文档是给人看的，guard 是给机器执行的。

退出码约定: 0 成功 / 2 部分失败 / 3 安全门拦截 / 4 状态卡死待人工
"""
import os
import sys
import json
import time
import ctypes
import tempfile
import subprocess

FILE_ATTRIBUTE_REPARSE_POINT = 0x400
INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF


class GuardError(Exception):
    """安全门拦截。必须由顶层捕获并 exit(3)，禁止被局部 except 吞掉。"""
    pass


class StuckError(Exception):
    """状态卡死，需人工介入。顶层捕获后 exit(4)。"""
    pass


# ---------- 路径工具 ----------

def norm_path(p):
    """归一化：去 \\\\?\\ 前缀、去尾斜杠、统一小写、分隔符统一反斜杠（供比对用）"""
    if not p:
        return ''
    s = os.path.abspath(p)
    s = s.replace('\\\\?\\', '').replace('\\\\.\\', '')
    s = s.rstrip('\\/')
    return s.lower()


def expand(p):
    """展开环境变量 + 用户目录（支持 %APPDATA% 和 ~）"""
    return os.path.expandvars(os.path.expanduser(p))


def fmt(size):
    if size is None or size < 0:
        return '-'
    if size >= 2**30:
        return f'{size/2**30:.2f} GB'
    if size >= 2**20:
        return f'{size/2**20:.1f} MB'
    return f'{size/2**10:.0f} KB'


# ---------- Junction 判定（修 v1.1 的两处 bug） ----------

_k32 = ctypes.windll.kernel32
# 坑: 不显式声明 argtypes/restype 时，64 位下返回值可能被截断，
# 且 Unicode 路径参数传递不稳定 —— 这是 v1.1 "先判失效后判生效"翻转的成因之一
_k32.GetFileAttributesW.argtypes = [ctypes.c_wchar_p]
_k32.GetFileAttributesW.restype = ctypes.c_uint32


def file_attrs(path):
    a = _k32.GetFileAttributesW(path)
    return None if a == INVALID_FILE_ATTRIBUTES else a


def has_reparse(path, retries=3, delay=0.5):
    """reparse 位判定，带重试。返回 True/False/**None**(不确定)。
    坑: 卷瞬时不可达（移动硬盘休眠/BitLocker/Defender 扫描）会返回 -1，
    此时必须返回 None 而不是 False —— 否则就会像事故里那样"先判失效后改口"。"""
    for i in range(retries):
        a = file_attrs(path)
        if a is not None:
            return bool(a & FILE_ATTRIBUTE_REPARSE_POINT)
        if i < retries - 1:
            time.sleep(delay)
    return None


def safe_readlink(path):
    try:
        return os.readlink(path)
    except (OSError, ValueError):
        # 坑: OneDrive 占位符等 reparse point 不是符号链接，readlink 抛 ValueError 而非 OSError
        return None


def is_junction(path):
    """reparse 位为真（不确定时保守返回 False）。仅供展示/粗筛，
    权威判定一律用 check_junction() 五判据。"""
    return has_reparse(path) is True


# ---------- 原子写 ----------

def atomic_write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def atomic_write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


# ---------- 安全门（v1.2 核心） ----------

# 黄灯命令（rm -rf / rmtree / robocopy /MIR）允许作用的路径白名单
# 全部锚定到具体缓存目录，展开后正则匹配
A_PATH_ALLOW = [
    r'%TEMP%',
    r'%LOCALAPPDATA%\Temp',
    r'%SystemRoot%\Temp',
    r'%LOCALAPPDATA%\CrashDumps',
    r'%LOCALAPPDATA%\pip\cache',
    r'%LOCALAPPDATA%\wsl-crashes',
    r'%LOCALAPPDATA%\SquirrelTemp',
    r'%SystemRoot%\SoftwareDistribution\Download',
]

# 红灯：任何情况下都不允许删除/移动/镜像清空的路径特征
NEVER_TOUCH_PATTERNS = [
    r'\$Recycle\.Bin',
    r'\\desktop$', r'\\documents$', r'\\downloads$',
    r'\\pictures$', r'\\music$', r'\\videos$',
    r'\\contacts$', r'\\favorites$', r'\\saved games$',
]

# S 类敏感数据路径特征（聊天记录/邮件/密码库 —— 丢失不可逆, 丢了没有"撤销"）
# scan_c_drive / migrate_junction / wechat_doctor 共用这一份
S_RULES = [
    (r'xwechat_files',         '微信4.x账号数据根（db_storage/message_N.db 聊天库）'),
    (r'we chat files',         '微信3.x数据目录'),
    (r'\\tencent\\xwechat',    '微信4.x运行时+配置（config ini 指定真实数据根）'),
    (r'\\tencent\\wechat',     '微信旧版数据'),
    (r'db_storage',            '聊天数据库目录'),
    (r'\\outlook\\.+\.pst$',   'Outlook 邮件数据文件'),
    (r'\\outlook\\.+\.ost$',   'Outlook 离线邮件缓存'),
    (r'\.kdbx$',               'KeePass 密码库'),
    (r'login data$',           'Chrome/Edge 密码库（迁移含它的目录前必须备份）'),
    (r'\\qq\\nt_?db',          'QQ NT 聊天数据库'),
    (r'\\dingtalk\\.+account', '钉钉账号数据'),
]


def is_sensitive(path):
    """判定路径是否命中 S 类敏感数据规则"""
    norm = norm_path(path)
    import re
    return any(re.search(pat, norm) for pat, _ in S_RULES)


def _compile(patterns):
    import re
    out = []
    for p in patterns:
        try:
            out.append(re.compile(expand(p).rstrip('\\').lower().replace('\\', '\\\\') + r'(\\|$)'))
        except Exception:
            continue
    return out


def known_folder_paths():
    """桌面/文档/下载/图片等已知文件夹真实位置（不依赖注册表，用 SHGetKnownFolderPath）"""
    import uuid
    FOLDERS = {
        'Desktop': '{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}',
        'Documents': '{FDD39AD0-238F-46AF-ADB4-6C85480369C7}',
        'Downloads': '{374DE290-123F-4565-9164-39C4925E467B}',
        'Pictures': '{33E28130-4E1E-4676-835A-98395C3BC3BB}',
        'Music': '{4BD8D571-6D19-48D3-BE97-422220080E43}',
        'Videos': '{18989B1D-99B5-455B-841C-AB7C74E4DDFC}',
    }

    class GUID(ctypes.Structure):
        _fields_ = [('Data1', ctypes.c_ulong), ('Data2', ctypes.c_ushort),
                    ('Data3', ctypes.c_ushort), ('Data4', ctypes.c_ubyte * 8)]

    result = {}
    for label, fid in FOLDERS.items():
        try:
            u = uuid.UUID(fid)
            g = GUID(u.time_low, u.time_mid, u.time_hi_version, (ctypes.c_ubyte * 8)(*u.bytes[8:]))
            buf = ctypes.c_void_p()
            r = ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(g), 0, None, ctypes.byref(buf))
            if r == 0:
                result[label] = ctypes.wstring_at(buf)
                ctypes.windll.ole32.CoTaskMemFree(buf)
        except Exception:
            pass
    return result


def guard(path, extra_protected=None, action='删除', allow=None):
    """安全门：任何破坏性操作（rmtree / robocopy /MIR / /MOVE / delete）前必须调用。

    拦截条件（命中即 raise GuardError）:
      1. 路径在迁移状态机里登记过（src / dst / *_backup）—— 由调用方传入
      2. 路径属于已知文件夹（桌面/文档/下载/图片等）
      3. 路径是回收站
      4. 路径是 S 类敏感数据（聊天库/邮件/密码库）—— 由调用方传入
    allow: 归一化路径集合，命中则放行（仅供走完全部确认门的流程使用，
           如 delete-backup 的四道门；普通清理流程不得使用）。
    """
    norm = norm_path(path)
    if not norm:
        raise GuardError(f'空路径，拒绝{action}')
    allow_norms = {norm_path(a) for a in (allow or [])}

    protected = list(extra_protected or [])
    for label, p in known_folder_paths().items():
        if p:
            protected.append(p)
    protected.append(os.path.join(os.path.expanduser('~'), 'xwechat_files'))

    if norm not in allow_norms:
        for p in protected:
            if not p:
                continue
            pn = norm_path(p)
            if norm == pn or norm.startswith(pn + os.sep):
                raise GuardError(
                    f'安全门拦截：{path}\n'
                    f'  原因：该路径是受保护位置（{pn}）\n'
                    f'  规则：迁移源/目标/备份、已知文件夹、敏感数据目录，禁止{action}')

    import re
    for pat in NEVER_TOUCH_PATTERNS:
        if re.search(pat, norm):
            raise GuardError(
                f'安全门拦截：{path}\n'
                f'  原因：命中禁止触碰模式 {pat}\n'
                f'  规则：回收站与已知文件夹不得由脚本清空，须用户自行操作')

    return True


def guard_a_class(path, extra_protected=None):
    """黄灯门：robocopy /MIR 与 rmtree 只允许作用于 A 类白名单路径。
    先过红灯 guard，再校验是否在 A 类白名单内。"""
    guard(path, extra_protected=extra_protected, action='批量删除')
    norm = norm_path(path)
    for rx in _compile(A_PATH_ALLOW):
        if rx.search(norm) or rx.match(norm):
            return True
    raise GuardError(
        f'安全门拦截：{path}\n'
        f'  原因：不在 A 类可清理白名单内\n'
        f'  规则：/MIR 镜像删除与 rmtree 仅允许用于纯缓存目录（Temp/CrashDumps/pip缓存等）\n'
        f'  白名单：{A_PATH_ALLOW}')


def safe_rmtree(path, extra_protected=None):
    """受安全门保护的 rmtree。只用于 A 类白名单路径。"""
    guard_a_class(path, extra_protected=extra_protected)
    import shutil
    shutil.rmtree(path, ignore_errors=False)


def mirror_delete(target, extra_protected=None, timeout=3600):
    """robocopy /MIR 空目录镜像删除法（Windows 上删海量小文件最快，且支持 >260 长路径）。
    只用于 A 类白名单路径。"""
    guard_a_class(target, extra_protected=extra_protected)
    empty = os.path.join(tempfile.gettempdir(), '__c_drive_cleanup_empty__')
    os.makedirs(empty, exist_ok=True)
    r = subprocess.run(
        ['robocopy', empty, target, '/MIR', '/MT:16', '/R:1', '/W:1',
         '/NFL', '/NDL', '/NJH', '/NJS', '/NP'],
        capture_output=True, text=True, errors='replace', timeout=timeout)
    if r.returncode >= 8:
        raise RuntimeError(f'robocopy /MIR 失败 (exit={r.returncode})')
    try:
        os.rmdir(target)
        os.rmdir(empty)
    except OSError:
        pass
    return True


# ---------- 目录统计 ----------

def dir_snapshot(path, prune_junction=True):
    """目录快照：(文件数, 总字节, 最大 mtime)。用于检测"迁移期间源被写入"。"""
    files = 0
    total = 0
    newest = 0.0
    stack = [path]
    while stack:
        cur = stack.pop()
        try:
            with os.scandir(cur) as it:
                for e in it:
                    try:
                        if prune_junction and has_reparse(e.path):
                            continue
                        st = e.stat(follow_symlinks=False)
                        if e.is_dir(follow_symlinks=False):
                            stack.append(e.path)
                        else:
                            files += 1
                            total += st.st_size
                            if st.st_mtime > newest:
                                newest = st.st_mtime
                    except OSError:
                        pass
        except OSError:
            pass
    return files, total, newest


def dir_size(path):
    return dir_snapshot(path)[1]


def out_json(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


def die(msg, code=3):
    print(msg, file=sys.stderr)
    sys.exit(code)
