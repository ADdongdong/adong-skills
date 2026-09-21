#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Junction 批量迁移脚本 v1.2（c-drive-cleanup skill 阶段4）

v1.1 → v1.2 安全加固（事故驱动, 详见 SKILL.md 事故复盘）:
  一起真实事故: 微信迁移时进程没杀干净 → 源目录持续被写 → 数据分裂, 聊天记录丢 4 天。
  v1.1 的缺陷: 完整路径入参不杀进程 / 进程名失真 / "目标已存在就跳过"致中断后卡死 /
  验证与改名之间有分钟级写入窗口 / junction 单点判定误报 / 回滚可能把源卡在 _backup 态。

  v1.2 的对策（每一条对应一个事故环节）:
  1. 状态机（state.py）: 每步落盘, 中断后重跑按"状态+磁盘现状"续跑/回滚, 不再卡死
  2. kill_and_confirm: 按 PID 杀（名称清单 + 路径/命令行关键字双判据）, 轮询 20s 确认归零
  3. probe_lock: 目录锁探测（试写+改名往返+3次静默快照）, 不静默绝不复制
  4. check_junction 五判据: reparse/realpath/穿透/写入探针/dst非空, UNKNOWN 不算通过
  5. 回滚永远先 rename(backup, src), 永不先删任何东西; 失败记 STUCK_BACKUP_PRESENT → exit 4
  6. S 类敏感路径直接拒绝迁移（微信走 wechat_doctor.py）
  7. --delete-backup 四道门, 且禁止 /MOVE /MIR 出现在迁移路径上（全脚本无一个破坏性删除）

用法:
  python migrate_junction.py --dirs kingsoft,google --target E            # 迁移
  python migrate_junction.py --dirs kingsoft,google --dry-run             # 预演
  python migrate_junction.py --dirs kingsoft --plan                       # 查看计划/续跑建议
  python migrate_junction.py --dirs kingsoft --delete-backup --i-know kingsoft --older-than 7

