#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""沙箱夹具（c-drive-cleanup v1.2 自测）

在临时目录构造各种残留状态, 全部只动沙箱, 不碰用户真实数据:
  sandbox/
    fake_local/                     ← 冒充 LOCALAPPDATA（state.py 的状态文件写这里）
    target/JunctionData/            ← 冒充迁移目标盘
    apps/fresh_app/                 ← 全新源（30个文件）
    apps/busy_app/                  ← 被占用的源（占用句柄由 run_selftest 持有）
    apps/renamed_app_backup/        ← RENAMED 残留态（src 没了, 数据在 _backup）
    apps/rebuilt_app/ + _backup + dst ← SRC_REBUILT 残留态
    fakebin/<sid>/$I…/$R…           ← 假回收站条目

用法: python make_fixture.py <sandbox_root>
输出: JSON 描述夹具路径
"""
import os
import sys
import json
import struct
import shutil
import glob
import time
import datetime

FILETIME_EPOCH_DELTA = 116444736000000000


def make_tree(path, n_files=30, tag=''):
    """造 n_files 个小文件的目录树（两层的扁平树）"""
    os.makedirs(path, exist_ok=True)
    sub = os.path.join(path, 'data')
    os.makedirs(sub, exist_ok=True)
    for i in range(n_files):
        with open(os.path.join(sub if i % 2 else path, f'f{i}_{tag}.txt'), 'w') as f:
            f.write(f'content-{tag}-{i}\n' * 5)


def make_i_v2(path, orig_path, size, deleted_dt):
    """旧版定长布局 v2: 24字节头 + 520字节定长路径 = 544 字节"""
    ft = int((deleted_dt - datetime.datetime(1970, 1, 1)).total_seconds() * 10**7
             + FILETIME_EPOCH_DELTA)
    name_bytes = orig_path.encode('utf-16-le')
    name_bytes = name_bytes + b'\x00' * (520 - len(name_bytes))
    raw = struct.pack('<q', 2) + struct.pack('<q', size) + struct.pack('<q', ft) + name_bytes
    open(path, 'wb').write(raw)
    return os.path.join(os.path.dirname(path), '$R' + os.path.basename(path)[2:])


def make_i_compact(path, orig_path, size, deleted_dt):
    """新版变长布局 v2（Win11 实测 114/196 字节）:
    24字节头 + 4字节路径长度(字符数, uint32) + 路径*2字节(utf-16-le, 无填充)

    为什么必须有这个 fixture: v1.2 的解析器曾写死 544 定长, 在变长布局机器上
    2 万个条目全部解析失败、静默返回 0 条 —— 而自测因为只造了定长 fixture, 全绿。
    教训: fixture 必须覆盖真实世界的每种布局变体, 否则自测是自欺欺人。
    """
    ft = int((deleted_dt - datetime.datetime(1970, 1, 1)).total_seconds() * 10**7
             + FILETIME_EPOCH_DELTA)
    name_bytes = orig_path.encode('utf-16-le')
    raw = (struct.pack('<q', 2) + struct.pack('<q', size) + struct.pack('<q', ft)
           + struct.pack('<I', len(orig_path)) + name_bytes)
    open(path, 'wb').write(raw)
    return os.path.join(os.path.dirname(path), '$R' + os.path.basename(path)[2:])


def build(sandbox, force=False):
    """建夹具。默认拒绝覆盖已存在目录（不自动删 —— 自测不该有任何删除动作）"""
    if os.path.exists(sandbox) and os.listdir(sandbox):
        if not force:
            raise SystemExit(
                f'沙箱目录非空, 拒绝覆盖（避免自测产生删除动作）: {sandbox}\n'
                f'  传新目录名, 或显式 force=True 重建')
        shutil.rmtree(sandbox)
    fx = {
        'sandbox': sandbox,
        'fake_local': os.path.join(sandbox, 'fake_local'),
        'target': os.path.join(sandbox, 'target'),
        'apps': os.path.join(sandbox, 'apps'),
        'fakebin': os.path.join(sandbox, 'fakebin'),
    }
    os.makedirs(os.path.join(fx['fake_local'], 'c-drive-cleanup', 'state'), exist_ok=True)
    os.makedirs(os.path.join(fx['target'], 'JunctionData'), exist_ok=True)
    os.makedirs(os.path.join(fx['fakebin'], 'S-1-5-21-0-0-0-1001'), exist_ok=True)

    # ① 全新源
    fx['fresh_app'] = os.path.join(fx['apps'], 'fresh_app')
    make_tree(fx['fresh_app'], 30, 'fresh')

    # ② 被占用源
    fx['busy_app'] = os.path.join(fx['apps'], 'busy_app')
    make_tree(fx['busy_app'], 10, 'busy')
    fx['busy_held_file'] = os.path.join(fx['busy_app'], 'f0_busy.txt')

    # ③ RENAMED 残留: 数据在 _backup, dst 已有完整拷贝, src 位置空
    fx['renamed_app'] = os.path.join(fx['apps'], 'renamed_app')
    fx['renamed_app_backup'] = fx['renamed_app'] + '_backup'
    make_tree(fx['renamed_app_backup'], 20, 'renamed')
    fx['renamed_dst'] = os.path.join(fx['target'], 'JunctionData', 'renamed_app')
    shutil.copytree(fx['renamed_app_backup'], fx['renamed_dst'])

    # ④ SRC_REBUILT 残留: dst 有旧数据 + _backup 有旧数据 + 应用在 src 重建了真实目录（含新文件）
    fx['rebuilt_app'] = os.path.join(fx['apps'], 'rebuilt_app')
    fx['rebuilt_app_backup'] = fx['rebuilt_app'] + '_backup'
    make_tree(fx['rebuilt_app_backup'], 20, 'old')
    fx['rebuilt_dst'] = os.path.join(fx['target'], 'JunctionData', 'rebuilt_app')
    shutil.copytree(fx['rebuilt_app_backup'], fx['rebuilt_dst'])
    make_tree(fx['rebuilt_app'], 5, 'NEW')   # 应用重建的新目录（新数据）

    # ⑤ 假回收站: 3条（1敏感 doc + 1普通老文件 + 1普通30天内文件）
    sid = os.path.join(fx['fakebin'], 'S-1-5-21-0-0-0-1001')
    now = datetime.datetime.now()
    r1 = make_i_v2(os.path.join(sid, '$I11111111.1'), r'C:\Users\测试\项目方案.doc',
                   1024 * 1024, now - datetime.timedelta(days=40))
    open(r1, 'wb').write(b'A' * 1024 * 1024)
    r2 = make_i_v2(os.path.join(sid, '$I22222222.2'), r'C:\Users\测试\notes_old.txt',
                   2048, now - datetime.timedelta(days=40))
    open(r2, 'wb').write(b'B' * 2048)
    r3 = make_i_v2(os.path.join(sid, '$I33333333.3'), r'C:\Users\测试\recent.txt',
                   512, now - datetime.timedelta(days=3))
    open(r3, 'wb').write(b'C' * 512)

    # ⑥ 变长布局（新版 Windows 真实布局, v1.2 曾在此全军覆没 → 必须有 fixture）
    r4 = make_i_compact(os.path.join(sid, '$I44444444.4'), r'C:\Users\测试\报价单.docx',
                        4096, now - datetime.timedelta(days=40))       # 中文+敏感
    open(r4, 'wb').write(b'D' * 4096)
    # ⑦ 边界用例: 路径正好 258 字符 → 28+258*2 = 544, 与定长布局总长相同
    #    （v1.2 的 len>=544 判据会把它误判成定长、解出乱码）
    boundary = 'C:\\' + 'a' * (258 - 3 - 4) + '.txt'   # 3=盘符 4=扩展名
    assert len(boundary) == 258, f'边界用例长度算错: {len(boundary)}'
    r5 = make_i_compact(os.path.join(sid, '$I55555555.5'), boundary,
                        256, now - datetime.timedelta(days=40))        # 普通旧文件
    open(r5, 'wb').write(b'E' * 256)

    fx['recycle_items'] = {'sensitive_doc': r1, 'old_txt': r2, 'recent_txt': r3,
                           'compact_sensitive': r4, 'boundary_258': r5}
    fx['boundary_path'] = boundary
    return fx


if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '_sandbox')
    fx = build(root)
    print(json.dumps(fx, ensure_ascii=False, indent=2))
