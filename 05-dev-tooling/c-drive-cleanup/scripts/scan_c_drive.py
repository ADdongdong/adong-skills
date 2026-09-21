#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C盘空间检测脚本（c-drive-cleanup skill 阶段1）
只读扫描，不删除不修改任何文件。
用法: python scan_c_drive.py [--quick] [--target D] [--json out.json]
  --quick: 跳过深层目录，只扫关键位置
  --target D: 指定迁移目标盘（缺省自动选空闲最大的非系统盘）
  --json out.json: 把扫描结果写入 JSON（供 migrate_junction.py / 后续阶段复用, 免重复扫描）
输出: A类(可清理) / B类(可Junction迁移) / C类(不动) / D类(个人文件) / S类(敏感数据) 分类建议

v1.2 安全加固（事故教训）:
- 新增 S 类敏感数据（聊天记录/邮件/密码库），识别后只报告不自动处理，
  迁移须走 wechat_doctor.py / 强制备份流程
- classify() 加路径限定：A/B 判定只在 AppData 顶层生效，
  避免 %USERPROFILE%\\code（个人源码）被判成迁移、%USERPROFILE%\\temp 被判成可清理
- 回收站 = 个人数据：只统计大小和条数，明细用 recycle_bin.py，禁止整体清空

坑位说明（实测）:
- Python 3.12+ 中 junction 的 entry.is_dir(follow_symlinks=False) 返回 False，
  必须用 GetFileAttributesW 的 REPARSE_POINT 属性判断 junction。
