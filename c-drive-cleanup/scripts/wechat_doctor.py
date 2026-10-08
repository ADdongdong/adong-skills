#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""微信专项脚本 v1.2（c-drive-cleanup skill）—— 微信数据的检测/迁移/复检/修复

为什么微信必须专项处理（事故复盘）:
  一起真实事故里, 通用迁移脚本把 Roaming\\Tencent\\xwechat 迁到 D 盘, 结果丢 4 天聊天记录:
  - 微信 4.x 的聊天库（db_storage/message_N.db）根本不在 Roaming 下,
    而由 %APPDATA%\\Tencent\\xwechat\\config\\51*.ini 指定（可为任意盘任意路径）
  - 只杀 Weixin.exe/WeChatAppEx.exe 不够, 后台还有 wechat-backend.exe/WeChatDataAnalysis.exe
    （进程名随版本变 —— 所以本脚本用"路径/命令行含关键字"作主判据, 名称只是 fallback）
  - 聊天库是加密 SQLite, 两份数据无法合并 —— 分裂 = 丢失, 没有后悔药

  因此本脚本的铁律:
  1. --migrate 前先做**完整只读备份**, 备份校验通过才开始迁移（宁可多占空间）
  2. 迁移顺序: 先聊天数据根（含 db_storage）→ 再运行时目录, 一次只迁一个
  3. ini 里数据根不在 C 盘 → 直接报告"聊天库不在 C 盘", 禁止迁移 db
  4. 进程按 PID 杀 + 20s 轮询确认归零 + 目录锁探测, 任一不过就不复制

用法:
  python wechat_doctor.py --detect                 # 检测全部微信数据位置与状态
  python wechat_doctor.py --migrate --target E     # 强制备份后迁移（一次一个目录）
  python wechat_doctor.py --check                  # 迁移后复检（五步: 穿透/归属/可读/写入/静默）
  python wechat_doctor.py --repair --yes           # SRC_REBUILT 修复（需 --yes 显式确认）
  python wechat_doctor.py --purge-backup --older-than 30 --i-know wechat   # 清备份

