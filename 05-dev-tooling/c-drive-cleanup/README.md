# c-drive-cleanup 🧹

Windows C盘空间清理与迁移的 Agent Skill —— 把"检测 → 清理 → 迁移"的完整经验沉淀成可复用的工作流。

**v1.2 = 安全加固版**：一次真实事故（用户迁移微信后聊天记录丢失 4 天、回收站 14647 项个人文件被整体清空）推动了本版本的全部改动。效率优化保留，安全成为第一优先级。

## 这是什么

一个 [WorkBuddy](https://www.workbuddy.cn) / Claude 风格的 Agent Skill。安装后，对 Agent 说"帮我清理C盘"，它会按**实测验证过的流程**执行，而不是现场发挥：

```
检测(只读扫描) → 五分类决策 → A类清理(黄灯白名单) → B类迁移(状态机) / S类专项 → 五判据验证 → 四道门删备份
```

## 核心方法论

**五分类决策**：

| 分类 | 判断标准 | 处理方式 |
|---|---|---|
| **A类** | 删了不影响使用（纯缓存/崩溃转储/临时文件） | 直接删除（黄灯命令仅限白名单路径） |
| **B类** | 删了影响使用、但迁移后不影响（应用数据） | Junction 迁移到数据盘（走状态机） |
| **C类** | 系统核心/运行时依赖（Windows/Microsoft/conda） | 不动 |
| **D类** | 用户个人静态文件（桌面/文档/图片/下载） | 报告 → 征求选择 → 确认后代办 |
| **S类** | 丢了不可逆（聊天记录/邮件/密码库） | 只报告，走专项流程（wechat_doctor / 强制备份） |

**命令安全分级（文档+代码双层强制）**：
- 🟢 绿灯（纯复制/mklink/os.rename）任意路径
- 🟡 黄灯（`rm -rf`/`rmtree`/robocopy `/MIR`）**仅限 A 类白名单**（Temp/CrashDumps/pip缓存等）
- 🔴 红灯（`/MOVE` `/PURGE`、对迁移路径的任何删除）**绝对禁止**——`common.guard()` 代码层拦截（exit 3），绕不过去

**为什么用 Junction 不用 symlink**：`mklink /D` 符号链接需要管理员权限；Junction（目录联接）不需要，且本地磁盘间转发功能完全等价。

## 包含内容

| 文件 | 说明 |
|---|---|
| `SKILL.md` | 完整工作流：五分类清单、**命令安全分级**、迁移状态机+续跑表、Junction五判据、删备份四道门、**微信专项**、回收站规范、**事故复盘**、**34条踩坑记录** |
| `scripts/common.py` | 公共库：路径工具、安全门 `guard()`/`guard_a_class()`、受控删除入口（safe_rmtree/mirror_delete）、junction 判定、原子写 |
| `scripts/state.py` | **迁移状态机**：13+3 状态、原子落盘、中断续跑决策、登记路径保护 |
| `scripts/scan_c_drive.py` | 一键检测脚本（只读安全）：磁盘总览、**并行**目录占用排序、Junction识别、**五分类**建议（含S类探测）、回收站概览、目标盘自动探测+容量校验、`--json` |
| `scripts/migrate_junction.py` | **一键批量迁移脚本（v1.2 重写）**：状态机驱动，进程关闭二次确认+锁探测 → 两遍 robocopy(/MT:16) → 单遍并发验证 → 改名 → 建 Junction → 五判据 → 失败安全回滚（先恢复数据后清理，绝不先删）；`--plan`/`--dry-run`/`--json`/`--delete-backup` 四道门 |
| `scripts/wechat_doctor.py` | **微信专项**：读 config ini 找真实聊天库位置、进程路径法盘点、强制备份后才迁移、五步复检、SRC_REBUILT 修复（不删数据）、备份清理四道门 |
| `scripts/recycle_bin.py` | **回收站明细**：解析 $I/$R（原始路径/删除时间/大小）、**$I 双布局兼容**（定长544/变长，含258字符边界）、敏感文件识别与三重通路、30天保留、逐条删除确认门；**永远不整体清空** |
| `scripts/tests/` | 沙箱自测：`make_fixture.py` 造各残留态（含两种 $I 布局）+ `run_selftest.py` 32 项断言（不碰真实数据、全程零删除动作） |

## 安全设计（v1.2 事故驱动）

1. **状态机防分裂**：迁移每步落盘，中断/失败重跑自动续跑（增量 robocopy）或安全回滚（先恢复数据、永不先删）；`STUCK_BACKUP_PRESENT`/`SRC_REBUILT` 状态强制停下等人工
2. **进程关闭三重防线**：路径关键字+名称双判据识别 → 杀后轮询二次确认 → 目录锁探测（改名往返+3次静默快照），任一不过绝不复制
3. **Junction 五判据**：reparse/realpath/穿透/写入探针/dst非空，UNKNOWN 不算通过（杜绝"先判失效后判生效"翻转）
4. **S 类敏感数据**：聊天库加密 SQLite 两份无法合并——分裂=丢失。强制备份→迁移→复检→保留期后才许清备份
5. **回收站**：只列明细逐条删，敏感文件默认排除，`--i-know` 确认门；敏感项三条通路（`--allow-list` 逐条放开 / `--include-sensitive` / `--keep-days`），**计划为空时打印原因而不是放任你去整体清空**
6. **自测零删除**：半程中断用 `robocopy /XF` 造残缺副本；沙箱用带时间戳目录名、跑完保留。**沙箱不能建在 %TEMP% 下**——否则所有路径命中 A 类白名单，安全门测试全部假通过（实测踩过）

## 效率设计（v1.1 保留）

- **批量迁移**：10 个目录从 ~80+ 次手工操作降到 2-3 条命令
- **扫描并行**：顶层目录大小统计线程池并行（8 workers），快 3-5 倍；`--json` 免重复扫描
- **删除提速**：海量小文件/超长路径大树用 `common.mirror_delete()`（robocopy 空目录镜像法，仅限 A 类白名单）
- **验证提速**：单遍并发双树比对，替代两遍独立 os.walk

## 使用

```bash
# 1. 检测（只读）: 五分类建议 + 回收站概览 + 敏感数据探测
python scripts/scan_c_drive.py --quick --json scan.json

# 2. A类清理: 看清单 → 用户确认 → 走 common.py 受控入口
python -c "from common import safe_rmtree; safe_rmtree(r'%TEMP%\xxx')"   # 带安全门

# 3. B类迁移: 预演 → 执行 → 复检 → 四道门删备份
python scripts/migrate_junction.py --dirs kingsoft,google --plan
python scripts/migrate_junction.py --dirs kingsoft,google --dry-run
python scripts/migrate_junction.py --dirs kingsoft,google --target E --json
python scripts/migrate_junction.py --dirs kingsoft --delete-backup --i-know kingsoft --older-than 7

# 4. 微信: 永远走专项
python scripts/wechat_doctor.py --detect
python scripts/wechat_doctor.py --migrate --target E
python scripts/wechat_doctor.py --check

# 5. 回收站: 列明细 → 确认 → 逐条删
python scripts/recycle_bin.py --scan --json purge_plan.json
python scripts/recycle_bin.py --purge --plan purge_plan.json --i-know <条数>
# 敏感项被排除导致计划为空时（推荐逐条放开）:
python scripts/recycle_bin.py --scan --json plan.json --allow-list "C:\某\文件.docx"

# 6. 自测（沙箱, 不碰真实数据, 零删除动作）
python scripts/tests/run_selftest.py    # 39 项断言
```

## 安全性

- 检测/计划/预演全部**只读**
- 破坏性操作唯一入口是 `common.py` 的受控函数，命中红灯路径直接 exit 3
- 清理/删备份前必须用户确认；迁移失败自动回滚（先恢复数据）
- 迁移日志与状态文件即时落盘（`%LOCALAPPDATA%\c-drive-cleanup\`），中断可查可续

## 验证记录

- v1.0/v1.1：真实机器 15+ 目录约 127GB 迁移，全部启动验证通过
- v1.2：沙箱自测断言全绿（占用 ABORT、安全门拦截、残留续跑、SRC_REBUILT 合并、回收站确认门等）；`wechat_doctor --detect` / `migrate --plan` / `recycle_bin --scan` 真机只读冒烟通过
- v1.2.1：真机跑清理时抓到 **$I 变长布局 bug**（旧解析器写死 544 定长 → 本机 20920 个回收站条目**静默返回 0 项**，看着像"回收站是空的"）。修复并补 fixture（含 258 字符撞 544 的边界用例，自测扩到 **39 项**，新增 T9 双布局兼容）。同时发现 **A 类白名单按前缀匹配 → TEMP 下任何东西都视为可删**，已写入踩坑表
- v1.2.1 实战（2026-09-04）：用本 skill 完成一次真实清理——释放 **57.44 GiB**（wsl-crashes 61.7GB + CrashDumps + 残留安装包），并据此定位 onlyoffice 容器"反复崩溃"的根因（非真崩溃，是容器关闭时 WSL 进程终止转储，dump 大小≈WSL2 VM 内存映射，配 `.wslconfig` 限内存即可根治）。实战又沉淀 **2 条踩坑**（bash `rm` 被 safe-delete shim 拦截 + 清 C 盘绝不能走回收站的悖论），踩坑记录达 **34 条**

> 完整 `run_selftest.py`（39 项，零删除设计）因本机安全策略对沙箱目录的历史累积删除计数而未在本机整体跑完；T1–T9 全部断言已分组单独验证通过，核心断言另经独立零删除脚本复核（双布局 + 258 边界 + 敏感三通路 13/13）。

## License

MIT
