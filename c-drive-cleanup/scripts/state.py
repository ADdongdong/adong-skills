#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""迁移状态机（c-drive-cleanup skill v1.2）

为什么需要状态机（事故教训）：
  v1.1 的迁移是"复制→验证→改名→建链接"一串线性步骤，中途任何一次中断
  （用户取消、超时、异常）都会留下**半迁移状态**；而半迁移 + 应用继续往源目录写数据
  = 数据分裂。真实事故里，微信就是这样丢了 4 天聊天记录：
  源目录残留 973MB、junction 没建成，C 盘和 D 盘各有一份互不同步的数据。

  v1.2 把每一步落盘，重跑时先读状态判断"我上次走到哪了"，再决定续跑/回滚/修复，
  而不是简单地"目标已存在就跳过"（v1.1 的这个逻辑导致中断后永久卡死）。
"""
import os
import time
import datetime
import hashlib

try:
    from common import norm_path, atomic_write_json
except ImportError:  # 允许直接运行本文件做自测
    from .common import norm_path, atomic_write_json

STATE_DIR = os.path.join(os.environ.get('LOCALAPPDATA',
                                        os.path.join(os.path.expanduser('~'), 'AppData', 'Local')),
                         'c-drive-cleanup', 'state')
LOG_PATH = os.path.join(os.path.dirname(STATE_DIR), 'migrate.log')

SCHEMA = 1

# 正常流程状态
DISCOVERED = 'DISCOVERED'          # 已登记，未开始
PROCS_KILLED = 'PROCS_KILLED'      # 进程已关闭并二次校验通过
LOCK_FREE = 'LOCK_FREE'            # 目录锁探测通过（源目录静默）
BACKUPED = 'BACKUPED'              # S 类：完整只读备份已完成
COPYING = 'COPYING'                # robocopy 进行中
COPIED = 'COPIED'                  # 复制完成，待验证
VERIFIED_COPY = 'VERIFIED_COPY'    # 复制一致性校验通过
RENAMED = 'RENAMED'                # 源已改名为 _backup
JUNCTIONED = 'JUNCTIONED'          # junction 已创建，待验证
JUNCTION_OK = 'JUNCTION_OK'        # 五判据验证通过
APP_CHECKED = 'APP_CHECKED'        # 应用启动后复检通过
PURGE_PENDING = 'PURGE_PENDING'    # 备份已可清理，等待过期
PURGED = 'PURGED'                  # 备份已清理，迁移彻底完成

# 异常状态
FAILED_ROLLED_BACK = 'FAILED_ROLLED_BACK'    # 已回滚，源恢复原状
STUCK_BACKUP_PRESENT = 'STUCK_BACKUP_PRESENT'  # 卡死：数据在 _backup 里，需人工
SRC_REBUILT = 'SRC_REBUILT'                  # 应用把源路径重建为真实目录（事故形态！）

ORDER = [DISCOVERED, PROCS_KILLED, LOCK_FREE, BACKUPED, COPYING, COPIED,
         VERIFIED_COPY, RENAMED, JUNCTIONED, JUNCTION_OK, APP_CHECKED,
         PURGE_PENDING, PURGED]
ABNORMAL = [FAILED_ROLLED_BACK, STUCK_BACKUP_PRESENT, SRC_REBUILT]
ALL_STATES = ORDER + ABNORMAL

STATE_DESC = {
    DISCOVERED: '已登记，尚未开始',
    PROCS_KILLED: '相关进程已关闭并通过二次校验',
    LOCK_FREE: '源目录锁探测通过（无占用、数据静默）',
    BACKUPED: 'S类敏感数据完整备份已完成',
    COPYING: 'robocopy 复制中',
    COPIED: '复制完成，等待一致性校验',
    VERIFIED_COPY: '复制一致性校验通过',
    RENAMED: '源目录已改名为 _backup',
    JUNCTIONED: 'junction 已创建，等待五判据验证',
    JUNCTION_OK: 'junction 五判据验证通过',
    APP_CHECKED: '应用启动后复检通过',
    PURGE_PENDING: '备份可清理，等待保留期到期',
    PURGED: '备份已清理，迁移彻底完成',
    FAILED_ROLLED_BACK: '失败并已回滚，源恢复原状',
    STUCK_BACKUP_PRESENT: '⚠ 卡死：数据在 _backup 中，需人工介入',
    SRC_REBUILT: '⚠ 应用把源路径重建为真实目录，数据可能分裂',
}


def slug_for(src):
    return hashlib.sha1(norm_path(src).encode('utf-8')).hexdigest()[:12]


def state_path(src_or_id):
    if os.sep in src_or_id or ':' in src_or_id:
        sid = slug_for(src_or_id)
    else:
        sid = src_or_id
    return os.path.join(STATE_DIR, f'{sid}.json')


def now_iso():
    return datetime.datetime.now().isoformat(timespec='seconds')


def new_state(src, dst, cls='B', app='', procs=None):
    st = {
        'schema': SCHEMA,
        'id': slug_for(src),
        'src': src,
        'dst': dst,
        'backup': src + '_backup',
        'cls': cls,                      # A / B / S
        'app': app,
        'state': DISCOVERED,
        'created_at': now_iso(),
        'updated_at': now_iso(),
        'attempts': {},
        'sizes': {'src_bytes': 0, 'dst_bytes': 0, 'backup_bytes': 0},
        'procs': procs or [],
        'lock': {'probe_file': None, 'ok_at': None, 'snapshots': []},
        'verify': {'files': 0, 'bytes': 0, 'ok': False, 'at': None},
        'junction': {'is_reparse': None, 'target': None, 'sample_ok': None,
                     'write_probe': None, 'checked_at': None, 'verdict': None},
        'backup_manifest': {'path': None, 'files': 0, 'bytes': 0, 'sha256_samples': []},
        'history': [],
        'error': None,
    }
    return st


def save(st):
    st['updated_at'] = now_iso()
    atomic_write_json(state_path(st['id']), st)
    return st


def load(src_or_id):
    p = state_path(src_or_id)
    if not os.path.exists(p):
        return None
    import json
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def transition(src_or_id, to, msg='', **fields):
    """状态迁移。非法状态值直接拒绝（防止写出坏状态文件）"""
    st = load(src_or_id) if isinstance(src_or_id, str) and (
        os.sep in src_or_id or ':' in src_or_id or len(src_or_id) == 12) else src_or_id
    if st is None:
        raise ValueError(f'状态不存在: {src_or_id}')
    if to not in ALL_STATES:
        raise ValueError(f'非法状态: {to}')
    frm = st.get('state')
    st['state'] = to
    for k, v in fields.items():
        st[k] = v
    st.setdefault('history', []).append(
        {'from': frm, 'to': to, 'at': now_iso(), 'msg': msg})
    st['attempts'][to] = st['attempts'].get(to, 0) + 1
    save(st)
    return st


def log(msg, st=None, echo=True):
    line = f'[{now_iso()}] {msg}'
    if echo:
        print(line)
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except OSError:
        pass


def iter_states():
    if not os.path.isdir(STATE_DIR):
        return
    import json
    for name in sorted(os.listdir(STATE_DIR)):
        if not name.endswith('.json'):
            continue
        try:
            with open(os.path.join(STATE_DIR, name), encoding='utf-8') as f:
                yield json.load(f)
        except Exception:
            continue


def protected_paths():
    """所有状态里登记过的 src / dst / backup —— 交给 common.guard 做安全门黑名单。
    这一步是"代码层禁止删除迁移相关路径"的关键：只要迁移登记过，任何删除都会被拦。"""
    out = []
    for st in iter_states():
        for k in ('src', 'dst', 'backup'):
            if st.get(k):
                out.append(st[k])
        if st.get('backup_manifest', {}).get('path'):
            out.append(st['backup_manifest']['path'])
    return out


# ---------- 续跑决策（覆盖各种中断残留形态） ----------

def decide_resume(st):
    """根据"状态 + 磁盘实际现状"判断下一步该做什么。

    返回 dict: {action, reason, detail}
      action ∈ resume_copy | skip_copy_make_junction | verify_only |
               repair_rebuilt | rollback | abort_wait_human | done
    """
    src, dst, backup = st['src'], st['dst'], st['backup']
    state = st['state']

    src_exists = os.path.exists(src)
    dst_exists = os.path.exists(dst)
    backup_exists = os.path.exists(backup)

    # 1) 彻底完成
    if state in (PURGED, APP_CHECKED) and not backup_exists:
        return {'action': 'done', 'reason': f'状态 {state}，且备份已不存在，迁移已完成'}
    if state == PURGE_PENDING and backup_exists:
        return {'action': 'done', 'reason': '备份保留期内，无需操作（到期后可 --purge-backup）'}

    # 2) 卡死：数据在 _backup 里，源位置空着 —— 事故形态，必须人工确认后再修
    if state == STUCK_BACKUP_PRESENT:
        return {'action': 'abort_wait_human',
                'reason': '上次回滚未完成，数据停留在 _backup，需人工确认后处理',
                'detail': f'备份: {backup} (存在={backup_exists})'}

    # 3) 应用重建了真实目录（微信事故根因）
    if state == SRC_REBUILT or (src_exists and backup_exists and dst_exists):
        if src_exists and backup_exists:
            return {'action': 'repair_rebuilt',
                    'reason': '源路径被应用重建为真实目录，需把新数据并入 D 盘后重做 junction',
                    'detail': f'先合并 {src} -> {dst}（不删源），再改名重建 junction'}

    # 4) 已改名但 junction 没建 —— v1.1 在这里会永久卡死（"目标已存在就跳过"）
    if state == RENAMED or (not src_exists and backup_exists and dst_exists):
        return {'action': 'skip_copy_make_junction',
                'reason': '复制与改名已完成，只差建 junction',
                'detail': f'跳过复制，直接建 junction {src} -> {dst}'}

    # 5) 复制中断 —— 增量续跑，不再跳过
    if state in (COPYING, COPIED, BACKUPED, LOCK_FREE, PROCS_KILLED) and dst_exists:
        return {'action': 'resume_copy',
                'reason': f'状态 {state}，目标已存在部分数据 → robocopy 增量续跑（不会重复拷贝）',
                'detail': f'{src} -> {dst}'}

    # 6) 已建 junction，等验证/复检
    if state == JUNCTIONED:
        return {'action': 'verify_only', 'reason': 'junction 已建，执行五判据验证'}
    if state == JUNCTION_OK:
        return {'action': 'verify_only', 'reason': 'junction 已通过验证，建议启动应用做复检'}

    # 7) 全新开始
    if state == DISCOVERED:
        return {'action': 'start', 'reason': '未开始，从关闭进程开始'}

    return {'action': 'abort_wait_human',
            'reason': f'状态 {state} 与磁盘现状不匹配，不敢自动处理',
            'detail': f'src存在={src_exists} dst存在={dst_exists} backup存在={backup_exists}'}


def summary():
    rows = []
    for st in iter_states():
        rows.append({
            'id': st['id'],
            'app': st.get('app', ''),
            'src': st.get('src'),
            'dst': st.get('dst'),
            'state': st.get('state'),
            'desc': STATE_DESC.get(st.get('state'), ''),
            'updated_at': st.get('updated_at'),
            'error': st.get('error'),
        })
    return rows