退出码: 0 成功 / 2 部分失败 / 3 安全门拦截 / 4 需人工
"""
import os
import sys
import json
import time
import glob
import datetime
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (norm_path, expand, has_reparse, safe_readlink, guard,
                    GuardError, StuckError, dir_snapshot, atomic_write_json)
import state as st
import migrate_junction as mj

USER_HOME = os.path.expanduser('~')
SYSTEM_DRIVE = os.environ.get('SystemDrive', 'C:').rstrip(':') + ':'

# 微信 4.x 全部已知数据位置（实测沉淀; 顺序 = 建议迁移顺序）
WECHAT_PATHS = [
    ('账号数据根(xwechat_files, 含聊天库db_storage)', lambda: os.path.join(USER_HOME, 'xwechat_files')),
    ('运行时+配置(Roaming\\Tencent\\xwechat)',       lambda: expand(r'%APPDATA%\Tencent\xwechat')),
    ('3.x旧版数据(Documents\\WeChat Files)',         lambda: os.path.join(USER_HOME, 'Documents', 'WeChat Files')),
    ('旧版数据(Roaming\\Tencent\\WeChat)',           lambda: expand(r'%APPDATA%\Tencent\WeChat')),
    ('临时文件(Temp\\WeChat Files)',                 lambda: expand(r'%LOCALAPPDATA%\Temp\WeChat Files')),
]

# 进程 fallback 名单。标"待实测"的未经本机验证（本机只见到 Weixin/WeChatAppEx/wetype 系列,
# wechat-backend/WeChatDataAnalysis 是事故机上出现的）—— 名称会随版本变, 主判据是路径关键字
WECHAT_PROC_NAMES = [
    'weixin.exe', 'weixinext.exe', 'weixinupdate.exe', 'crashpad_handler.exe',
    'wechatappex.exe', 'wechat-backend.exe', 'wechatdataanalysis.exe',
    'wechatplayer.exe', 'wechatocr.exe', 'wechatutility.exe',   # 后三个: 待实测
]
WECHAT_KEYWORDS = ['weixin', 'wechat', 'xwechat']

RESULTS = {'detect': [], 'migrate': [], 'check': [], 'actions': []}


# ---------- 数据根探测 ----------

def find_data_root():
    """从 config\\51*.ini 读微信 4.x 真实数据根。返回 (root 或 None, ini路径)。
    实测: ini 内容为单行路径; 编码可能是 utf-8 / utf-16 / gbk（多分支兼容, 不赌编码）"""
    ini_dir = expand(r'%APPDATA%\Tencent\xwechat\config')
    if not os.path.isdir(ini_dir):
        return None, None
    for ini in glob.glob(os.path.join(ini_dir, '51*.ini')):
        try:
            raw = open(ini, 'rb').read()
        except OSError:
            continue
        for enc in ('utf-8', 'utf-16', 'gbk'):
            try:
                text = raw.decode(enc)
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        else:
            continue
        for line in text.splitlines():
            line = line.strip()
            if line and os.sep in line:
                return line, ini
    return None, None


def enum_paths():
    """枚举所有存在的微信数据位置。ini 根仅在系统盘时纳入（不在 C 盘的无需处理）"""
    found = []
    root, ini = find_data_root()
    if root and os.path.exists(root):
        on_c = norm_path(root).startswith(norm_path(SYSTEM_DRIVE + '\\'))
        # ini 根下面找 xwechat_files 子目录（实际聊天库所在）
        target = root if os.path.basename(norm_path(root)).lower() == 'xwechat_files' \
            else os.path.join(root, 'xwechat_files')
        found.append({'label': '数据根(来自config ini, 含聊天库)', 'path': target,
                      'ini': ini, 'on_system_drive': on_c and os.path.exists(target),
                      'has_db': os.path.isdir(os.path.join(target, 'db_storage'))
                                or any(os.path.isdir(os.path.join(target, w, 'db_storage'))
                                       for w in _subdirs(target))})
    for label, fn in WECHAT_PATHS:
        p = fn()
        if os.path.exists(p):
            found.append({'label': label, 'path': p, 'ini': None,
                          'on_system_drive': norm_path(p).startswith(norm_path(SYSTEM_DRIVE + '\\')),
                          'has_db': os.path.isdir(os.path.join(p, 'db_storage'))
                                    or any(os.path.isdir(os.path.join(p, w, 'db_storage'))
                                           for w in _subdirs(p))})
    return found


def _subdirs(p):
    try:
        return [e.name for e in os.scandir(p) if e.is_dir()]
    except OSError:
        return []


def wechat_procs():
    """当前微信相关进程（主判据: 路径含关键字; fallback: 名称清单）。复用 migrate_junction 的实现"""
    return mj.list_procs(WECHAT_KEYWORDS, set(WECHAT_PROC_NAMES))


# ---------- 复检（五步） ----------

def check_db(src=None, dst=None):
    """迁移后复检五步（--check）:
    ①穿透能 stat 到 db_storage 下的 .db ②realpath 前缀 == dst（数据真的在新盘）
    ③打开 .db 读 4096 字节成功 ④写入探针 ⑤C盘原路径 mtime 采样 —— 若变化 = SRC_REBUILT"""
    if src is None or dst is None:
        # 从状态机里找微信相关迁移记录
        for s in st.iter_states():
            if 'xwechat' in norm_path(s.get('src', '')) or 'wechat' in norm_path(s.get('src', '')):
                src, dst = s['src'], s['dst']
                break
    if not src or not dst:
        return {'ok': False, 'msg': '没有找到微信迁移记录（先 --migrate）'}

    out = {'src': src, 'dst': dst, 'steps': {}}
    # ① 穿透 stat 聊天库
    db = _find_message_db(src)
    out['steps']['stat_db'] = bool(db) and os.path.exists(db)
    out['db'] = db
    # ② realpath 归属
    try:
        real = norm_path(os.path.realpath(src))
        out['steps']['realpath_is_dst'] = real == norm_path(dst)
    except OSError:
        out['steps']['realpath_is_dst'] = False
    # ③ 可读性
    try:
        with open(db, 'rb') as f:
            f.read(4096)
        out['steps']['db_readable'] = True
    except OSError:
        out['steps']['db_readable'] = False
    # ④ 写入探针
    probe = os.path.join(src, '.wechat-doctor-probe')
    try:
        with open(probe, 'w') as f:
            f.write('x')
        out['steps']['write_probe'] = os.path.exists(os.path.join(dst, '.wechat-doctor-probe'))
        os.remove(probe)
    except OSError:
        out['steps']['write_probe'] = False
    # ⑤ 静默采样: 记录 C盘原路径 mtime 基准; 若上次有基准且变了 → SRC_REBUILT
    st_doc = st.load(src)
    mtime_now = os.path.getmtime(src) if os.path.exists(src) else None
    prev = (st_doc or {}).get('db_mtime_base')
    out['steps']['src_mtime'] = mtime_now
    if prev is not None and mtime_now is not None and abs(mtime_now - prev) > 2:
        out['src_rebuilt'] = True
        if st_doc:
            st.transition(st_doc, st.SRC_REBUILT, msg='check_db 发现 C 盘原路径被重建/写入')
    else:
        out['src_rebuilt'] = False
        if st_doc and mtime_now is not None:
            st_doc['db_mtime_base'] = mtime_now
            st.save(st_doc)

    out['ok'] = (out['steps']['stat_db'] and out['steps']['realpath_is_dst']
                 and out['steps']['db_readable'] and out['steps']['write_probe']
                 and not out['src_rebuilt'])
    return out


def _find_message_db(base):
    """找 db_storage 下的聊天库文件（message_*.db / 任意 .db）"""
    for root, dirs, files in os.walk(base):
        if 'db_storage' in root and any(f.endswith('.db') for f in files):
            for f in files:
                if f.endswith('.db'):
                    return os.path.join(root, f)
    return None


# ---------- 迁移（强制备份优先） ----------

def do_migrate(target, dry=False, timeout=3600):
    """微信迁移。顺序: 聊天数据根 → 运行时, 一次一个。每个目录: 强制备份→关进程→锁探测→迁移"""
    paths = enum_paths()
    jobs = [p for p in paths if p['on_system_drive']]
    if not jobs:
        print('✓ 微信聊天数据均不在 C 盘, 无需迁移')
        for p in paths:
            print(f'  {p["label"]}: {p["path"]}')
        return 0

    killed_confirmed = False
    for job in jobs:
        src = job['path']
        name = os.path.basename(norm_path(src))
        dst = os.path.join(f'{target}\\JunctionData', name)
        # ---- 强制备份（只读复制 + 校验, 校验不过绝不开始迁移） ----
        backup_root = os.path.join(f'{target}\\JunctionData', 'wechat_backup')
        backup = os.path.join(backup_root, f'{name}_{datetime.datetime.now():%Y%m%d%H%M%S}')
        log(f'=== {job["label"]} ===')
        log(f'  源: {src}')
        log(f'  强制备份: {backup}')
        if not dry:
            # 关进程 + 二次确认（整个微信批次只做一次, 一次关干净）
            if not killed_confirmed:
                procs, dead = mj.kill_and_confirm(WECHAT_KEYWORDS, set(WECHAT_PROC_NAMES),
                                                  timeout=40)
                if not dead:
                    log('  ✗ 微信进程未能全部退出, 中止（绝不带占用复制聊天库）')
                    RESULTS['migrate'].append({'src': src, 'ok': False, 'msg': '进程未退出'})
                    continue
                killed_confirmed = True
            ok, why = mj.probe_lock(src)
            if not ok:
                log(f'  ✗ 锁探测失败: {why} → 中止')
                RESULTS['migrate'].append({'src': src, 'ok': False, 'msg': why})
                continue
            # 备份 = 单遍全量 + 增量补一遍（与迁移复制同一命令形态, 只读不动源）
            if not mj.robocopy(src, backup, timeout=timeout):
                log('  ✗ 备份复制失败 → 迁移取消（源数据未动）')
                RESULTS['migrate'].append({'src': src, 'ok': False, 'msg': '备份失败'})
                continue
            bok, ns, nd, bs, bd, detail = mj.verify_trees(src, backup)
            if not bok:
                log('  ✗ 备份校验不一致 → 迁移取消（宁可不做, 不可做错）')
                for d in detail[:5]:
                    log(d)
                RESULTS['migrate'].append({'src': src, 'ok': False, 'msg': '备份校验失败'})
                continue
            log(f'  ✓ 备份完成并校验通过: {ns}文件/{fmt_b(bs)}')
        # ---- 正式迁移（allow_sensitive=True: 备份已完成, 放行 S 类） ----
        try:
            r = mj.migrate_one(src, target, dry=dry, timeout=timeout,
                               app='wechat', allow_sensitive=True)
            # 把强制备份登记进状态（四道门删除时用 backup_manifest.path）
            st_doc = st.load(src)
            if st_doc and not dry:
                st_doc['backup_manifest'] = {'path': backup, 'files': ns, 'bytes': bs}
                st.save(st_doc)
            RESULTS['migrate'].append(r)
        except (GuardError, StuckError) as e:
            RESULTS['migrate'].append({'src': src, 'ok': False, 'msg': str(e)})
    ok_n = sum(1 for r in RESULTS['migrate'] if r.get('ok'))
    log(f'==== 微信迁移完成: {ok_n}/{len(RESULTS["migrate"])} ====')
    log('下一步: 启动微信 → 看聊天记录是否完整 → python wechat_doctor.py --check 复检')
    return 0 if ok_n == len(RESULTS['migrate']) or not RESULTS['migrate'] else 2


def fmt_b(size):
    return mj.fmt(size)


def log(msg):
    mj.log(msg)


# ---------- SRC_REBUILT 修复 ----------

def do_repair(yes=False, dry=False):
    """修复"应用重建了源目录"形态: 增量合并新数据到 dst（不删源）→ 改名 stale → 重建 junction。
    S 类默认不自动执行, 须 --yes（用户确认已停止微信且知晓操作内容）。"""
    found = False
    for s in st.iter_states():
        if s['state'] != st.SRC_REBUILT:
            continue
        if not ('xwechat' in norm_path(s['src']) or 'wechat' in norm_path(s['src'])):
            continue
        found = True
        src, dst = s['src'], s['dst']
        log(f'=== 修复 SRC_REBUILT: {src} ===')
        if not yes:
            log('  预览（加 --yes 才执行）: 增量合并 新src → dst（不删任何数据）, '
                '然后改名 src 为 *_stale_<ts>, 重建 junction。执行前请确认微信已完全退出。')
            continue
        procs, dead = mj.kill_and_confirm(WECHAT_KEYWORDS, set(WECHAT_PROC_NAMES), timeout=40)
        if not dead:
            log('  ✗ 进程未退出, 中止')
            continue
        ok, why = mj.probe_lock(src)
        if not ok:
            log(f'  ✗ 锁探测失败: {why}')
            continue
        # ① 增量合并新数据（robocopy 只补差异, 不删除 dst 已有数据）
        if not mj.robocopy(src, dst, dry=dry):
            log('  ✗ 合并失败, 状态保持 SRC_REBUILT')
            continue
        # ② 改名新目录（不删! 留作 stale 供人工核对）, 再建 junction
        stale = src + f'_stale_{datetime.datetime.now():%Y%m%d%H%M%S}'
        if not dry:
            try:
                os.rename(src, stale)
            except OSError as e:
                log(f'  ✗ 改名失败: {e}')
                continue
            if not mj.make_junction(src, dst):
                os.rename(stale, src)
                log('  ✗ junction 创建失败, 已还原')
                continue
            verdict, _ = mj.check_junction(src, dst)
            log(f'  修复完成: 新数据已合并, 旧重建目录保留于 {stale}（核对后可手动删除）, 判定={verdict}')
            st.transition(s, st.JUNCTION_OK if verdict == 'OK' else st.JUNCTIONED,
                          msg=f'SRC_REBUILT 修复, stale={stale}')
    if not found:
        log('没有 SRC_REBUILT 状态的微信迁移记录')
    return 0


# ---------- 清理强制备份 ----------

def do_purge_backup(older_than=30, i_know='', dry=False):
    """清理 wechat_backup 下的强制备份。门: 迁移状态 JUNCTION_OK+ 且 check_db 通过 + 保留期 + --i-know"""
    # 从状态里找 backup_manifest 路径, 而不是扫盘 —— 状态里登记过的才可清
    db_check = check_db()
    db_ok = bool(db_check.get('ok'))
    for s in st.iter_states():
        bp = (s.get('backup_manifest') or {}).get('path')
        if not bp or not os.path.exists(bp):
            continue
        if 'wechat' not in norm_path(bp) and 'xwechat' not in norm_path(s['src']):
            continue
        if s['state'] not in (st.JUNCTION_OK, st.APP_CHECKED, st.PURGE_PENDING):
            log(f'⊘ {bp}: 迁移状态 {s["state"]} 未达 JUNCTION_OK, 不清')
            continue
        if not db_ok:
            log(f'⊘ {bp}: check_db 未通过, 绝不清备份')
            continue
        age = (datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(bp))).days
        if age < older_than:
            log(f'⊘ {bp}: 备份 {age} 天, 未到保留期 {older_than} 天')
            continue
        if 'wechat' not in (i_know or '').lower():
            log(f'⊘ {bp}: 需 --i-know wechat 显式确认')
            continue
        if dry:
            log(f'[dry-run] 将删除 {bp} ({fmt_b(mj.dir_size(bp))})')
            continue
        guard(bp, extra_protected=st.protected_paths(), action='删除微信备份',
              allow=[norm_path(bp)])
        try:
            import shutil
            shutil.rmtree(bp)
            log(f'✓ 已删除备份 {bp}')
            st.transition(s, st.PURGED, msg='强制备份已清理')
        except OSError as e:
            log(f'✗ 删除失败: {e}')
    return 0


# ---------- 主流程 ----------

def main():
    ap = argparse.ArgumentParser(description='微信数据专项检测/迁移/复检/修复')
    ap.add_argument('--detect', action='store_true', help='检测全部微信数据位置与进程')
    ap.add_argument('--migrate', action='store_true', help='强制备份后迁移（一次一个目录）')
    ap.add_argument('--check', action='store_true', help='迁移后五步复检')
    ap.add_argument('--repair', action='store_true', help='修复 SRC_REBUILT（须配合 --yes）')
    ap.add_argument('--yes', action='store_true', help='确认执行修复')
    ap.add_argument('--purge-backup', action='store_true', help='清理强制备份（四道门）')
    ap.add_argument('--target', default=None, help='迁移目标盘符')
    ap.add_argument('--older-than', type=int, default=30, help='备份保留天数（默认30）')
    ap.add_argument('--i-know', default='', help='清备份确认词')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--timeout', type=int, default=3600)
    ap.add_argument('--json', dest='json_out', action='store_true')
    args = ap.parse_args()

    if not any([args.detect, args.migrate, args.check, args.repair, args.purge_backup]):
        ap.print_help()
        sys.exit(1)

    code = 0
    if args.detect:
        root, ini = find_data_root()
        procs = wechat_procs()
        paths = enum_paths()
        print('微信数据位置:')
        for p in paths:
            mark = '★在C盘' if p['on_system_drive'] else '(不在C盘)'
            db = ' [含db_storage聊天库]' if p.get('has_db') else ''
            print(f'  {mark} {p["label"]}')
            print(f'    {p["path"]}{db}')
        if root:
            print(f'  config ini 指定数据根: {root}  (ini: {ini})')
        print(f'\n微信相关进程: {len(procs)} 个')
        for p in procs[:10]:
            print(f'  {p["name"]} (pid={p["pid"]}) {p["path"][:80]}')
        RESULTS['detect'] = {'paths': paths, 'data_root': root, 'ini': ini,
                             'procs': [{'pid': p['pid'], 'name': p['name']} for p in procs]}
        code = 0

    if args.migrate:
        target = mj.pick_target(args.target)
        if not target:
            print('✗ 无可用数据盘')
            sys.exit(1)
        code = do_migrate(target, dry=args.dry_run, timeout=args.timeout)

    if args.check:
        r = check_db()
        print(json.dumps(r, ensure_ascii=False, indent=2))
        RESULTS['check'] = r
        if r.get('src_rebuilt'):
            print('⚠ C 盘原路径被重建! 用 --repair --yes 修复')
            code = 4
        elif not r.get('ok'):
            print('✗ 复检未通过, 不要删除任何备份!')
            code = 2
        else:
            print('✓ 复检五步全部通过')
            code = 0

    if args.repair:
        code = do_repair(yes=args.yes, dry=args.dry_run)

    if args.purge_backup:
        code = do_purge_backup(args.older_than, args.i_know, args.dry_run)

    if args.json_out:
        print(json.dumps(RESULTS, ensure_ascii=False, indent=2, default=str))
    sys.exit(code)


if __name__ == '__main__':
    main()
