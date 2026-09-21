#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""回收站明细脚本 v1.2（c-drive-cleanup skill 阶段3.5）

为什么回收站必须专项处理（事故复盘）:
  一起真实事故里 agent 调了"清空回收站", 14647 项被整体清空,
  里面有用户的投行需求变更 doc、尽职调查手册、Chrome 密码.csv 等个人文件。
  教训: 回收站 = 个人数据, 禁止整体清空; 只能"列明细 → 逐条确认 → 按条删除"。

本脚本只做两件事:
  --scan   枚举明细（原始路径/删除时间/大小/是否敏感文件）, 按删除日期分组
  --purge  按已生成的 purge_plan 逐条删除（$R 实体 + $I 记录）, 有确认门

技术要点:
  - 各盘 $Recycle.Bin\\<SID>\\ 下: $I开头=元数据记录, $R开头=被删实体
  - $I 文件头: 前 8 字节版本号（v1=int32(1), v2=int64(2)）。v2 布局:
    size=unpack('<q', b[8:16]); ftime=unpack('<q', b[16:24]); path=b[24:544] utf-16-le
    （v1 的路径是固定 520 字节, 布局待实测 —— 多分支兼容, 解析失败的单条跳过不报错）
  - 非当前用户 SID 子目录会 PermissionError, 直接跳过
  - 敏感文件（doc/xlsx/pdf/csv/zip/文件名含密码合同尽调等）默认排除在清理计划外

用法:
  python recycle_bin.py --scan                       # 列明细
  python recycle_bin.py --scan --json plan.json      # 明细 + 生成清理计划（默认保留30天内）
  python recycle_bin.py --purge --plan plan.json --i-know <计划条数>   # 逐条删除
