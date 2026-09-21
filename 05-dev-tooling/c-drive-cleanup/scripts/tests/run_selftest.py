#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""沙箱自测（c-drive-cleanup v1.2）—— 断言 8 项核心安全机制, 全绿才算过

先跑: python tests/make_fixture.py <sandbox>   （或由本脚本自动调用）

断言清单（每条对应事故/审计的一个具体缺陷）:
  T1  完整路径入参能解析出进程判据（修: v1.1 返回空列表 → 一个进程都不杀）
  T2  目录被占用时迁移 ABORT, 源文件数不变, 不产生半成品 dst（修: 带占用复制 → 数据分裂）
  T3  安全门: 对状态机登记过的路径 rmtree → GuardError（修: 文档规则无代码强制）
  T4  黄灯门: /MIR、rmtree 对非白名单路径 → GuardError（修: /MIR 被用到迁移源）
  T5  RENAMED 残留续跑 → skip_copy_make_junction, 不再"目标已存在就跳过"卡死
  T6  COPIED 残留续跑 → resume_copy（增量补齐, 不重复拷贝不报错）
  T7  SRC_REBUILT 检出 + 增量合并不丢数据
  T8  回收站: 解析出原始路径/删除时间/大小; 敏感项不进计划; --i-know 不对时拒绝删除
  T9  回收站 $I 双布局兼容: 定长544 + 变长(含 258 字符撞 544 的边界用例)