退出码: 0 成功 / 1 无可迁移项 / 2 部分失败 / 3 安全门拦截 / 4 状态卡死待人工
"""
import os
import sys
import json
import time
import ctypes
import shutil
import datetime
import argparse
import subprocess
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (norm_path, expand, has_reparse, safe_readlink, guard,
                    GuardError, StuckError, is_sensitive, dir_snapshot, dir_size)
import state as st

USER_HOME = os.path.expanduser('~')
LOCAL = os.path.join(USER_HOME, 'AppData', 'Local')
ROAMING = os.path.join(USER_HOME, 'AppData', 'Roaming')
SYSTEM_DRIVE = os.environ.get('SystemDrive', 'C:').rstrip(':') + ':'

LOG_LINES = []
RESULTS = []   # 结构化结果, --json 输出用


def log(msg):
    line = f'[{datetime.datetime.now().strftime("%H:%M:%S")}] {msg}'
    print(line)
    LOG_LINES.append(line)
    st.log(msg, echo=False)  # 同步写运行日志（立即落盘, 中断不丢）


# ---------- 短名 -> (定位候选目录, 进程名清单[fallback], 关键字[主判据]) ----------
# 注意: 进程名随版本变（事故教训: 字典里写 WeChat.exe, 真名是 Weixin.exe）,
# 所以名称清单只是 fallback, 主判据是"路径/命令行含关键字"的 PID 匹配。
# 名称标 (待实测) 的表示未经本机验证, 只作辅助。
B_APPS = {
    'kingsoft':      ([os.path.join(ROAMING, 'kingsoft')],
                      ['wps.exe', 'wpscloudsvr.exe', 'wpscenter.exe', 'wpspdf.exe', 'et.exe', 'wpp.exe'],
                      ['kingsoft', 'wps']),
    'google':        ([os.path.join(LOCAL, 'Google')],
                      ['chrome.exe'], ['google', 'chrome']),
    'larkshell':     ([os.path.join(ROAMING, 'LarkShell')],
                      ['Feishu.exe', 'Lark.exe'], ['lark', 'feishu']),
    'code':          ([os.path.join(ROAMING, 'Code')],
                      ['Code.exe'], ['code']),
    'tdappdesktop':  ([os.path.join(ROAMING, 'TDAppDesktop')],
                      ['tdw.exe', 'TdxW.exe'], ['tdx', 'tdapp', 'tencentdocs']),
    'jetbrains':     ([os.path.join(ROAMING, 'JetBrains'), os.path.join(LOCAL, 'JetBrains')],
                      ['idea64.exe', 'pycharm64.exe', 'webstorm64.exe'], ['jetbrains']),
    'docker':        ([os.path.join(LOCAL, 'Docker', 'wsl')],
                      ['Docker Desktop.exe', 'com.docker.backend.exe'], ['docker']),
    'dingtalk':      ([os.path.join(ROAMING, 'DingTalk')],
                      ['DingTalk.exe'], ['dingtalk']),
    'qqex':          ([os.path.join(ROAMING, 'QQEX')],
                      ['qqbrowser.exe'], ['qqex', 'qqbrowser']),   # 待实测
    'xmind':         ([os.path.join(ROAMING, 'Xmind')],
                      ['Xmind.exe'], ['xmind']),
    'githubdesktop': ([os.path.join(ROAMING, 'GitHubDesktop')],
                      ['GitHubDesktop.exe'], ['github']),
    'doubao':        ([os.path.join(ROAMING, 'Doubao')],
                      ['Doubao.exe'], ['doubao']),
    'steam':         ([os.path.join(ROAMING, 'Steam'), os.path.join(LOCAL, 'Steam')],
                      ['steam.exe'], ['steam']),
    # 'tencent' 整包已移除（事故教训: Roaming\Tencent 含 40+ 子应用, 整包迁移粒度太粗;
    # 微信必须走 wechat_doctor.py —— 它会读 config ini 找到真实聊天库位置）
}

# 解释器进程: 关键字匹配命令行时必须排除（否则脚本自己的参数会误伤自己）
INTERPRETER_EXE = ('python', 'pythonw', 'powershell', 'pwsh', 'cmd', 'node',
                   'conhost', 'bash', 'sh', 'git')


# ---------- 盘符工具 ----------

def drive_free(drive):
    letter = drive.rstrip(':').rstrip('/').rstrip('\\')
    free = ctypes.c_ulonglong(0)
    if ctypes.windll.kernel32.GetDiskFreeSpaceExW(letter + ':/', None, None, ctypes.pointer(free)):
        return free.value
    return -1


def available_data_drives():
    drives = ctypes.windll.kernel32.GetLogicalDrives()
    return [f'{l}:' for l in 'DEFGHIJKLMNOPQRSTUVWXYZ'
            if drives & (1 << (ord(l) - 65)) and drive_free(f'{l}:') > 0]


def pick_target(arg_value=None):
    if arg_value:
        d = arg_value.rstrip(':').upper() + ':'
        if d in available_data_drives():
            return d
        print(f'⚠ 指定目标盘 {d} 不存在或不可写, 回退自动选择')
    cands = available_data_drives()
    return max(cands, key=lambda d: drive_free(d)) if cands else None


def fmt(size):
    if size is None or size < 0:
        return '-'
    if size >= 2**30:
        return f'{size/2**30:.2f} GB'
    if size >= 2**20:
        return f'{size/2**20:.1f} MB'
    return f'{size/2**10:.0f} KB'


# ---------- 验证（单遍并发双树比对, 保留 v1.1 成果） ----------

def verify_trees(src, dst):
    def collect(base):
        entries, total = set(), 0
        stack = [base]
        while stack:
            cur = stack.pop()
            try:
                with os.scandir(cur) as it:
                    for e in it:
                        try:
                            if has_reparse(e.path):
                                continue
                            if e.is_dir(follow_symlinks=False):
                                stack.append(e.path)
                            else:
                                stt = e.stat(follow_symlinks=False)
                                rel = os.path.relpath(e.path, base).lower()
                                entries.add((rel, stt.st_size))
                                total += stt.st_size
                        except OSError:
                            pass
            except OSError:
                pass
        return entries, total

    with ThreadPoolExecutor(max_workers=2) as pool:
        fs, ds = pool.submit(collect, src), pool.submit(collect, dst)
        src_e, src_b = fs.result()
        dst_e, dst_b = ds.result()

    missing = list(src_e - dst_e)[:10]
    extra = list(dst_e - src_e)[:10]
    ok = not missing and not extra
    detail = [f'  缺失: {m[0]} ({m[1]}B)' for m in missing] + [f'  多余: {e[0]}' for e in extra]
    return ok, len(src_e), len(dst_e), src_b, dst_b, detail


# ---------- 进程管理（v1.2: 按 PID + 双判据 + 二次确认） ----------

def list_procs(keywords, names):
    """用 Get-CimInstance 列出目标进程 (pid, name, path)。
    主判据: ExecutablePath 含关键字; 辅助: 映像名在 names 里。
    坑: 命令行关键字匹配会误伤脚本自己（参数里就有目录名），解释器进程全部排除。"""
    ps = ("Get-CimInstance Win32_Process | "
          "Select-Object ProcessId,Name,ExecutablePath | ConvertTo-Json -Compress")
    try:
        r = subprocess.run(['powershell', '-NoProfile', '-Command', ps],
                           capture_output=True, text=True, errors='replace', timeout=60)
        data = json.loads(r.stdout) if r.stdout.strip() else []
    except Exception:
        return []
    if isinstance(data, dict):
        data = [data]
    out = []
    for p in data:
        try:
            pid = int(p.get('ProcessId', 0))
        except (TypeError, ValueError):
            continue
        name = (p.get('Name') or '').lower()
        path = (p.get('ExecutablePath') or '')
        if not name or pid == os.getpid():
            continue
        if name.split('.')[0] in INTERPRETER_EXE:
            continue
        if name in names or any(kw in path.lower() for kw in keywords):
            out.append({'pid': pid, 'name': name, 'path': path})
    return out


def kill_and_confirm(keywords, names, timeout=30, dry=False):
    """杀进程并二次确认。返回 (found, confirmed_dead)。
    事故教训: v1.1 杀完只 sleep 0.5s 不复查; 这里轮询直到全部退出或超时。
    超时仍有残留 → confirmed_dead=False → 调用方必须中止, 不进入复制。"""
    procs = list_procs(keywords, names)
    if not procs:
        return [], True
    log(f'  发现进程: {", ".join(p["name"] + "(" + str(p["pid"]) + ")" for p in procs[:8])}'
        + ('...' if len(procs) > 8 else ''))
    if dry:
        return procs, False  # dry-run 不杀也不确认
    for p in procs:
        r = subprocess.run(['taskkill', '/F', '/PID', str(p['pid']), '/T'],
                           capture_output=True, text=True, errors='replace')
        log(f'  taskkill {p["name"]}({p["pid"]}): {"ok" if r.returncode == 0 else r.stderr.strip()[:60]}')
    deadline = time.time() + timeout
    while time.time() < deadline:
        alive = list_procs(keywords, names)
        if not alive:
            log(f'  ✓ 进程已全部退出（二次确认通过）')
            return procs, True
        time.sleep(1)
    leftover = list_procs(keywords, names)
    log(f'  ✗ {len(leftover)} 个进程 {timeout}s 内未能退出: '
        + ', '.join(p['name'] for p in leftover[:5]))
    log('  → 中止本目录迁移（绝不带占用复制, 这是事故的第一道防线）')
    return procs, False


def probe_lock(path, quiet_checks=3, interval=1):
    """目录锁探测（v1.2 核心）: 三步全过才算"静默可迁"。
    ① 试写+改名往返 ② 目录改名往返（等2s再改回, 杀不干净的进程会立刻暴露）
    ③ 连续 3 次快照 (文件数,字节,最新mtime) 完全一致
    返回 (ok, 说明)"""
    # ① 试写
    try:
        probe = os.path.join(path, '.__locktest__')
        with open(probe, 'w') as f:
            f.write('x')
        os.rename(probe, probe + '2')
        os.rename(probe + '2', probe)
        os.remove(probe)
    except OSError as e:
        return False, f'试写失败（目录被占用）: {e}'
    # ② 改名往返（try/finally 保证一定改回去; 标志位记录改回结果, 不在 finally 里 return —— 会吞异常）
    renamed = path + '.__probe__'
    rename_back_ok = True
    try:
        os.rename(path, renamed)
        time.sleep(2)
    except OSError as e:
        return False, f'目录改名失败（有进程持有句柄）: {e}'
    finally:
        if os.path.exists(renamed) and not os.path.exists(path):
            try:
                os.rename(renamed, path)
            except OSError:
                rename_back_ok = False
    if not rename_back_ok:
        return False, f'⚠ 目录改名后未能改回! 残留: {renamed}（需人工恢复）'
    # ③ 静默快照
    snaps = []
    for i in range(quiet_checks):
        snaps.append(dir_snapshot(path))
        if i < quiet_checks - 1:
            time.sleep(interval)
    if len(set(snaps)) != 1:
        return False, f'目录仍在被写入（{quiet_checks} 次快照不一致）: {snaps}'
    return True, f'静默确认: {snaps[0]}'


# ---------- Junction 五判据（v1.2, 杜绝"先判失效后判生效"翻转） ----------

def check_junction(src, dst):
    """五判据交叉验证。返回 (verdict, detail)
    verdict: OK / BROKEN / UNKNOWN（UNKNOWN 不算通过! 需人工判断）
    事故教训: v1.1 只查 reparse 位 —— 占位符/去重/DFS 同为 0x400, 卷瞬时不可达返回 -1,
    这就是 agent 两分钟内判定翻转的成因; 且 dst 空串时"穿透访问"恒真。"""
    d = {}
    # ① reparse 位（带重试, None=不确定）
    d['reparse'] = has_reparse(src)
    # ② realpath 解析后必须等于 dst（修"dst 空串恒真"）
    try:
        real = norm_path(os.path.realpath(src))
        d['realpath'] = real
        d['realpath_eq_dst'] = bool(dst) and real == norm_path(dst)
    except OSError:
        d['realpath_eq_dst'] = False
    # ③ 穿透列举 + stat
    try:
        with os.scandir(src) as it:
            first = next(iter(it), None)
        d['through_ok'] = first is not None and first.stat(follow_symlinks=False) is not None
    except OSError:
        d['through_ok'] = False
    # ④ 写入探针: 在 src 建临时文件, 确认它真实落在 dst 下面
    probe_name = '.c-drive-cleanup-probe'
    try:
        with open(os.path.join(src, probe_name), 'w') as f:
            f.write(str(time.time()))
        landed = os.path.exists(os.path.join(dst, probe_name))
        d['write_probe'] = landed
        try:
            os.remove(os.path.join(src, probe_name))
        except OSError:
            pass
    except OSError:
        d['write_probe'] = False
    # ⑤ dst 非空
    try:
        d['dst_files'] = sum(1 for _ in os.scandir(dst) if _.is_file())
    except OSError:
        d['dst_files'] = 0

    if d['reparse'] is None:
        return 'UNKNOWN', d            # 卷瞬时不可达等, 不敢下结论
    if not d['reparse'] or not d['realpath_eq_dst']:
        return 'BROKEN', d
    if d['dst_files'] == 0:
        return 'BROKEN', d             # 空链接（dst 被清空）也是坏的
    if not d['write_probe']:
        return 'BROKEN', d
    if not d['through_ok']:
        return 'UNKNOWN', d            # 空目录穿透无法证实, 不算通过
    return 'OK', d


# ---------- robocopy（加 timeout; 失败把半成品 dst 改名隔离, 不删除） ----------

def robocopy(src, dst, dry=False, timeout=3600):
    """两遍 robocopy: 第1遍全量, 第2遍增量补齐（同命令只拷差异, 秒级）。
    幂等: 中断后重跑自动增量续跑（robocopy 天然只拷差异）—— 这是状态机续跑的基础。"""
    cmd = ['robocopy', src, dst, '/E', '/COPY:DAT', '/R:3', '/W:5', '/MT:16',
           '/NFL', '/NDL', '/NJH', '/NJS', '/NP']
    if dry:
        log(f'  [dry-run] robocopy {" -> ".join(cmd[1:3])} /E /MT:16 (共2遍, timeout={timeout}s)')
        return True
    for i in (1, 2):
        log(f'  robocopy 第{i}遍...')
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, errors='replace',
                               timeout=timeout)
        except subprocess.TimeoutExpired:
            log(f'  ✗ robocopy 第{i}遍超时 ({timeout}s)')
            quarantine_dst(dst)
            return False
        if r.returncode >= 8:
            log(f'  ✗ robocopy 失败 (exit={r.returncode})')
            quarantine_dst(dst)
            return False
    return True


def quarantine_dst(dst):
    """复制失败后把半成品隔离（改名, 不删除 —— 删除交给确认后的人工/后续流程）"""
    if not os.path.exists(dst):
        return
    quarantine = dst + f'.__corrupt_{datetime.datetime.now():%Y%m%d%H%M%S}'
    try:
        os.rename(dst, quarantine)
        log(f'  半成品已隔离: {quarantine}（确认无用后可手动删除）')
    except OSError as e:
        log(f'  ⚠ 半成品隔离失败: {e}（重跑时 robocopy 会增量补齐, 不影响安全）')


# ---------- Junction 操作 ----------

def make_junction(src, dst_target, dry=False):
    if dry:
        log(f'  [dry-run] 将创建 Junction: {src} -> {dst_target}')
        return True
    r = subprocess.run(['cmd', '/c', 'mklink', '/J', src, dst_target],
                       capture_output=True, text=True, errors='replace')
    if r.returncode == 0:
        return True
    log(f'  mklink 失败({r.stdout.strip()[:60]}), 回退 PowerShell...')
    r2 = subprocess.run(['powershell', '-NoProfile', '-Command',
                         f"New-Item -ItemType Junction -Path '{src}' -Target '{dst_target}' | Out-Null"],
                        capture_output=True, text=True, errors='replace')
    return r2.returncode == 0


def remove_junction_link(path):
    """只删链接本身, 绝不碰目标数据（os.rmdir 对 junction 只移除 reparse point）"""
    try:
        os.rmdir(path)
        return True
    except OSError:
        return False


def rollback(src, backup, st_doc=None, reason=''):
    """回滚。铁律（修审计第11条）: 先恢复数据, 再清理现场; 永不先删任何东西。
    顺序: ①src 若是 junction → 只删链接 ②rename(backup, src)（数据回家）
    ③改回去失败 → STUCK_BACKUP_PRESENT → raise StuckError(exit 4), 人工介入。"""
    log(f'  回滚开始: {reason}')
    if os.path.lexists(src) and has_reparse(src):
        if remove_junction_link(src):
            log(f'  已移除 junction 链接: {src}（目标数据 {st_doc["dst"] if st_doc else "?"} 未动）')
        else:
            log(f'  ⚠ junction 链接移除失败: {src}')
    if not os.path.exists(src) and os.path.exists(backup):
        try:
            os.rename(backup, src)
            log(f'  ✓ 数据已恢复: {backup} -> {src}')
            if st_doc:
                st.transition(st_doc, st.FAILED_ROLLED_BACK, msg=f'回滚: {reason}')
            return True
        except OSError as e:
            if st_doc:
                st.transition(st_doc, st.STUCK_BACKUP_PRESENT, msg=f'回滚失败: {e}', error=str(e))
            raise StuckError(
                f'回滚失败, 数据停在 {backup}, 源位置 {src} 为空!\n'
                f'  原因: {e}\n'
                f'  人工恢复命令: ren "{backup}" "{os.path.basename(src)}"\n'
                f'  （先关闭占用源路径的进程再执行）')
    log('  无需数据恢复（源位置数据完整）')
    if st_doc:
        st.transition(st_doc, st.FAILED_ROLLED_BACK, msg=f'回滚: {reason}')
    return True


# ---------- 核心: 迁移单个目录（状态机驱动） ----------

def migrate_one(src, target, dry=False, timeout=3600, app='', allow_sensitive=False):
    """迁移一个目录。全程状态机落盘, 任何一步失败都可安全重跑。
    allow_sensitive: 仅限 wechat_doctor.py 在完成强制备份后传入, 普通调用禁止。
    返回 dict(结构化结果)"""
    name = os.path.basename(src)
    dst = os.path.join(f'{target}\\JunctionData', name)
    backup = src + '_backup'
    t0 = time.time()
    result = {'src': src, 'dst': dst, 'ok': False, 'state': None, 'msg': ''}

    # S 类守卫: 敏感路径绝不走通用迁移（微信走 wechat_doctor.py）
    if is_sensitive(src) and not allow_sensitive:
        msg = (f'S类敏感数据, 拒绝通用迁移: {src}\n'
               f'  聊天记录/邮件/密码库必须走专项流程（wechat_doctor.py / 强制备份规范）')
        log(f'=== {name} ===')
        log(f'  ✗ {msg}')
        result['msg'] = msg
        raise GuardError(msg)

    # 状态加载/新建 + 续跑决策
    st_doc = st.load(src)
    if st_doc is None:
        st_doc = st.new_state(src, dst, cls='B', app=app)
        st.save(st_doc)
    decision = st.decide_resume(st_doc)
    log(f'=== {name} ===')
    log(f'  状态: {st_doc["state"]} | 续跑决策: {decision["action"]} ({decision["reason"]})')
    result['state'] = st_doc['state']

    if decision['action'] == 'abort_wait_human':
        result['msg'] = decision['reason']
        RESULTS.append(result)
        raise StuckError(f'{name}: {decision["reason"]} {decision.get("detail", "")}')
    if decision['action'] == 'done':
        log('  ⊘ 已完成, 跳过')
        result['ok'], result['msg'] = True, '已完成'
        RESULTS.append(result)
        return result
    if decision['action'] == 'repair_rebuilt':
        result['msg'] = '源路径被应用重建为真实目录（事故形态）, 请用 --plan 查看修复步骤后人工确认'
        RESULTS.append(result)
        raise StuckError(f'{name}: SRC_REBUILT —— 修复动作涉及合并数据, 需人工确认后按 SKILL.md 修复流程执行')

    if dry:
        log(f'  [dry-run] 预演: {src} -> {dst}')
        log(f'  [dry-run] 将执行: 关进程(确认) -> 锁探测 -> 两遍robocopy -> 校验 -> 改名 -> 建junction -> 五判据')
        result['ok'], result['msg'] = True, '预演完成'
        RESULTS.append(result)
        return result

    # ---- 阶段1: 关进程 + 二次确认 ----
    if st_doc['state'] in (st.DISCOVERED,):
        keywords, names = proc_ident_for(src)
        procs, dead = kill_and_confirm(keywords, names)
        st_doc['procs'] = [p['name'] for p in procs]
        if not dead:
            result['msg'] = '进程未能全部退出, 中止'
            st.transition(st_doc, st.DISCOVERED, msg='进程未退出, 中止')
            RESULTS.append(result)
            return result
        st.transition(st_doc, st.PROCS_KILLED, msg=f'已关闭 {len(procs)} 个进程')

    # ---- 阶段2: 目录锁探测 ----
    if st_doc['state'] == st.PROCS_KILLED:
        ok, why = probe_lock(src)
        if not ok:
            result['msg'] = f'锁探测未通过: {why}'
            log(f'  ✗ {why}')
            log('  → 中止（不进入复制）。处理: 找出隐藏占用进程后重跑; 已复制部分会在下次增量补齐')
            st.transition(st_doc, st.PROCS_KILLED, msg=f'锁探测失败: {why}')
            RESULTS.append(result)
            return result
        log(f'  ✓ {why}')
        st.transition(st_doc, st.LOCK_FREE, msg=why)

    # ---- 阶段3: 复制（增量幂等, 中断可续跑） ----
    if st_doc['state'] in (st.LOCK_FREE, st.COPYING, st.COPIED):
        size = dir_size(src)
        log(f'  源大小: {fmt(size)}')
        if drive_free(target) < size * 1.1:
            result['msg'] = f'目标盘空间不足 (需≥{fmt(size*1.1)})'
            st.transition(st_doc, st.LOCK_FREE, msg='目标盘空间不足, 中止')
            RESULTS.append(result)
            return result
        st.transition(st_doc, st.COPYING, msg='开始复制')
        if not robocopy(src, dst, timeout=timeout):
            result['msg'] = 'robocopy 失败（半成品已隔离）, 可重跑增量续传'
            RESULTS.append(result)
            return result
        st.transition(st_doc, st.COPIED, msg='复制完成')

    # ---- 阶段4: 复制一致性校验 ----
    if st_doc['state'] == st.COPIED:
        ok, ns, nd, bs, bd, detail = verify_trees(src, dst)
        log(f'  验证: 源 {ns}文件/{fmt(bs)} vs 目标 {nd}文件/{fmt(bd)} -> {"✓ 一致" if ok else "✗ 不一致"}')
        for d_line in detail:
            log(d_line)
        if not ok:
            result['msg'] = '复制校验不一致, 中止（不改名!）'
            st.transition(st_doc, st.COPIED, msg='校验不一致, 等待重跑补齐')
            RESULTS.append(result)
            return result
        st.transition(st_doc, st.VERIFIED_COPY, msg='复制校验通过')

    # ---- 阶段4.5: RENAMED 残留续跑（复制+改名已完成, 只差建 junction; v1.1 在这里永久卡死）----
    if st_doc['state'] == st.RENAMED:
        if not os.path.exists(backup):
            rollback(src, backup, st_doc, 'RENAMED 但 backup 不存在, 异常')
            result['msg'] = 'RENAMED 态但备份缺失, 已按异常处理'
            RESULTS.append(result)
            return result
        if not make_junction(src, dst):
            rollback(src, backup, st_doc, '建 junction 失败（续跑）')
            result['msg'] = '建 junction 失败, 已回滚'
            RESULTS.append(result)
            return result
        st.transition(st_doc, st.JUNCTIONED, msg='junction 已创建（RENAMED 续跑）')

    # ---- 阶段5: 改名 + 建 junction（锁探测把这里的写入窗口压到秒级） ----
    if st_doc['state'] == st.VERIFIED_COPY:
        # 复检一次锁（离阶段2可能已过数分钟, 重新静默确认）
        ok, why = probe_lock(src, quiet_checks=2)
        if not ok:
            result['msg'] = f'改名前复检失败: {why}'
            log(f'  ✗ {why} → 中止, 数据未动, 重跑即可')
            RESULTS.append(result)
            return result
        try:
            os.rename(src, backup)
            st.transition(st_doc, st.RENAMED, msg=f'改名 {name} -> {name}_backup')
        except OSError as e:
            result['msg'] = f'改名被拒(有占用): {e}'
            log(f'  ✗ 改名被拒: {e}')
            log('  → 数据未动。找出占用进程后重跑（复制已完成, 重跑只需几秒）')
            RESULTS.append(result)
            return result
        if not make_junction(src, dst):
            rollback(src, backup, st_doc, '建 junction 失败')
            result['msg'] = '建 junction 失败, 已回滚'
            RESULTS.append(result)
            return result
        st.transition(st_doc, st.JUNCTIONED, msg='junction 已创建')

    # ---- 阶段6: 五判据验证 ----
    if st_doc['state'] == st.JUNCTIONED:
        verdict, jd = check_junction(src, dst)
        st_doc['junction'] = {**jd, 'checked_at': st.now_iso(), 'verdict': verdict}
        st.save(st_doc)
        log(f'  五判据: reparse={jd["reparse"]} realpath={jd["realpath_eq_dst"]} '
            f'穿透={jd["through_ok"]} 写入探针={jd["write_probe"]} dst文件={jd["dst_files"]} → {verdict}')
        if verdict != 'OK':
            if verdict == 'BROKEN':
                rollback(src, backup, st_doc, f'junction 验证 {verdict}')
                result['msg'] = f'junction 验证 {verdict}, 已回滚'
            else:
                result['msg'] = 'junction 验证 UNKNOWN（不算通过）, 已回滚（UNKNOWN 时宁可回滚重来）'
                rollback(src, backup, st_doc, 'junction 验证 UNKNOWN')
            RESULTS.append(result)
            return result
        st.transition(st_doc, st.JUNCTION_OK, msg='五判据全部通过')
        log(f'  ✓ Junction 建好且五判据通过, 耗时 {time.time()-t0:.0f}s (备份保留在 {backup})')
        log('  下一步: 启动应用实测正常后, 待保留期满可用 --delete-backup 清理备份')

    result['ok'] = True
    RESULTS.append(result)
    return result


def proc_ident_for(src):
    """按源路径推断 (关键字, 进程名清单)。完整路径也能解析（修审计第1条: v1.1 返回空列表）"""
    base = os.path.basename(src).lower()
    parent = os.path.basename(os.path.dirname(norm_path(src))).lower()
    for key, (_dirs, names, kws) in B_APPS.items():
        if base == key or base.startswith(key) or key in parent:
            return kws, [n.lower() for n in names]
    # 未知应用: 用目录名自身作关键字（按路径/命令行匹配）—— 总比一个都不杀强
    return [base], []


# ---------- 删备份（四道门） ----------

def delete_backups(items, i_know, older_than_days, dry=False):
    """四道门全过才删:
    ①状态=JUNCTION_OK及之后 ②备份与dst比对一致 ③--i-know 指定了该目录末段 ④备份已过保留期
    且用 common.guard(allow=...) 放行 —— 只放行本道门, 不影响其他保护。"""
    ok_list = []
    for b in items:
        log(f'--- 检查备份: {b} ---')
        src = b[:-len('_backup')] if b.endswith('_backup') else b
        st_doc = st.load(src) or st.load(b)
        # 门①状态
        if not st_doc or st_doc['state'] not in (st.JUNCTION_OK, st.APP_CHECKED, st.PURGE_PENDING):
            log(f'  ✗ 门①失败: 状态 {st_doc["state"] if st_doc else "(无状态)"} 不满足（须 JUNCTION_OK 及之后）')
            continue
        # 门②内容比对
        dst = st_doc['dst']
        if not os.path.exists(dst):
            log(f'  ✗ 门②失败: junction 目标 {dst} 不存在, 绝不能删备份')
            continue
        ok, ns, nd, bs, bd, detail = verify_trees(b, dst)
        if not ok:
            log(f'  ✗ 门②失败: 备份与目标不一致（{len(detail)}条差异）, 绝不能删备份')
            for line in detail[:5]:
                log(line)
            continue
        # 门③ --i-know
        tail = os.path.basename(norm_path(b)).lower()
        known = [x.strip().lower() for x in (i_know or '').split(',') if x.strip()]
        if tail not in known:
            log(f'  ✗ 门③失败: 未用 --i-know {os.path.basename(norm_path(b))} 显式确认')
            continue
        # 门④保留期
        age_days = (datetime.datetime.now() - datetime.datetime.fromtimestamp(
            os.path.getmtime(b))).days
        if age_days < older_than_days:
            log(f'  ✗ 门④失败: 备份仅 {age_days} 天, 未到保留期 {older_than_days} 天')
            continue
        log(f'  ✓ 四道门通过（状态={st_doc["state"]}, 一致, 已确认, {age_days}天）')
        ok_list.append((b, st_doc, age_days))

    deleted = 0
    for b, st_doc, age in ok_list:
        if dry:
            log(f'  [dry-run] 将删除 {b} ({fmt(dir_size(b))}, {age}天)')
            continue
        size = dir_size(b)
        # guard 放行的只是"这一个"备份路径; 已知文件夹/回收站等红灯保护仍然生效
        guard(b, extra_protected=st.protected_paths(), action='删除备份',
              allow=[norm_path(b)])
        try:
            shutil.rmtree(b)
            log(f'  ✓ 已删除备份 {b} ({fmt(size)})')
            st.transition(st_doc, st.PURGED, msg='备份已清理')
            deleted += 1
        except OSError as e:
            log(f'  ✗ 删除失败（文件被占用?）: {e} —— 备份保留, 不强制')
            continue
    return deleted


# ---------- 目录解析 ----------

def resolve_dirs(dir_args, override_procs=None):
    """短名/完整路径 -> [(路径, 关键字, 进程名)]。完整路径也解析进程（修 v1.1 缺陷）"""
    result = []
    for item in dir_args:
        item = item.strip().strip('"')
        if os.sep in item or ':' in item:
            if not os.path.isdir(item):
                print(f'⚠ 路径不存在, 跳过: {item}')
                continue
            kws, names = proc_ident_for(item)
            result.append((item, kws, names))
            continue
        key = item.lower()
        if key not in B_APPS:
            print(f'⚠ 未知短名 "{item}"。可选: {", ".join(sorted(B_APPS))}；或给完整路径'
                  f'（微信数据请用 wechat_doctor.py）')
            continue
        candidates, names, kws = B_APPS[key]
        if override_procs and key in override_procs:
            names = override_procs[key]
        for c in candidates:
            if os.path.isdir(c):
                result.append((c, kws, [n.lower() for n in names]))
    return result


# ---------- 主流程 ----------

def main():
    ap = argparse.ArgumentParser(description='Junction 批量迁移 v1.2（状态机+安全门）')
    ap.add_argument('--dirs', required=True, help='逗号分隔的短名或完整路径')
    ap.add_argument('--target', default=None, help='目标盘符, 缺省自动选空闲最大非系统盘')
    ap.add_argument('--dry-run', action='store_true', help='预演, 不做任何修改')
    ap.add_argument('--plan', action='store_true', help='只显示计划与续跑建议, 不执行')
    ap.add_argument('--delete-backup', action='store_true', help='删除备份（须过四道门）')
    ap.add_argument('--i-know', default='', help='--delete-backup 的显式确认: 目录末段名, 如 --i-know kingsoft')
    ap.add_argument('--older-than', type=int, default=7, help='备份保留期天数（默认7, 门④）')
    ap.add_argument('--processes', default=None, help='覆盖进程名映射: "kingsoft=wps.exe;google=chrome.exe"')
    ap.add_argument('--timeout', type=int, default=3600, help='单次 robocopy 超时秒数')
    ap.add_argument('--json', dest='json_out', action='store_true', help='末尾输出 JSON 结果')
    args = ap.parse_args()

    override = {}
    if args.processes:
        for seg in args.processes.split(';'):
            if '=' in seg:
                k, v = seg.split('=', 1)
                override[k.strip().lower()] = [x.strip() for x in v.split(',') if x.strip()]

    log(f'==== Junction 批量迁移 v1.2 {datetime.datetime.now():%Y-%m-%d %H:%M} ====')
    if args.dry_run:
        log('** DRY-RUN 预演模式, 不会修改任何文件 **')

    try:
        target = pick_target(args.target)
        if not target:
            print('✗ 没有可用数据盘, 无法迁移')
            sys.exit(1)
        log(f'目标盘: {target} (空闲 {fmt(drive_free(target))}), Junction 根: {target}\\JunctionData')

        jobs = resolve_dirs(args.dirs.split(','), override)

        # --plan / --delete-backup 单独处理
        if args.delete_backup:
            backups = []
            for src, _k, _n in jobs:
                b = src + '_backup'
                if os.path.exists(b):
                    backups.append(b)
            if not backups:
                print('没有可删的备份')
                sys.exit(0)
            n = delete_backups(backups, args.i_know, args.older_than, args.dry_run)
            log(f'==== 删备份完成: {n}/{len(backups)} ====')
            sys.exit(0 if n == len(backups) else 2)

        # --plan: 打印每个目录的现状 + 续跑建议
        if args.plan:
            print('\n迁移计划 / 续跑建议:')
            for src, kws, names in jobs:
                st_doc = st.load(src)
                cur = st_doc['state'] if st_doc else '(无状态, 全新)'
                dec = st.decide_resume(st_doc) if st_doc else {'action': 'start', 'reason': '全新迁移'}
                print(f'  {src}')
                print(f'    状态: {cur} | 建议: {dec["action"]} — {dec["reason"]}')
                print(f'    进程判据: 关键字={kws} / 名称={names[:5]}')
            sys.exit(0)

        jobs = [j for j in jobs if not has_reparse(j[0])]
        if not jobs:
            print('没有待迁移目录')
            sys.exit(1)

        # 预检清单 + 容量
        total = 0
        print('\n待迁移清单:')
        for src, kws, names in jobs:
            size = dir_size(src)
            total += size
            print(f'  {fmt(size):>10}  {src}  [进程判据: {",".join(kws[:3])}...]')
        if drive_free(target) < total * 1.2:
            print(f'✗ 目标盘容量不足: 待迁 {fmt(total)} × 1.2 > 空闲 {fmt(drive_free(target))}')
            sys.exit(1)

        # 逐目录迁移（每个目录独立状态机; 一个失败不影响其他）
        for src, _kws, _names in jobs:
            migrate_one(src, target, args.dry_run, timeout=args.timeout)

    except GuardError as e:
        log(f'安全门拦截 (exit 3): {e}')
        RESULTS.append({'ok': False, 'msg': f'GuardError: {e}'})
        _finish(args, exit_code=3)
    except StuckError as e:
        log(f'状态卡死 (exit 4): {e}')
        RESULTS.append({'ok': False, 'msg': f'StuckError: {e}'})
        _finish(args, exit_code=4)

    log('==== 汇总 ====')
    ok_n = sum(1 for r in RESULTS if r.get('ok'))
    for r in RESULTS:
        log(f'  {"✓" if r.get("ok") else "✗"} {os.path.basename(r["src"])}: {r["msg"] or r.get("state", "")}')
    log(f'成功 {ok_n}/{len(RESULTS)}')
    _finish(args, exit_code=0 if ok_n == len(RESULTS) else 2)


def _finish(args, exit_code):
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            f'migrate_log_{datetime.datetime.now():%Y%m%d}.txt')
    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write('\n'.join(LOG_LINES) + '\n')
    except OSError:
        pass
    if args.json_out:
        print(json.dumps({'exit_code': exit_code,
                          'results': RESULTS,
                          'states': st.summary()}, ensure_ascii=False, indent=2))
    print(f'\n日志: {log_path}')
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