退出码: 0 成功 / 1 参数错 / 2 部分失败 / 3 安全门拦截
"""
import os
import sys
import json
import glob
import struct
import string
import ctypes
import datetime
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import guard, norm_path, fmt, GuardError

FILETIME_EPOCH_DELTA = 116444736000000000  # 1601-01-01 → 1970-01-01 (100ns units)

SENSITIVE_EXT = {'.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                 '.pdf', '.csv', '.zip', '.rar', '.7z', '.kdbx', '.bak', '.eml'}
SENSITIVE_KEYWORDS = ['密码', 'password', '账号', '合同', '尽调', '协议', '身份证',
                      '银行', '客户', '报价', '薪酬', '简历', 'key', 'secret', '.csv']


def filetime_to_dt(ft):
    try:
        return datetime.datetime.fromtimestamp((ft - FILETIME_EPOCH_DELTA) / 10**7)
    except (OSError, OverflowError, ValueError):
        return None


def parse_i_file(path):
    """解析 $I 元数据。返回 dict 或 None（解析失败的单条跳过 —— 不赌布局）

    实测两种 v2 布局（Windows 新旧版本不同, 都要接住）:
      - 旧版固定 544 字节: 24字节头 + 520字节定长路径(utf-16-le)
      - 新版变长（本机实测 114/196 字节）: 24字节头 + 4字节路径长度(uint32)
        + 路径*2字节(utf-16-le, 无填充)
      判据（重要）: 不能简单用 len>=544 判新旧 —— 变长布局下路径正好 258 字符时
        28+258*2 = 544, 会被误判成定长而解出乱码。改用自洽性校验优先试探变长:
        读 namelen@24, 若 28+namelen*2 恰好等于文件长度(或其后全是 \0 填充),
        判定为变长布局; 否则退回定长 544。
    """
    try:
        raw = open(path, 'rb').read()
        if len(raw) < 28:
            return None
        size = struct.unpack('<q', raw[8:16])[0]
        ftime = struct.unpack('<q', raw[16:24])[0]
        name = None
        # ① 先试探新版变长布局（自洽性校验: 尾部精确对齐）
        namelen = struct.unpack('<I', raw[24:28])[0]
        end = 28 + namelen * 2
        if 0 < namelen <= 32767 and end <= len(raw):
            tail = raw[end:]
            if not tail or tail == b'\x00' * len(tail):   # 无残留 或 仅 \0 填充
                name = raw[28:end].decode('utf-16-le', errors='replace').rstrip('\x00')
        # ② 变长不自洽 → 退回旧版定长
        if name is None:
            if len(raw) < 544:
                return None
            name = raw[24:544].decode('utf-16-le', errors='replace').rstrip('\x00')
        if not name:
            return None
        return {'orig_path': name, 'size': size,
                'deleted_at': filetime_to_dt(ftime)}
    except (OSError, struct.error):
        return None


def is_sensitive(orig_path):
    name = (orig_path or '').lower()
    ext = os.path.splitext(name)[1]
    if ext in SENSITIVE_EXT:
        return True
    return any(k in name for k in SENSITIVE_KEYWORDS)


def entity_for(i_path):
    """$Ixxxxxxxx... -> $Rxxxxxxxx...（同号不同前缀）"""
    base = os.path.basename(i_path)
    return os.path.join(os.path.dirname(i_path), '$R' + base[2:])


def entity_size(r_path):
    """$R 实体大小（文件直取; 目录递归统计）"""
    try:
        if os.path.isfile(r_path):
            return os.path.getsize(r_path)
        if os.path.isdir(r_path):
            total = 0
            for root, _d, files in os.walk(r_path):
                for f in files:
                    try:
                        total += os.path.getsize(os.path.join(root, f))
                    except OSError:
                        pass
            return total
    except OSError:
        pass
    return None


def scan(keep_days=30, bases=None):
    """枚举全部回收站条目。bases: 自定义扫描根（测试沙箱用; 缺省扫各盘 $Recycle.Bin）"""
    items = []
    roots = bases or [os.path.join(f'{l}:\\', '$Recycle.Bin')
                      for l in string.ascii_uppercase
                      if os.path.exists(f'{l}:\\')]
    for base in roots:
        for sid_dir in glob.glob(os.path.join(base, '*')):
            try:
                i_files = glob.glob(os.path.join(sid_dir, '$I*'))
            except OSError:
                continue  # 其他用户的 SID 目录无权限, 跳过
            for ip in i_files:
                info = parse_i_file(ip)
                if info is None:
                    continue
                rp = entity_for(ip)
                r_exists = os.path.lexists(rp)
                r_size = entity_size(rp) if r_exists else 0
                size = info['size'] or r_size
                items.append({
                    'i_file': ip,
                    'r_entity': rp if r_exists else None,
                    'orig_path': info['orig_path'],
                    # size = 名义大小($I 记录的原始文件大小); actual_size = 实际占用($R 实体)
                    # 实测两者可差 44%: $R 已被系统清理/跨盘时 $I 记录仍在, 名义大小就是虚的
                    'size': size,
                    'size_str': fmt(size),
                    'actual_size': r_size,
                    'actual_size_str': fmt(r_size),
                    'deleted_at': info['deleted_at'].isoformat(timespec='seconds')
                                  if info['deleted_at'] else None,
                    'drive': base[:2],
                    'sensitive': is_sensitive(info['orig_path']),
                })
    return items


def summarize(items, keep_days=30):
    """分组统计: 总量 / ≤7天 / ≤keep_days / 更早; Top20; 敏感项单列"""
    now = datetime.datetime.now()
    groups = {'within_7d': 0, 'within_keep': 0, 'older': 0}
    gbytes = {'within_7d': 0, 'within_keep': 0, 'older': 0}
    gactual = {'within_7d': 0, 'within_keep': 0, 'older': 0}
    for it in items:
        dt = datetime.datetime.fromisoformat(it['deleted_at']) if it['deleted_at'] else None
        age = (now - dt).days if dt else 9999
        if age <= 7:
            k = 'within_7d'
        elif age <= keep_days:
            k = 'within_keep'
        else:
            k = 'older'
        groups[k] += 1
        gbytes[k] += it['size'] or 0
        gactual[k] += it.get('actual_size') or 0
    sens = [it for it in items if it['sensitive']]
    # 孤儿记录: $I 在但 $R 实体已不在 —— 名义大小是虚的, 清了也不释放空间
    orphans = [it for it in items if not it['r_entity']]
    nominal = sum(it['size'] or 0 for it in items)
    actual = sum(it.get('actual_size') or 0 for it in items)
    top = sorted(items, key=lambda x: -(x.get('actual_size') or 0))[:20]
    return {
        'total_count': len(items),
        'total_size_str': fmt(nominal),
        'actual_total_str': fmt(actual),
        'orphan_count': len(orphans),
        'groups': {k: {'count': v, 'size': fmt(gbytes[k]), 'actual': fmt(gactual[k])}
                   for k, v in groups.items()},
        'sensitive_count': len(sens),
        'top20': [{'orig_path': t['orig_path'], 'size': t['size_str'],
                   'actual_size': t.get('actual_size_str', t['size_str']),
                   'deleted_at': t['deleted_at'], 'sensitive': t['sensitive'],
                   'drive': t['drive'], 'has_entity': bool(t['r_entity'])}
                  for t in top],
    }


def _older_than(deleted_at, keep_days):
    """deleted_at(ISO串) 是否早于保留期; 时间缺失时保守返回 False（不当旧数据处理）"""
    if not deleted_at:
        return False
    try:
        dt = datetime.datetime.fromisoformat(deleted_at)
    except ValueError:
        return False
    return (datetime.datetime.now() - dt).days > keep_days


def build_purge_plan(items, keep_days=30, include_sensitive=False, allow_list=None):
    """清理计划: 只含 keep_days 之前的、且 $R 实体存在的条目。

    敏感项三重门（默认全关, 任一打开才纳入）:
      --include-sensitive   全部敏感项纳入（危险, 需人工逐条看过明细）
      --allow-list <路径>   只放开指定原始路径的敏感项（推荐）
    """
    now = datetime.datetime.now()
    allow_set = {norm_path(p) for p in (allow_list or []) if p}
    plan = []
    for it in items:
        if it['sensitive']:
            if not include_sensitive and norm_path(it['orig_path']) not in allow_set:
                continue  # 敏感文件默认绝不进计划
        dt = datetime.datetime.fromisoformat(it['deleted_at']) if it['deleted_at'] else None
        if dt and (now - dt).days <= keep_days:
            continue
        if not it['r_entity']:
            continue  # $R 实体已不在的只清 $I 记录也行, 但保守起见留给系统自清理
        plan.append(it)
    return plan


def do_purge(plan_path, i_know, allow_list=None, dry=False):
    """按计划逐条删除。确认门: --i-know 必须等于计划条数。"""
    try:
        with open(plan_path, encoding='utf-8') as f:
            doc = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f'✗ 读取计划失败: {e}')
        sys.exit(1)
    plan = doc.get('purge_plan', [])
    if not plan:
        print('计划为空, 无需清理')
        sys.exit(0)
    try:
        known = int(i_know)
    except ValueError:
        print('✗ --i-know 需为计划条数（数字）, 用 --scan --json 重新生成计划查看')
        sys.exit(3)
    if known != len(plan):
        print(f'✗ 确认门: --i-know {known} ≠ 计划条数 {len(plan)}。'
              f'请先查看计划文件确认每一项后再执行')
        sys.exit(3)

    allow = [norm_path(it['r_entity']) for it in plan] + \
            [norm_path(it['i_file']) for it in plan]
    allow += [norm_path(a) for a in (allow_list or [])]
    deleted, failed = 0, 0
    import shutil
    for it in plan:
        if dry:
            print(f'[dry-run] 删除 {it["orig_path"]} ({fmt(it["size"])}, 删于 {it["deleted_at"]})')
            deleted += 1
            continue
        try:
            # guard: 常规保护仍生效（已知文件夹等）, 仅放行本计划内的 $R/$I 路径
            guard(it['r_entity'], action='删除回收站条目', allow=allow)
            guard(it['i_file'], action='删除回收站记录', allow=allow)
            if os.path.isdir(it['r_entity']):
                shutil.rmtree(it['r_entity'])
            else:
                os.remove(it['r_entity'])
            os.remove(it['i_file'])
            deleted += 1
        except (GuardError, OSError) as e:
            print(f'✗ 跳过 {it["orig_path"]}: {e}')
            failed += 1
    print(f'\n完成: 删除 {deleted} 项, 失败/跳过 {failed} 项')
    return 0 if failed == 0 else 2


def main():
    ap = argparse.ArgumentParser(description='回收站明细（列明细→逐条确认→按条删除, 禁止整体清空）')
    ap.add_argument('--scan', action='store_true', help='枚举明细并打印汇总')
    ap.add_argument('--keep-days', type=int, default=30, help='保留期（计划只含更早的, 默认30天）')
    ap.add_argument('--json', dest='json_out', default=None, help='明细+清理计划写入 JSON 文件')
    ap.add_argument('--purge', action='store_true', help='按计划逐条删除')
    ap.add_argument('--plan', default=None, help='purge 用的计划文件')
    ap.add_argument('--i-know', default='', help='确认门: 计划条数')
    ap.add_argument('--allow-list', default=None, help='额外允许删除的敏感项原始路径（逗号分隔, 推荐逐条放开）')
    ap.add_argument('--include-sensitive', action='store_true',
                    help='把所有敏感项也纳入清理计划（危险: 仅在你逐条看过明细后使用）')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    if args.purge:
        if not args.plan:
            print('✗ --purge 需要 --plan 文件（先 --scan --json 生成）')
            sys.exit(1)
        sys.exit(do_purge(args.plan, args.i_know,
                          (args.allow_list or '').split(',') if args.allow_list else None,
                          args.dry_run))

    if not args.scan:
        ap.print_help()
        sys.exit(1)

    items = scan(args.keep_days)
    s = summarize(items, args.keep_days)
    print(f'回收站共 {s["total_count"]} 项')
    print(f'  名义大小($I记录): {s["total_size_str"]}   ← 不可信, 含已删实体的虚账')
    print(f'  实际占用($R实体): {s["actual_total_str"]}   ← 真正能被释放的空间')
    if s['orphan_count']:
        print(f'  其中 {s["orphan_count"]} 项是孤儿记录（$I 在、$R 已不在, 不占空间, 清了也不释放）')
    for label, k in [('7天内删除', 'within_7d'),
                     (f'{args.keep_days}天内删除', 'within_keep'),
                     ('更早', 'older')]:
        g = s['groups'][k]
        print(f'  {label:<12} {g["count"]:>6} 项  名义 {g["size"]:>10}  实际 {g["actual"]:>10}')
    print(f'  ⚠ 其中疑似敏感文件 {s["sensitive_count"]} 项（默认排除在清理计划外）')
    print('\nTop20（按实际占用排序）:')
    for t in s['top20']:
        mark = ' [敏感]' if t['sensitive'] else ''
        ghost = '' if t['has_entity'] else ' [实体已不在]'
        print(f'  {t["actual_size"]:>10}  {t["drive"]}  删于 {t["deleted_at"]}  '
              f'{t["orig_path"]}{mark}{ghost}')
    allow = (args.allow_list or '').split(',') if args.allow_list else None
    plan = build_purge_plan(items, args.keep_days, args.include_sensitive, allow)
    # 排除原因分开设账 —— 不同原因出路不同, 混在一起会把人往"整体清空"上逼
    old_items = [it for it in items if _older_than(it['deleted_at'], args.keep_days)]
    old_sens = sum(1 for it in old_items if it['sensitive'])
    old_ghost = sum(1 for it in old_items if not it['r_entity'])
    print(f'\n清理计划: {len(plan)} 项')
    if not plan and old_items:
        print(f'  ⚠ 保留期前有 {len(old_items)} 项, 但计划为空 —— 原因:')
        if old_ghost:
            print(f'    - {old_ghost} 项 $R 实体已不存在（孤儿记录）: 不占空间, '
                  f'清了也释放不了 1 字节 → 无需处理, 系统会自清')
        if old_sens:
            print(f'    - {old_sens} 项疑似敏感被默认排除 → 出路: '
                  f'--allow-list "路径" 逐条放开（推荐）或 --include-sensitive（危险）')
        if not old_ghost and not old_sens:
            print('    - （未知原因, 请检查 keep-days 设置）')
    print('\n用法: python recycle_bin.py --scan --json plan.json  生成计划')
    print('      python recycle_bin.py --purge --plan plan.json --i-know <条数>  逐条删除')
    print('⚠ 本脚本永远不做"整体清空回收站"。')

    if args.json_out:
        doc = {'generated_at': datetime.datetime.now().isoformat(timespec='seconds'),
               'keep_days': args.keep_days,
               'include_sensitive': args.include_sensitive,
               'excluded_sensitive_older': old_sens,
               'excluded_ghost_older': old_ghost,
               'actual_reclaimable': fmt(sum(it.get('actual_size') or 0 for it in plan)),
               'summary': s,
               'purge_plan': [{'orig_path': it['orig_path'], 'i_file': it['i_file'],
                               'r_entity': it['r_entity'], 'size': it['size'],
                               'actual_size': it.get('actual_size', 0),
                               'sensitive': it['sensitive'],
                               'deleted_at': it['deleted_at']} for it in plan]}
        with open(args.json_out, 'w', encoding='utf-8') as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
        print(f'\n明细与清理计划已写入: {args.json_out} （计划含 {len(plan)} 项'
              f'{", 含敏感项" if args.include_sensitive else ""}）')


if __name__ == '__main__':
    main()