- os.walk 会穿透 junction 把 E 盘数据算进 C 盘大小，必须剪枝。
"""
import os
import sys
import json
import ctypes
import argparse
import datetime
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import expand, norm_path, S_RULES  # S_RULES 定义在 common.py（各脚本共用一份）

USER_HOME = os.path.expanduser('~')          # 当前用户的家目录（通用）
SYSTEM_DRIVE = os.environ.get('SystemDrive', 'C:').rstrip(':') + ':'
LOCAL = os.path.join(USER_HOME, 'AppData', 'Local')
ROAMING = os.path.join(USER_HOME, 'AppData', 'Roaming')

NESTED_JUNCTIONS = []  # 扫描过程中发现的嵌套 junction（如 Docker\wsl）

# ---------- 目标盘探测（通用化：不写死E盘） ----------

def _drive_free(drive):
    """查询盘符空闲字节。兼容 'E' / 'E:' / 'E:/' 三种写法（内部统一去掉冒号再拼路径）"""
    free = ctypes.c_ulonglong(0)
    kernel32 = ctypes.windll.kernel32
    letter = drive.rstrip(':').rstrip('/').rstrip('\\')
    if kernel32.GetDiskFreeSpaceExW(letter + ':/', None, None, ctypes.pointer(free)):
        return free.value
    return -1

def available_data_drives():
    """列出所有可写的非系统盘符（字母: 形式）。
    坑: GetLogicalDrives 位掩码中盘符对应 bit = ord(字母)-65（A=bit0）, 不要用 enumerate"""
    drives = ctypes.windll.kernel32.GetLogicalDrives()
    result = []
    for letter in 'DEFGHIJKLMNOPQRSTUVWXYZ':
        if drives & (1 << (ord(letter) - 65)):
            d = f'{letter}:'
            if _drive_free(d) > 0:
                result.append(d)
    return result

def pick_target_drive(arg_value=None):
    """目标盘选择规则: --target 参数(校验存在) > 空闲空间最大的非系统盘 > None(仅扫描)"""
    if arg_value:
        d = arg_value.rstrip(':').upper() + ':'
        if d in available_data_drives():
            return d
        print(f'⚠ 指定的目标盘 {d} 不存在或不可写, 回退为自动选择')
    candidates = available_data_drives()
    if not candidates:
        return None
    return max(candidates, key=lambda d: _drive_free(d))

def junction_base(drive):
    """Junction 统一目标根目录: <数据盘>:\\JunctionData"""
    return f'{drive}\\JunctionData' if drive else '(未指定数据盘)'

# ---------- 工具函数 ----------

def is_junction(path):
    """用 reparse point 属性判断 junction（不要用 is_dir(follow_symlinks=False)）"""
    FILE_ATTRIBUTE_REPARSE_POINT = 0x400
    attrs = ctypes.windll.kernel32.GetFileAttributesW(path)
    return bool(attrs & FILE_ATTRIBUTE_REPARSE_POINT) if attrs != -1 else False

def get_dir_size(path):
    """统计目录大小，但剪枝 junction 子目录（不把其他盘的数据算进来）。
    提速: scandir 迭代 + entry.stat(follow_symlinks=False).st_size
    （比 os.walk + os.path.getsize 每文件少一次系统调用，几十万小文件时差距明显）"""
    total = 0
    stack = [path]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as it:
                for entry in it:
                    try:
                        if is_junction(entry.path):
                            NESTED_JUNCTIONS.append((entry.path, _safe_readlink(entry.path)))
                        elif entry.is_dir(follow_symlinks=False):
                            stack.append(entry.path)
                        else:
                            total += entry.stat(follow_symlinks=False).st_size
                    except OSError:
                        pass
        except OSError:
            pass
    return total

def _safe_readlink(path):
    try:
        return os.readlink(path)
    except (OSError, ValueError):
        # 坑: OneDrive 占位符等 reparse point 不是符号链接, readlink 抛 ValueError 而非 OSError
        return '?'

def fmt(size):
    if size < 0:
        return '(junction)'
    if size >= 2**30:
        return f'{size/2**30:.2f} GB'
    if size >= 2**20:
        return f'{size/2**20:.0f} MB'
    return f'{size/2**10:.0f} KB'

def disk_space(drive):
    free = ctypes.c_ulonglong(0); total = ctypes.c_ulonglong(0)
    kernel32 = ctypes.windll.kernel32
    kernel32.GetDiskFreeSpaceExW(drive, None, ctypes.pointer(total), ctypes.pointer(free))
    return total.value / 2**30, free.value / 2**30

def list_dirs(base, top=30, min_size=50*2**20, workers=8):
    """列出 base 下子目录, 按大小排序; junction 单独标记(不参与top截断)。
    提速: 顶层子目录大小统计用线程池并行（IO 密集, 8 workers 约快 3-5 倍）"""
    junctions, dir_paths = [], []
    try:
        for entry in os.scandir(base):
            full = entry.path
            if is_junction(full):
                junctions.append((entry.name, -1, True))
            elif entry.is_dir():
                dir_paths.append((entry.name, full))
    except OSError:
        pass
    sizes = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(get_dir_size, full): name for name, full in dir_paths}
        for fut in as_completed(futures):
            sizes[futures[fut]] = fut.result()
    dirs_only = [(name, sizes.get(name, 0), False) for name, _ in dir_paths]
    dirs_only.sort(key=lambda x: -x[1])
    return junctions + dirs_only[:top], min_size

# ---------- 分类规则（实测沉淀, v1.2） ----------

A_CLEAN = {  # A类: 可直接清理（黄灯命令仅限本清单 + A_PATH_ALLOW 白名单路径）
    'temp': '临时文件（先看大文件内容, wsl-crashes/*.dmp 崩溃转储可放心删）',
    'wsl-crashes': 'WSL 崩溃转储（反复暴涨说明容器有问题）',
    'diagoutputdir': '诊断日志',
    'squirreltemp': '应用安装器缓存',
    'pip': 'pip 缓存 → pip cache purge（仅 Local\\pip）',
    '.cache': 'AI模型/工具缓存（删后重新下载, 需确认, 仅 AppData 下）',
}
B_JUNCTION = {  # B类: Junction 迁移安全清单
    'kingsoft': 'WPS 数据',
    'google': 'Chrome 数据（密码/书签属敏感项, 迁移前备份 Login Data）',
    'larkshell': '飞书',
    'code': 'VS Code 数据（仅 AppData 下）',
    'tdappdesktop': '通达信（隐藏占用: TencentDocs 当 user-data-dir）',
    'jetbrains': 'JetBrains（Roaming 和 Local 各一个都要迁）',
    'docker': 'Docker WSL 虚拟磁盘（若本地仅剩小日志=已迁移）',
    '.codebuddy': 'CodeBuddy CLI（需关 CodeBuddy CN）',
    '.codebuddycn': 'CodeBuddy CN 扩展（需关 CodeBuddy CN）',
    'dingtalk': '钉钉（聊天附件属敏感项, 先备份）',
    'qqex': 'QQ浏览器',
    'xmind': 'Xmind',
    'githubdesktop': 'GitHub Desktop',
    'doubao': '豆包',
    'steam': 'Steam',
    # v1.2: 'tencent' 整包已移除 —— Roaming\\Tencent 含 40+ 子应用（QQNT/WXWork/TIM/WeDrive），
    # 整包迁移粒度太粗是微信事故诱因之一。微信走 wechat_doctor.py，其余按子应用逐个评估
}
C_KEEP = {  # C类: 不动
    'microsoft': '系统组件/Edge/OneDrive',
    'windows': '系统核心',
    'nvidia': 'GPU驱动',
    'programs': '应用安装目录（应卸载重装到数据盘而非junction）',
    'anaconda3': '路径硬编码 → 用 conda clean --all',
    '.workbuddy': 'Agent运行自身目录（运行中被锁, 需独立脚本+退出应用）',
    'packages': '系统组件包',
    'tencent': '腾讯系数据根（含微信/QQ聊天库, 禁止整包迁移, 微信走 wechat_doctor.py）',
}

def classify(name, full_path=''):
    """分类优先级: C > S > A > B > ?（v1.2 起带路径限定）
    坑（事故教训）: 之前按目录名全等匹配、不限路径，导致
    %USERPROFILE%\\code（个人源码）被判成 B 类建议迁移、
    %USERPROFILE%\\temp 被判成 A 类建议清理。现在 A/B 只在 AppData 下生效。"""
    key = name.lower()
    norm = norm_path(full_path) if full_path else ''
    in_appdata = ('\\appdata\\local' in norm or '\\appdata\\roaming' in norm)

    # S 类最先于 A/B：哪怕目录名叫 temp，只要里面是聊天库就不能按缓存处理
    if norm:
        for pat, _note in S_RULES:
            if re.search(pat, norm):
                return 'S'

    if key in C_KEEP:
        return 'C'
    if key in A_CLEAN:
        # 路径限定: A 类判定只在 AppData 下生效（家目录下的 temp/.cache 可能是个人目录）
        return 'A' if in_appdata else '?'
    if key in B_JUNCTION:
        return 'B' if in_appdata else '?'
    return '?'

# ---------- 回收站概览（v1.2: 只统计, 不清空） ----------

def recycle_bin_overview():
    """统计各盘 $Recycle.Bin 大小。v1.2 事故教训: 回收站是个人数据重灾区
    （一起事故里 14647 个个人文件被整体清空），本脚本只报占用，
    明细列表用 recycle_bin.py，清理必须逐条确认。"""
    import string
    items = []
    for letter in string.ascii_uppercase:
        drive = f'{letter}:'
        if not os.path.exists(drive + '\\'):
            continue
        rb = os.path.join(drive, '$Recycle.Bin')
        if not os.path.isdir(rb):
            continue
        size = get_dir_size(rb)
        if size > 2**20:  # 超过 1MB 才报
            items.append({'drive': drive, 'bytes': size, 'size': fmt(size)})
    return items

# ---------- 敏感数据探测（v1.2: S 类只报告, 不自动处理） ----------

def sensitive_probe():
    """探测常见敏感数据位置（微信聊天库/Outlook/密码库）。
    只做 exists + 大小统计，任何清理/迁移动作都须走专门流程。"""
    found = []
    # 微信 4.x: config ini 指定真实数据根（实测: 单行路径, 编码可能是 utf-8/utf-16/gbk）
    ini_dir = expand(r'%APPDATA%\Tencent\xwechat\config')
    ini_roots = []
    if os.path.isdir(ini_dir):
        try:
            for fn in os.listdir(ini_dir):
                if not fn.endswith('.ini'):
                    continue
                raw = open(os.path.join(ini_dir, fn), 'rb').read()
                for enc in ('utf-8', 'utf-16', 'gbk'):
                    try:
                        line = raw.decode(enc).strip().splitlines()
                        if line and line[0]:
                            ini_roots.append(line[0])
                            break
                    except (UnicodeDecodeError, UnicodeError):
                        continue
        except OSError:
            pass
    candidates = [
        ('微信4.x账号数据根(xwechat_files)', expand(r'%USERPROFILE%\xwechat_files')),
        ('微信3.x数据(WeChat Files)', os.path.join(USER_HOME, 'Documents', 'WeChat Files')),
        ('微信4.x运行时+配置', expand(r'%APPDATA%\Tencent\xwechat')),
        ('微信旧版数据', expand(r'%APPDATA%\Tencent\WeChat')),
        ('Outlook邮件', expand(r'%LOCALAPPDATA%\Microsoft\Outlook')),
        ('Chrome密码库', expand(r'%LOCALAPPDATA%\Google\Chrome\User Data\Default\Login Data')),
    ]
    for label, p in [(f'微信数据根(来自config ini)', r) for r in ini_roots] + candidates:
        try:
            if p and os.path.exists(p):
                sz = get_dir_size(p) if os.path.isdir(p) else os.path.getsize(p)
                on_c = norm_path(p).startswith(norm_path(SYSTEM_DRIVE + '\\'))
                found.append({'label': label, 'path': p, 'bytes': sz, 'size': fmt(sz),
                              'on_system_drive': on_c})
        except OSError:
            continue
    return found

# ---------- 已知文件夹检测（D类: 用户个人静态文件） ----------

KNOWN_FOLDERS = {
    'Desktop(桌面)':   '{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}',
    'Documents(文档)': '{FDD39AD0-238F-46AF-ADB4-6C85480369C7}',
    'Downloads(下载)': '{374DE290-123F-4565-9164-39C4925E467B}',
    'Pictures(图片)':  '{33E28130-4E1E-4676-835A-98395C3BC3BB}',
    'Music(音乐)':     '{4BD8D571-6D19-48D3-BE97-422220080E43}',
    'Videos(视频)':    '{18989B1D-99B5-455B-841C-AB7C74E4DDFC}',
}

def known_folder_paths():
    """用 SHGetKnownFolderPath 获取已知文件夹真实位置。
    坑: 注册表 HKCU...User Shell Folders 可能为空, 不要依赖它"""
    import uuid

    def known_path(fid_str):
        class GUID(ctypes.Structure):
            _fields_ = [('Data1', ctypes.c_ulong), ('Data2', ctypes.c_ushort),
                        ('Data3', ctypes.c_ushort), ('Data4', ctypes.c_ubyte * 8)]
        u = uuid.UUID(fid_str)
        g = GUID(u.time_low, u.time_mid, u.time_hi_version, (ctypes.c_ubyte * 8)(*u.bytes[8:]))
        buf = ctypes.c_void_p()
        r = ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(g), 0, None, ctypes.byref(buf))
        if r != 0:
            return None
        path = ctypes.wstring_at(buf)
        ctypes.windll.ole32.CoTaskMemFree(buf)
        return path

    return {label: known_path(fid) for label, fid in KNOWN_FOLDERS.items()}

# ---------- 主流程 ----------

def main():
    ap = argparse.ArgumentParser(description='C盘空间检测（只读, 不删不改）')
    ap.add_argument('--quick', action='store_true', help='跳过深层目录, 只扫关键位置')
    ap.add_argument('--target', default=None, help='指定迁移目标盘, 如 D')
    ap.add_argument('--json', dest='json_out', default=None, help='扫描结果写入 JSON 文件（复用免重扫）')
    args = ap.parse_args()
    quick = args.quick
    target_drive = pick_target_drive(args.target) if args.target else pick_target_drive()

    report = {
        'generated_at': datetime.datetime.now().isoformat(timespec='seconds'),
        'system_drive': SYSTEM_DRIVE,
        'quick': quick,
        'target_drive': target_drive,
    }

    total, free = disk_space(SYSTEM_DRIVE)
    print('=' * 62)
    print(f'{SYSTEM_DRIVE}盘: 总 {total:.0f}GB | 剩余 {free:.1f}GB')
    if target_drive:
        print(f'迁移目标盘: {target_drive} (剩余 {_drive_free(target_drive)/2**30:.1f}GB)')
        print(f'Junction 目标根目录: {junction_base(target_drive)}')
    else:
        print('⚠ 未找到可用的数据盘, 本次仅输出扫描结果')
    data_drives = available_data_drives()
    print(f'可用数据盘: {", ".join(data_drives) if data_drives else "(无)"}')
    print('=' * 62)
    report['disk'] = {'total_gb': round(total, 1), 'free_gb': round(free, 1),
                      'data_drives': data_drives}

    scan_targets = [
        ('AppData\\Local', LOCAL),
        ('AppData\\Roaming', ROAMING),
    ]
    if not quick:
        scan_targets.append(('用户主目录', USER_HOME))

    buckets = {'A': [], 'B': [], 'C': [], 'S': [], '?': []}
    junctions_found = []
    report['scans'] = []

    for label, base in scan_targets:
        print(f'\n### {label} ###')
        dirs, min_size = list_dirs(base)
        entries = []
        for name, size, junc in dirs:
            full = os.path.join(base, name)
            if junc:
                junctions_found.append((full, _safe_readlink(full)))
                entries.append({'name': name, 'bytes': -1, 'junction': True})
                continue
            print(f'  {fmt(size):>10}  {name}')
            entries.append({'name': name, 'bytes': size, 'junction': False})
            if size >= min_size:
                cat = classify(name, full)
                buckets[cat].append((fmt(size), name, full, size))
        report['scans'].append({'label': label, 'base': base, 'entries': entries})

    report['buckets'] = {cat: [{'size': b[0], 'bytes': b[3], 'name': b[1], 'path': b[2]}
                               for b in items] for cat, items in buckets.items()}

    print('\n' + '=' * 62)
    print('已知文件夹位置(D类: 报告后征求用户选择, 确认前不处理):')
    kf = known_folder_paths()
    kf_report = []
    for label, path in kf.items():
        if not path:
            print(f'  {label:<16} (获取失败)')
            kf_report.append({'label': label, 'path': None})
            continue
        on_c = path.upper().startswith(str(SYSTEM_DRIVE).upper())
        size = get_dir_size(path) if on_c and os.path.exists(path) else None
        size_str = fmt(size) if size is not None else '-'
        tag = f'← 在{SYSTEM_DRIVE}盘 {size_str:>10}  → 官方法: 右键→属性→位置→移动' if on_c else '(不在系统盘)'
        print(f'  {label:<16} {path}  {tag}')
        kf_report.append({'label': label, 'path': path, 'on_system_drive': on_c,
                          'bytes': size})
    report['known_folders'] = kf_report

    # v1.2: 回收站概览（只统计大小, 不清空; 明细用 recycle_bin.py）
    print('\n' + '=' * 62)
    print('回收站占用（个人数据! 只统计不清空, 明细: python recycle_bin.py --scan）:')
    rb_items = recycle_bin_overview()
    if rb_items:
        for it in rb_items:
            print(f'  {it["drive"]}盘回收站: {it["size"]:>10}')
    else:
        print('  (无 ≥1MB 的回收站)')
    report['recycle_bin'] = rb_items

    # v1.2: 敏感数据探测（S 类只报告; 迁移须走 wechat_doctor.py / 强制备份流程）
    print('\n' + '=' * 62)
    print('敏感数据探测（S类: 聊天记录/邮件/密码库, 丢失不可逆, 禁止自动清理/迁移）:')
    sens = sensitive_probe()
    if sens:
        for it in sens:
            loc = '在C盘' if it['on_system_drive'] else '不在C盘(无需处理)'
            print(f'  {it["size"]:>10}  {it["label"]}  {loc}')
            print(f'{" ":>12}  {it["path"]}')
        on_c = [it for it in sens if it['on_system_drive']]
        if on_c:
            print('  ⚠ C盘上有敏感数据: 微信用 wechat_doctor.py --detect 专项处理;')
            print('    其他敏感项迁移前必须先做完整只读备份（见 SKILL.md S类规范）')
    else:
        print('  (未发现)')
    report['sensitive'] = sens

    print('\n' + '=' * 62)
    print('已存在的 Junction（数据已在其他盘, 跳过）:')
    for full, target in junctions_found:
        print(f'  {full}\n    -> {target}')
    if NESTED_JUNCTIONS:
        # 只显示跨盘的嵌套 junction（指向本盘其他位置的是系统/UWP重定向, 属于噪音）
        def _norm(t):
            return t.replace('\\\\?\\', '').lower()
        cross = [(f, t) for f, t in NESTED_JUNCTIONS if not _norm(t).startswith('c:')]
        if cross:
            print('嵌套 Junction（父目录内已迁移到其他盘的部分, 其数据实际不在C盘）:')
            for full, target in cross:
                print(f'  {full}\n    -> {target}')
    if not junctions_found and not NESTED_JUNCTIONS:
        print('  (无)')
    report['existing_junctions'] = [{'path': f, 'target': t}
                                    for f, t in junctions_found]
    report['nested_junctions'] = [{'path': f, 'target': t} for f, t in NESTED_JUNCTIONS]

    for cat, title, action in [
        ('A', 'A类: 可直接清理（删除不影响使用, 需确认后执行; /MIR与rmtree仅限白名单路径）', '清理'),
        ('B', 'B类: 建议Junction迁移到数据盘（迁移后不影响使用, 迁移走状态机）', '迁移'),
        ('S', 'S类: 敏感数据（聊天记录/邮件/密码库, 丢失不可逆 —— 只报告, 不自动处理）', '专项流程'),
        ('C', 'C类: 不建议动', '保持'),
        ('?', '待判断（需查看内容后决定）', '查看'),
    ]:
        print(f'\n### {title} ###')
        if not buckets[cat]:
            print('  (无)')
        for size_str, name, full, _bytes in buckets[cat]:
            note = (A_CLEAN.get(name.lower()) or B_JUNCTION.get(name.lower())
                    or C_KEEP.get(name.lower()) or '')
            if cat == 'S':
                for pat, s_note in S_RULES:
                    if re.search(pat, norm_path(full)):
                        note = s_note
                        break
            print(f'  {size_str:>10}  {name:<28} {note}')
            if cat in ('A', 'B'):
                print(f'{" ":>12}→ {action}: {full}')
                if cat == 'B' and target_drive:
                    print(f'{" ":>12}→ Junction 目标: {junction_base(target_drive)}\\{name}')
            if cat == 'S':
                print(f'{" ":>12}→ 禁止直接清理/迁移。微信走 wechat_doctor.py; 其他先完整备份')

    # 容量校验: 目标盘空闲空间 vs B类待迁移总量(需>1.2倍余量, 迁移过程中源数据还在)
    if target_drive and buckets['B']:
        need = sum(b[3] for b in buckets['B'])
        avail = _drive_free(target_drive)
        ratio = avail / need if need else 0
        print('\n' + '=' * 62)
        print(f'容量校验: B类待迁移 {need/2**30:.1f}GB | 目标盘 {target_drive} 空闲 {avail/2**30:.1f}GB (需≥1.2倍)')
        if ratio >= 1.2:
            print(f'✓ 容量充足 (余量 {ratio:.1f} 倍)')
        else:
            print(f'✗ 容量不足! 建议只迁移最大的前几项, 或先做A类清理腾出目标盘空间')
            # 按大小降序列出可优先迁移的项
            ranked = sorted(buckets['B'], key=lambda x: -x[3])
            print('  建议优先迁移:', ', '.join(f'{n}({s})' for s, n, _, _ in ranked[:3]))
        report['capacity_check'] = {'need_bytes': need, 'avail_bytes': avail,
                                    'ratio': round(ratio, 2), 'sufficient': ratio >= 1.2}

    print('\n提示: A类清理前必须列出清单并经用户确认（/MIR、rmtree 仅限 A_PATH_ALLOW 白名单）;')
    print('     B类用 python migrate_junction.py --dirs 短名 --dry-run 预演后执行;')
    print('     S类敏感数据一律走专项流程, 禁止直接删/迁; 回收站用 recycle_bin.py 列明细逐条确认。')

    if args.json_out:
        with open(args.json_out, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f'扫描结果已写入: {args.json_out}')


if __name__ == '__main__':
    main()
