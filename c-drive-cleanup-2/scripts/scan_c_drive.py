#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C盘空间检测脚本（c-drive-cleanup skill 阶段1）
只读扫描，不删除不修改任何文件。
用法: python scan_c_drive.py [--quick] [--target D]
  --quick: 跳过深层目录，只扫关键位置
  --target D: 指定迁移目标盘（缺省自动选空闲最大的非系统盘）
输出: A类(可清理) / B类(可Junction迁移) / C类(不动) 分类建议

坑位说明（实测）:
- Python 3.12+ 中 junction 的 entry.is_dir(follow_symlinks=False) 返回 False，
  必须用 GetFileAttributesW 的 REPARSE_POINT 属性判断 junction。
- os.walk 会穿透 junction 把 E 盘数据算进 C 盘大小，必须剪枝。
"""
import os
import sys
import ctypes

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
    """统计目录大小，但剪枝 junction 子目录（不把其他盘的数据算进来）"""
    total = 0
    for root, dirs, files in os.walk(path):
        pruned = []
        for d in dirs:
            full = os.path.join(root, d)
            if is_junction(full):
                NESTED_JUNCTIONS.append((full, _safe_readlink(full)))
            else:
                pruned.append(d)
        dirs[:] = pruned
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total

def _safe_readlink(path):
    try:
        return os.readlink(path)
    except OSError:
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

def list_dirs(base, top=30, min_size=50*2**20):
    """列出 base 下子目录, 按大小排序; junction 单独标记(不参与top截断)"""
    junctions, dirs_only = [], []
    try:
        for entry in os.scandir(base):
            full = entry.path
            if is_junction(full):
                junctions.append((entry.name, -1, True))
            elif entry.is_dir():
                dirs_only.append((entry.name, get_dir_size(full), False))
    except OSError:
        pass
    dirs_only.sort(key=lambda x: -x[1])
    return junctions + dirs_only[:top], min_size

# ---------- 分类规则（实测沉淀） ----------

A_CLEAN = {  # A类: 可直接清理
    'temp': '临时文件（先看大文件内容, wsl-crashes/*.dmp 崩溃转储可放心删）',
    'wsl-crashes': 'WSL 崩溃转储（反复暴涨说明容器有问题）',
    'diagoutputdir': '诊断日志',
    'squirreltemp': '应用安装器缓存',
    'pip': 'pip 缓存 → pip cache purge',
    '.cache': 'AI模型/工具缓存（删后重新下载, 需确认）',
}
B_JUNCTION = {  # B类: Junction 迁移安全清单
    'kingsoft': 'WPS 数据',
    'google': 'Chrome 数据',
    'tencent': 'QQ/微信/企微（隐藏占用: WeType/WXWork/TencentDocs）',
    'larkshell': '飞书',
    'code': 'VS Code 数据',
    'tdappdesktop': '通达信（隐藏占用: TencentDocs 当 user-data-dir）',
    'jetbrains': 'JetBrains（Roaming 和 Local 各一个都要迁）',
    'docker': 'Docker WSL 虚拟磁盘（若本地仅剩小日志=已迁移）',
    '.codebuddy': 'CodeBuddy CLI（需关 CodeBuddy CN）',
    '.codebuddycn': 'CodeBuddy CN 扩展（需关 CodeBuddy CN）',
    'dingtalk': '钉钉',
    'qqex': 'QQ浏览器',
    'xmind': 'Xmind',
    'githubdesktop': 'GitHub Desktop',
    'doubao': '豆包',
    'steam': 'Steam',
}
C_KEEP = {  # C类: 不动
    'microsoft': '系统组件/Edge/OneDrive',
    'windows': '系统核心',
    'nvidia': 'GPU驱动',
    'programs': '应用安装目录（应卸载重装到数据盘而非junction）',
    'anaconda3': '路径硬编码 → 用 conda clean --all',
    '.workbuddy': 'Agent运行自身目录（运行中被锁, 需独立脚本+退出应用）',
    'packages': '系统组件包',
}

def classify(name):
    key = name.lower()
    if key in C_KEEP:
        return 'C'
    if key in A_CLEAN:
        return 'A'
    if key in B_JUNCTION:
        return 'B'
    return '?'

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
    quick = '--quick' in sys.argv
    # --target D 形式指定目标盘；缺省自动选空闲最大的非系统盘
    target_drive = None
    if '--target' in sys.argv:
        idx = sys.argv.index('--target')
        if idx + 1 < len(sys.argv):
            target_drive = pick_target_drive(sys.argv[idx + 1])
    else:
        target_drive = pick_target_drive()

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

    scan_targets = [
        ('AppData\\Local', LOCAL),
        ('AppData\\Roaming', ROAMING),
    ]
    if not quick:
        scan_targets.append(('用户主目录', USER_HOME))

    buckets = {'A': [], 'B': [], 'C': [], '?': []}
    junctions_found = []

    for label, base in scan_targets:
        print(f'\n### {label} ###')
        dirs, min_size = list_dirs(base)
        for name, size, junc in dirs:
            full = os.path.join(base, name)
            if junc:
                junctions_found.append((full, _safe_readlink(full)))
                continue
            print(f'  {fmt(size):>10}  {name}')
            if size >= min_size:
                cat = classify(name)
                buckets[cat].append((fmt(size), name, full))

    print('\n' + '=' * 62)
    print('已知文件夹位置(D类: 报告后征求用户选择, 确认前不处理):')
    kf = known_folder_paths()
    for label, path in kf.items():
        if not path:
            print(f'  {label:<16} (获取失败)')
            continue
        on_c = path.upper().startswith(str(SYSTEM_DRIVE).upper())
        size_str = fmt(get_dir_size(path)) if on_c and os.path.exists(path) else '-'
        tag = f'← 在{SYSTEM_DRIVE}盘 {size_str:>10}  → 官方法: 右键→属性→位置→移动' if on_c else '(不在系统盘)'
        print(f'  {label:<16} {path}  {tag}')

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

    for cat, title, action in [
        ('A', 'A类: 可直接清理（删除不影响使用, 需确认后执行）', '清理'),
        ('B', 'B类: 建议Junction迁移到数据盘（迁移后不影响使用）', '迁移'),
        ('C', 'C类: 不建议动', '保持'),
        ('?', '待判断（需查看内容后决定）', '查看'),
    ]:
        print(f'\n### {title} ###')
        if not buckets[cat]:
            print('  (无)')
        for size, name, full in buckets[cat]:
            note = A_CLEAN.get(name.lower(), B_JUNCTION.get(name.lower(), C_KEEP.get(name.lower(), '')))
            print(f'  {size:>10}  {name:<28} {note}')
            if cat in ('A', 'B'):
                print(f'{" ":>12}→ {action}: {full}')
                if cat == 'B' and target_drive:
                    print(f'{" ":>12}→ Junction 目标: {junction_base(target_drive)}\\{name}')

    # 容量校验: 目标盘空闲空间 vs B类待迁移总量(需>1.2倍余量, 迁移过程中源数据还在)
    if target_drive and buckets['B']:
        def _to_bytes(s):
            num, unit = s.split()
            mult = {'GB': 2**30, 'MB': 2**20, 'KB': 2**10}[unit]
            return float(num) * mult
        need = sum(_to_bytes(s) for s, _, _ in buckets['B'])
        avail = _drive_free(target_drive)
        ratio = avail / need if need else 0
        print('\n' + '=' * 62)
        print(f'容量校验: B类待迁移 {need/2**30:.1f}GB | 目标盘 {target_drive} 空闲 {avail/2**30:.1f}GB (需≥1.2倍)')
        if ratio >= 1.2:
            print(f'✓ 容量充足 (余量 {ratio:.1f} 倍)')
        else:
            print(f'✗ 容量不足! 建议只迁移最大的前几项, 或先做A类清理腾出目标盘空间')
            # 按大小降序列出可优先迁移的项
            ranked = sorted(buckets['B'], key=lambda x: -_to_bytes(x[0]))
            print('  建议优先迁移:', ', '.join(f'{n}({s})' for s, n, _ in ranked[:3]))

    print('\n提示: A类清理前必须列出清单并经用户确认; B类按 SKILL.md 阶段4 八步流程执行。')

if __name__ == '__main__':
    main()