用法: python run_selftest.py [sandbox_root]
沙箱默认建在 tests/_sandbox_<时间戳>（每次全新、不覆盖、不自动删）。
跑完保留沙箱供人工核验与残留态勘查, 需要时自行删除（路径在结尾打印）。
"""
import os
import sys
import json
import time
import shutil
import struct
import tempfile
import subprocess
import datetime as _dt

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
# 沙箱位置有讲究: 绝不能建在 %TEMP% 下 —— A类白名单按路径前缀匹配,
# 沙箱在 TEMP 下会让所有测试路径都命中白名单、安全门形同虚设（实测踩过）。
# 建在 tests/ 下 + 时间戳目录名: 每次全新不覆盖, 因此无需删除旧沙箱。
SANDBOX = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    HERE, '_sandbox_' + _dt.datetime.now().strftime('%Y%m%d_%H%M%S'))

# 夹具先行（必须在 import state 之前设 LOCALAPPDATA, 状态文件落沙箱）
sys.path.insert(0, HERE)
import make_fixture
FX = make_fixture.build(SANDBOX)
os.environ['LOCALAPPDATA'] = FX['fake_local']

sys.path.insert(0, SCRIPTS)
import common
import state as st
import migrate_junction as mj
import recycle_bin as rb

PASS, FAIL = [], []


def check(name, cond, detail=''):
    if cond:
        PASS.append(name)
        print(f'  ✓ {name}')
    else:
        FAIL.append(f'{name}: {detail}')
        print(f'  ✗ {name}  {detail}')


print('== T1 完整路径入参解析进程判据 ==')
kws, names = mj.proc_ident_for(r'C:\Users\x\AppData\Roaming\Tencent\xwechat')
check('T1 短名/父目录命中', len(kws) > 0, f'kws={kws}')
kws2, _ = mj.proc_ident_for(r'C:\Users\x\AppData\Roaming\某未知应用\data')
check('T1 未知应用也有兜底关键字', len(kws2) > 0, f'kws2={kws2}')

print('== T2 占用目录迁移必须 ABORT ==')
target = FX['target']
held = open(FX['busy_held_file'], 'r')          # 持有句柄 → 目录 rename 必败
try:
    # drive_free 打桩（沙箱目录不是盘符）
    real_drive_free = mj.drive_free
    mj.drive_free = lambda d: 10 ** 15
    r = mj.migrate_one(FX['busy_app'], target, timeout=600)
finally:
    held.close()
    mj.drive_free = real_drive_free
src_files = sum(len(fs) for _, _, fs in os.walk(FX['busy_app']))
check('T2 迁移未成功', not r.get('ok'), r.get('msg', ''))
check('T2 源文件完好', src_files == 10, f'src_files={src_files}')
check('T2 无半成品 dst', not os.path.exists(os.path.join(target, 'JunctionData', 'busy_app')))
check('T2 状态停在 PROCS_KILLED', (st.load(FX['busy_app']) or {}).get('state') == st.PROCS_KILLED)

print('== T3 安全门拦截状态机登记路径 ==')
try:
    common.safe_rmtree(FX['busy_app'], extra_protected=st.protected_paths())
    blocked = False
except common.GuardError:
    blocked = True
check('T3 登记 src 禁删', blocked)
try:
    common.safe_rmtree(FX['renamed_app_backup'], extra_protected=st.protected_paths())
    blocked2 = False
except common.GuardError:
    blocked2 = True
check('T3 登记 backup 禁删', blocked2)

print('== T4 黄灯白名单 ==')
try:
    common.guard_a_class(FX['fresh_app'])
    blocked3 = False
except common.GuardError:
    blocked3 = True
check('T4 非白名单路径禁 /MIR·rmtree', blocked3)
try:
    common.guard_a_class(os.path.join(common.expand(r'%TEMP%'), 'whatever'))
    allowed = True
except common.GuardError as e:
    allowed = False
    print(f'    (TEMP 被拦: {e})')
check('T4 TEMP 白名单放行', allowed)
sens = os.path.join(SANDBOX, 'apps', 'xwechat_files')
os.makedirs(sens, exist_ok=True)
try:
    mj.migrate_one(sens, target)
    refused = False
except common.GuardError:
    refused = True
check('T4 S类路径拒绝通用迁移', refused)

print('== T5 RENAMED 残留续跑 ==')
# 手工构造 RENAMED 态（夹具已备好磁盘现状: src空/backup有/dst有）
os.makedirs(os.path.dirname(os.path.join(FX['fake_local'], 'c-drive-cleanup', 'state', 'x.json')),
            exist_ok=True)
st_doc = st.new_state(FX['renamed_app'], FX['renamed_dst'], app='test')
st.save(st_doc)
st.transition(FX['renamed_app'], st.RENAMED, msg='测试预置')
dec = st.decide_resume(st.load(FX['renamed_app']))
check('T5 决策=skip_copy_make_junction', dec['action'] == 'skip_copy_make_junction', str(dec))
# 实际续跑: migrate_one 应跳过复制直接建 junction 并五判据通过
real_drive_free = mj.drive_free
mj.drive_free = lambda d: 10 ** 15
try:
    r5 = mj.migrate_one(FX['renamed_app'], target)
finally:
    mj.drive_free = real_drive_free
check('T5 续跑成功', r5.get('ok'), r5.get('msg', ''))
check('T5 junction 生效', common.has_reparse(FX['renamed_app']) is True)
check('T5 状态推进到 JUNCTION_OK',
      (st.load(FX['renamed_app']) or {}).get('state') == st.JUNCTION_OK)
# 清理 junction（只删链接不删目标; 用 lexists 防路径不存在）
if os.path.lexists(FX['renamed_app']) and common.has_reparse(FX['renamed_app']):
    os.rmdir(FX['renamed_app'])

print('== T6 COPIED 残留增量续跑 ==')
fresh_dst = os.path.join(target, 'JunctionData', 'fresh_app')
st_doc6 = st.new_state(FX['fresh_app'], fresh_dst, app='test')
st.save(st_doc6)
# 造"只拷了一半"的 dst。
# 关键: 用 robocopy /XF 排除部分文件, 天然得到残缺的 dst —— 全程零删除动作。
# （旧写法是"先全量拷再删一半", 那些删除动作会累积触发安全策略的批量删除拦截）
os.makedirs(fresh_dst, exist_ok=True)
data_dir = os.path.join(FX['fresh_app'], 'data')
data_files = sorted(os.listdir(data_dir))
exclude = data_files[:len(data_files) // 2]      # 排除 data 下一半文件
subprocess.run(['robocopy', FX['fresh_app'], fresh_dst, '/E', '/COPY:DAT',
                '/XF', *exclude, '/MT:4', '/NFL', '/NDL', '/NJH', '/NJS', '/NP'],
               capture_output=True)
missing_before = sum(1 for f in exclude if not os.path.exists(os.path.join(fresh_dst, 'data', f)))
check('T6 夹具: dst 确实缺一半', missing_before == len(exclude) and len(exclude) > 0,
      f'exclude={len(exclude)} missing={missing_before}')
st.transition(FX['fresh_app'], st.COPIED, msg='测试预置: 半程')
real_drive_free = mj.drive_free
mj.drive_free = lambda d: 10 ** 15
try:
    r6 = mj.migrate_one(FX['fresh_app'], target)
finally:
    mj.drive_free = real_drive_free
ok6, ns, nd, *_ = mj.verify_trees(FX['fresh_app'], fresh_dst)
check('T6 续跑完成且一致', r6.get('ok') and ok6, f'{r6.get("msg")} ns={ns} nd={nd}')
check('T6 残缺文件已增量补齐',
      all(os.path.exists(os.path.join(fresh_dst, 'data', f)) for f in exclude),
      f'{sum(1 for f in exclude if os.path.exists(os.path.join(fresh_dst, "data", f)))}/{len(exclude)}')
check('T6 只建了一个 dst', os.path.isdir(fresh_dst) and common.has_reparse(fresh_dst) is False
      or common.has_reparse(FX['fresh_app']) is True)
# 清理: junction 在 src 上（fresh_app 已被迁移）, 移除链接
if common.has_reparse(FX['fresh_app']):
    os.rmdir(FX['fresh_app'])

print('== T7 SRC_REBUILT 检出 + 合并不丢数据 ==')
st_doc7 = st.new_state(FX['rebuilt_app'], FX['rebuilt_dst'], app='test')
st.save(st_doc7)
st.transition(FX['rebuilt_app'], st.SRC_REBUILT, msg='测试预置')
dec7 = st.decide_resume(st.load(FX['rebuilt_app']))
check('T7 决策=repair_rebuilt', dec7['action'] == 'repair_rebuilt', str(dec7))
# 增量合并（repair 第一步的本质）
rc = subprocess.run(['robocopy', FX['rebuilt_app'], FX['rebuilt_dst'], '/E', '/COPY:DAT',
                     '/MT:4', '/NFL', '/NDL', '/NJH', '/NJS', '/NP'], capture_output=True)
merged = os.listdir(os.path.join(FX['rebuilt_dst'], 'data'))
check('T7 旧数据未丢', len([f for f in merged if 'old' in f]) == 10, f'{len(merged)} files')
check('T7 新数据已并入', any('NEW' in f for f in merged))

print('== T8 回收站明细 ==')
items = rb.scan(bases=[FX['fakebin']])
check('T8 解析出 5 条(3定长+2变长)', len(items) == 5, f'got {len(items)}')
doc_item = [i for i in items if '项目方案.doc' in (i['orig_path'] or '')]
check('T8 原始路径正确', bool(doc_item) and '测试' in doc_item[0]['orig_path'])
check('T8 敏感项识别', bool(doc_item) and doc_item[0]['sensitive'] is True)
check('T8 删除时间解析', bool(doc_item) and doc_item[0]['deleted_at'] is not None)
check('T8 大小解析(1MB)', bool(doc_item) and doc_item[0]['size'] == 1024 * 1024)

print('== T9 $I 双布局兼容（v1.2 曾因只认定长, 在变长机器上静默返回 0 条） ==')
cjk = [i for i in items if '报价单.docx' in (i['orig_path'] or '')]
check('T9 变长布局解析出中文路径', bool(cjk), f'变长条目={[i["orig_path"] for i in items]}')
check('T9 变长布局敏感识别', bool(cjk) and cjk[0]['sensitive'] is True)
check('T9 变长布局大小解析(4KB)', bool(cjk) and cjk[0]['size'] == 4096,
      str(cjk[0]['size']) if cjk else 'n/a')
bnd = FX['boundary_path']                      # 258 字符 → 28+258*2 = 544, 与定长总长相同
bnd_item = [i for i in items if i['orig_path'] == bnd]
check('T9 258字符边界用例解出不乱码', bool(bnd_item), f'期望 {bnd[:20]}…(len={len(bnd)})')
check('T9 边界用例长度精确', bool(bnd_item) and len(bnd_item[0]['orig_path']) == 258,
      str(len(bnd_item[0]['orig_path'])) if bnd_item else 'n/a')

plan = rb.build_purge_plan(items, keep_days=30)
check('T8 敏感项不进计划(定长)', all('项目方案.doc' not in it['orig_path'] for it in plan))
check('T8 敏感项不进计划(变长)', all('报价单.docx' not in it['orig_path'] for it in plan))
check('T9 变长普通项可进计划', any(i['orig_path'] == bnd for i in plan),
      f'plan={[i["orig_path"][:30] for i in plan]}')
check('T8 30天内项不进计划', all('recent.txt' not in it['orig_path'] for it in plan))
plan_file = os.path.join(SANDBOX, 'purge_plan.json')
with open(plan_file, 'w', encoding='utf-8') as f:
    json.dump({'purge_plan': [{'orig_path': it['orig_path'], 'i_file': it['i_file'],
                               'r_entity': it['r_entity'], 'size': it['size'],
                               'sensitive': it['sensitive'],
                               'deleted_at': it['deleted_at']} for it in plan]}, f,
              ensure_ascii=False)
# --i-know 不对 → 拒绝（exit 3）
p = subprocess.run([sys.executable, os.path.join(SCRIPTS, 'recycle_bin.py'),
                    '--purge', '--plan', plan_file, '--i-know', '999'],
                   capture_output=True, text=True, errors='replace')
check('T8 i-know 不对拒绝删除', p.returncode == 3, f'exit={p.returncode}')
# 正确条数 + dry-run → 通过确认门
p2 = subprocess.run([sys.executable, os.path.join(SCRIPTS, 'recycle_bin.py'),
                     '--purge', '--plan', plan_file, '--i-know', str(len(plan)), '--dry-run'],
                    capture_output=True, text=True, errors='replace')
check('T8 正确 i-know 过门(dry-run)', p2.returncode == 0, f'exit={p2.returncode} {p2.stdout[-200:]}')
# 实删一条后 $R/$I 都消失
p3 = subprocess.run([sys.executable, os.path.join(SCRIPTS, 'recycle_bin.py'),
                     '--purge', '--plan', plan_file, '--i-know', str(len(plan))],
                    capture_output=True, text=True, errors='replace')
leftover = rb.scan(bases=[FX['fakebin']])
check('T8 逐条删除生效', p3.returncode == 0 and
      all('notes_old.txt' not in (i['orig_path'] or '') for i in leftover),
      f'exit={p3.returncode}')

# ---------- 收尾: 保留沙箱, 不做任何删除 ----------
# 为什么要保留: ① 失败时可现场勘查残留态 ② 自测本身不该产生删除动作
# （曾因自动 rmtree 沙箱被安全策略判定为批量删除而中断）
print('\n' + '=' * 50)
print(f'通过 {len(PASS)} / 失败 {len(FAIL)}')
for f_ in FAIL:
    print(f'  FAIL → {f_}')
print(f'\n沙箱保留: {SANDBOX}')
print('（含夹具/状态文件/日志, 可现场勘查; 不需时自行删除该目录）')
sys.exit(0 if not FAIL else 1)
