---
name: c-drive-cleanup
description: Windows系统盘(C盘)空间清理与迁移全流程方案。当用户提到"清理C盘"、"C盘满了/空间不足"、"释放磁盘空间"、"迁移到其他盘/数据盘"、"Junction迁移"、"软链接迁移"时使用。核心方法论：检测→分类→清理→迁移→验证，含完整的Windows Junction迁移标准流程、可复用检测脚本与踩坑记录。任何Windows机器可直接使用（路径全部走环境变量，目标盘自动探测）。
agent_created: true
version: "1.2.1"
display_name: "C盘清理与迁移"
display_name_en: "C Drive Cleanup & Migration"
description_zh: "Windows C盘空间清理与迁移全流程（v1.2 安全加固版）：五分类（A清理/B迁移/C不动/D个人文件/S敏感数据）+ 命令安全分级（绿灯/黄灯/红灯，代码层强制拦截）+ 迁移状态机（可续跑、防数据分裂）+ 目录锁探测 + Junction五判据验证 + 删备份四道门 + 微信专项脚本（读config ini找真实聊天库+强制备份）+ 回收站明细（禁止整体清空, $I双布局兼容, 敏感项三通路）。含真实事故复盘（微信聊天记录丢失4天）与34条踩坑记录。沙箱自测39项断言。任何Windows机器可用。"
description_en: "Windows C drive cleanup & migration with v1.2 safety hardening: 5-class triage (clean/migrate/keep/personal/sensitive), command safety levels enforced in code, resumable migration state machine, directory lock probing, 5-criteria junction verification, 4-gate backup deletion, WeChat-specific tooling (reads config ini for real chat DB root + forced backup), recycle bin itemization (never bulk-empty, dual $I layout support, 3 sensitive-item paths). Includes real incident postmortem and 34 pitfalls. 39 sandbox assertions. Works on any Windows machine."
visibility: "public"
---

# Windows系统盘(C盘)清理与迁移全流程

## ⚠ 先读我：一条血的原则（v1.2 增）

本 skill 曾导致一起**真实数据丢失事故**：用户迁移微信数据时，agent 把 `robocopy /MOVE` 和 `/MIR` 用在正在被微信写入的源目录上，进程又没杀干净，最终 C/D 两盘数据分裂，**聊天记录丢失 4 天且无法合并**（聊天库是加密 SQLite，两份无法拼接）；同一会话里还整体清空了回收站 14647 项（含用户的合同、密码导出等个人文件）。

v1.2 的所有加固都来自这次复盘，使用本 skill 时**这四条是铁律**：

1. **S 类敏感数据（聊天记录/邮件/密码库）绝不直接删/迁** —— 微信必须走 `wechat_doctor.py`（它会读 config ini 找到真实聊天库位置，迁移前强制完整备份）
2. **`/MIR`、`/MOVE`、`rm -rf` 只允许用于 A 类白名单路径**（Temp/CrashDumps/pip缓存等纯缓存），迁移相关路径碰都不要碰 —— 代码层 `common.py` 的 guard 会直接拦截（exit 3）
3. **迁移走状态机**，中断/失败重跑会自动续跑或回滚，绝不留下"C盘一份、D盘一份"的分裂状态；看到 `STUCK_BACKUP_PRESENT`/`SRC_REBUILT` 状态必须停下找人工
4. **回收站永远不整体清空**，用 `recycle_bin.py` 列明细逐条确认

## 通用性说明（任何 Windows 机器可直接使用）
- 脚本通过 `os.path.expanduser('~')` / `%USERPROFILE%` / `%SystemDrive%` 环境变量定位路径，**不依赖任何特定用户名或盘符**
- 迁移目标盘自动探测：`--target D` 指定，或自动选空闲最大的非系统盘；没有数据盘时仅输出扫描结果
- A/B/C 分类清单为**常见应用参考模板**（按应用名匹配），遇到清单外应用按判断标准归类即可

## 方法论总览

```
检测(只读扫描) → 五分类决策 → 清理(A类, 黄灯白名单) → 迁移(B类, 状态机) / 专项(S类) → 验证 → 四道门删备份
```

**五分类判断原则**：
- 删了**不影响使用**的 → 直接删除（**A类**：纯缓存/崩溃转储/临时文件；黄灯命令仅限白名单路径）
- 删了**影响使用、但迁移后不影响**的 → Junction 迁移（**B类**：应用数据；走状态机脚本）
- 系统/运行时核心，动不得 → 保持不动（**C类**）
- **用户个人静态文件** → 报告后征求用户选择，确认后才代办（**D类**：桌面/文档/图片/音乐/视频/下载）
- **丢了不可逆的** → 只报告，走专项流程（**S类**：聊天记录/邮件/密码库/含 Login Data 的浏览器数据）

**命令安全分级（文档 + 代码双层强制）**：

| 级 | 命令 | 边界 |
|---|---|---|
| 🟢 绿灯 | 只读命令；`robocopy /E /COPY:DAT /MT:16`（纯复制）；`mklink /J`；`os.rename` | 任意路径 |
| 🟡 黄灯 | `rm -rf` / `shutil.rmtree` / `rmdir /s /q`；`robocopy /MIR` 空目录镜像删除法 | **仅 A 类白名单路径**（`%TEMP%`、`CrashDumps`、`pip\cache`、`SquirrelTemp`、`SoftwareDistribution\Download` 等，见 `common.py` 的 `A_PATH_ALLOW`）+ 用户确认 |
| 🔴 红灯 | `robocopy /MOVE` `/MOV` `/PURGE`；对迁移源/目标/`_backup`/已知文件夹/`$Recycle.Bin`/S类路径的任何删除 | **绝对禁止**。命中 `common.guard()` → `raise GuardError` → exit 3，禁止被 except 吞掉 |

> 为什么写进代码：上一起事故里"仅限 A 类"只是文档里的文字，agent 没遵守。v1.2 起 `guard()`/`guard_a_class()`/`safe_rmtree()`/`mirror_delete()` 是所有破坏性操作的唯一入口，绕不过去。

**D类处理规范**（用户个人数据，三步交互式流程）：
- **第1步 报告**：扫描后列出各已知文件夹的位置+大小（脚本自动完成）
- **第2步 征求选择**：用 AskUserQuestion 给用户选项——① 官方法迁移（推荐）② Junction迁移 ③ 保持不动 ④ 用户自己处理。**未获明确选择前绝不处理**
- **第3步 确认后代办**：用户选了迁移 → agent 列出具体操作清单（源→目标路径）二次确认后执行

**第3步"官方法迁移"的自动化做法**（等价于"属性→位置→移动"的底层操作）：
1. 目标盘建目录 → `robocopy 源 目标 /E /COPY:DAT`（先复制不删源）
2. 验证文件数+大小一致
3. 写注册表 `HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders`（REG_EXPAND_SZ，值用 `%USERPROFILE%` 风格变量指向新路径）
4. 原目录改名 `_backup`（不删）；提示部分应用需重启才感知新位置

**注意事项**：
- OneDrive 备份重定向的文件夹先暂停同步再迁，否则两边打架
- 微信/QQ 默认保存位置常指向文档/桌面，迁移后要同步改软件设置（微信数据见下方专项章节）
- junction 方式对已知文件夹也可行（备选），但官方法的注册表方式软件感知更好

---

## 阶段1：检测（只读，不删不改）

### 1.1 磁盘空间总览
```python
import ctypes
kernel32 = ctypes.windll.kernel32
free = ctypes.c_ulonglong(0); total = ctypes.c_ulonglong(0)
kernel32.GetDiskFreeSpaceExW('C:/', None, ctypes.pointer(total), ctypes.pointer(free))
print(f'C盘: 总{total.value/2**30:.0f}GB, 剩余{free.value/2**30:.2f}GB')
```
注意：bash 里 `python -c` 的 `'C:\\'` 反斜杠会被 shell 吃掉报语法错，用 heredoc 或 `'C:/'`。

### 1.2 目录占用扫描
扫描顺序（优先级从高到低）：
1. `C:\Users\<user>\AppData\Local\Temp` — **先看内容再定**（实测教训：111GB 的 Temp 其实是 1 个 wsl-crashes 崩溃转储 .dmp 文件）
2. `AppData\Local\*` 和 `AppData\Roaming\*` 子目录大小排序（du -sh 或 python os.walk）
3. 用户主目录隐藏目录（`.cache`、`.codebuddy`、`.codebuddycn` 等）
4. `C:\hiberfil.sys` / `pagefile.sys` / `swapfile.sys`
5. `C:\Windows\SoftwareDistribution`、`C:\Windows\Temp`、回收站
6. `C:\ProgramData`（重点看 Anaconda3 的 pkgs 缓存）

大目录扫描耗时，Bash 调用记得加 timeout（300s+），或用 `python os.scandir` 递归统计。

**扫描提速（v1.1 已内置到 scan_c_drive.py）**：
- 顶层子目录大小统计用 `ThreadPoolExecutor`（8 workers）并行——IO 密集型，实测快 3-5 倍
- 单文件大小用 `entry.stat(follow_symlinks=False).st_size`（scandir 迭代 + 少一层系统调用，替代 os.walk + os.path.getsize）
- `--json out.json` 把扫描结果落盘，后续阶段/迁移脚本直接复用，免重复扫描

### 1.3 已有 Junction 检测（避免重复迁移）
```python
import os, ctypes
def is_junction(path):
    attrs = ctypes.windll.kernel32.GetFileAttributesW(path)
    return bool(attrs & 0x400) if attrs != -1 else False  # REPARSE_POINT
# is_junction 为 True 时用 os.readlink(path) 看目标
```

### 1.4 输出检测报告
按 A/B/C 三类汇总成表格（目录、大小、路径、建议动作、所需条件），**先给用户看，确认后再动手**。

---

## 阶段2：分类决策（依据实测沉淀的清单）

### A类：直接清理（删除后自动重建或不影响使用）
| 目标 | 说明 |
|---|---|
| `AppData\Local\Temp\*` | 临时文件。**大文件先 ls 看内容**：wsl-crashes/*.dmp 是崩溃转储可放心删；DiagOutputDir、*-update-*、puppeteer/playwright 临时 profile 都可删；正在使用的文件会锁住，跳过即可 |
| `Temp\wsl-crashes\` | WSL 崩溃转储。**如果反复涨到几十GB，说明容器有问题（实测是 onlyoffice 崩的），要提醒用户查容器** |
| pip 缓存 | `pip cache purge` |
| `.cache`（huggingface 等） | AI 模型缓存，删了下次重新下载，需确认 |
| `SquirrelTemp` | 应用安装器缓存 |
| conda `pkgs` | `conda clean --all`（不要 junction Anaconda3） |
| Windows Update 缓存 | 磁盘清理工具处理 |

### B类：Junction 迁移（实测验证过安全的清单）
| 目录 | 大小 | 注意事项 |
|---|---|---|
| `AppData\Roaming\kingsoft` (WPS) | ~11GB | 关 WPS 全家桶（wps.exe/wpscloudsvr.exe） |
| `AppData\Local\Google` (Chrome) | ~10GB | 关 chrome.exe。**注意：User Data 里含 Login Data 密码库（S类），迁移前 wechat_doctor 式备份或至少备份该文件** |
| `AppData\Roaming\LarkShell` (飞书) | ~6GB | 关 Feishu/Lark。聊天附件属敏感项，先备份 |
| `AppData\Roaming\Code` (VS Code) | ~2GB | 若 VS Code 内嵌于 CodeBuddy，**不能关宿主**，用 python shutil.copytree 容错复制 |
| `AppData\Roaming\TDAppDesktop` (通达信) | ~2GB | **隐藏占用：TencentDocs.exe 拿它当 --user-data-dir** |
| `AppData\Roaming\JetBrains` + `AppData\Local\JetBrains` | ~1.5GB | 两个都要迁 |
| `AppData\Local\Docker\wsl` | ~15GB | 先 `wsl --shutdown`；迁完启动 Docker Desktop 验证 `docker images`；官方替代方案：Docker Desktop Settings → Resources → Disk image location |
| `.codebuddy` / `.codebuddycn` | ~0.6GB | 关 CodeBuddy CN（tasklist 名 "CodeBuddy CN.exe"） |
| 其他：QQ浏览器(QQEX)、钉钉(DingTalk)、Xmind、语雀、夸克、Steam 等 | 各<1.5GB | 同标准流程。钉钉账号数据属敏感项，先备份 |

> ⚠ **v1.2 移除了 `AppData\Roaming\Tencent` 整包**：里面混着 40+ 子应用（QQNT/TIM/企微/微云/腾讯会议/WeType），整包迁移粒度太粗、且含微信数据（S类）。腾讯系按子应用逐个评估，**微信一律走 `wechat_doctor.py`**。

### S类：敏感数据（只报告，绝不自动清理/迁移）
| 特征 | 说明 | 处理 |
|---|---|---|
| `xwechat_files`（含 `db_storage/message_N.db`） | **微信4.x 真正的聊天库**，位置由 `%APPDATA%\Tencent\xwechat\config\51*.ini` 指定，可在任意盘 | `python wechat_doctor.py --detect` 先看它在哪 → 迁移走 `--migrate`（强制备份） |
| `Documents\WeChat Files` | 微信3.x 数据 | 同上 |
| `Outlook\*.ost/.pst` | 邮件数据 | 只报告；迁移先完整备份 |
| `Login Data`（Chrome/Edge） | 浏览器密码库 | 迁移含它的目录前必须备份该文件 |
| `*.kdbx` | KeePass 密码库 | 绝不动 |
| 回收站 `$Recycle.Bin` | 个人数据重灾区 | 见阶段3.5 |

**S 类为什么特殊**：聊天库是加密 SQLite，两份数据**无法合并**——一旦分裂就是永久丢失。所以 S 类迁移必须"强制备份→迁移→复检通过→保留期后才删备份"，缺任何一环都不许动。

### C类：不动
- 系统盘的 `Windows`、`AppData\Local\Microsoft`（Edge/OneDrive/系统组件）
- `AppData\Local\Programs`（应用安装目录，正确做法是卸载重装到数据盘）
- NVIDIA、驱动目录
- **Agent/工具自身运行中的数据目录**（如 `.workbuddy`、`.codebuddy` 等 AI 助手本体目录）：运行中被锁，杀进程即断会话，AI 自己无法完成 → 见"特殊场景"
- Anaconda/Miniconda：路径硬编码，junction 风险高 → 用 `conda clean --all`（pkgs 缓存常可清 ~10GB）或整体卸载/重装

> 注：以上 B 类清单的**目录大小因机器而异**，仅列应用名作参考模板；遇到清单外的新应用，按"应用数据/缓存类 + 可完全关闭"两个标准判断，同样流程处理。

---

## 阶段3：A类清理执行

1. **危险操作规则**：删除前列出完整清单（路径+大小），用户明确确认后才执行
2. **只删 A 类白名单路径**：`%TEMP%`、`CrashDumps`、`pip\cache`、`SquirrelTemp`、`SoftwareDistribution\Download` 等（`common.py:A_PATH_ALLOW`）。清单外的"看起来像缓存"的目录 → 先看内容、降级为 D 类征求用户，**不要凭名字猜**
3. **删除一律走 `common.py` 的受控入口**（它们自带安全门，命中红灯路径会抛 GuardError）：
   - 常规目录：`common.safe_rmtree(path)`
   - 海量小文件/超长路径：`common.mirror_delete(path)`（内部 robocopy /MIR 空目录镜像法，Windows 上删大树最快且天然支持 >260 长路径）
4. **禁止**：对任何目录直接 `rm -rf`（错误被 2>/dev/null 吞掉后你根本不知道删没删成）；对迁移源/目标/备份用 `/MOVE` `/MOV` `/PURGE` `/MIR`
5. 删完复查磁盘空间，汇报释放量

### 阶段3.5：回收站处理规范（v1.2 新增, 事故来源之一）

回收站 = 个人数据。一起真实事故里整体清空回收站丢了 14647 项（含合同 doc、尽职调查手册、Chrome 密码.csv）。

**永远禁止**：`Clear-RecycleBin`、`rd /s /q $Recycle.Bin`、任何形式的整体清空。

**唯一正确姿势**（`scripts/recycle_bin.py`）：
```bash
python scripts/recycle_bin.py --scan --json purge_plan.json   # 列明细: 原始路径/删除时间/大小/是否敏感
python scripts/recycle_bin.py --purge --plan purge_plan.json --i-know <计划条数>   # 逐条删
```
- 明细要给用户看 Top20（**按实际占用排序**）+ 按删除日期分组（≤7天/≤30天/更早）
- **名义大小 ≠ 可释放空间**：`$I` 记录的是删除时的原始大小，`$R` 实体可能早已不在（孤儿记录）。报告必须同时给两个数，只按实际占用（`actual_size`）排优先级
- **疑似敏感文件**（doc/xlsx/pdf/csv/zip/文件名含密码/合同/尽调等）默认排除在清理计划外，用户点名才删
- 默认只清保留期（30天）之前的项；30 天内的建议保留
- 清理计划须经用户确认，`--i-know` 必须等于计划条数（防看都不看就删）

**敏感项的三条通路**（默认全关，必须显式打开才生效）：
```bash
--allow-list "C:\路径\a.docx,C:\路径\b.pdf"   # ① 逐条放开（推荐）
--include-sensitive                            # ② 全部敏感项纳入（危险, 仅当逐条看过明细）
--keep-days 7                                  # ③ 缩短保留期
```
> 计划为空但明明有旧数据时，脚本会打印原因（"N 项因敏感被排除"）并给出上面三条出路 —— 不要因为清不动就改用整体清空。

---

## 阶段4：B类 Junction 迁移标准流程（v1.2 状态机版）

**首选：一键批量迁移脚本 `scripts/migrate_junction.py`**（v1.2 重写：每步落盘的迁移状态机 + 进程关闭二次确认 + 目录锁探测 + Junction 五判据 + 失败安全回滚）：

```bash
# 看计划/续跑建议（只读）
python scripts/migrate_junction.py --dirs kingsoft,google --plan
# 预演（不改任何文件）
python scripts/migrate_junction.py --dirs kingsoft,google --dry-run
# 正式执行（逐目录: 关进程+二次确认 -> 锁探测 -> 两遍robocopy -> 校验 -> 改名 -> 建junction -> 五判据）
python scripts/migrate_junction.py --dirs kingsoft,google --target E --json
# 用户确认应用正常 + 备份过保留期后, 删备份（四道门, 见下）
python scripts/migrate_junction.py --dirs kingsoft --delete-backup --i-know kingsoft --older-than 7
```

- `--dirs` 支持内置短名（kingsoft/google/larkshell/code/tdappdesktop/jetbrains/docker/dingtalk/qqex/xmind/githubdesktop/doubao/steam）或完整路径。**完整路径也能解析进程判据**（v1.1 的"完整路径不杀进程"是事故根因之一，已修）
- **腾讯系整包（tencent）已从短名移除**：粒度太粗且含微信。微信走 wechat_doctor.py，其他腾讯子应用给完整路径
- 清单外应用自动用"目录名"作进程关键字兜底匹配；也可 `--processes "路径关键词=进程1,进程2"` 显式覆盖

### 迁移状态机（防数据分裂的核心）

状态文件在 `%LOCALAPPDATA%\c-drive-cleanup\state\<id>.json`（原子写）。每个目录一条记录，中断后重跑脚本会读状态 + 核对磁盘现状，自动选择续跑动作：

| 上次中断在 | 磁盘现状 | 重跑行为 |
|---|---|---|
| COPYING/COPIED | dst 有部分数据 | **robocopy 增量续跑**（不再"目标已存在就跳过"——v1.1 该逻辑导致中断后永久卡死） |
| VERIFIED_COPY | src/backup/dst 齐全 | 复检锁 → 改名 → 建 junction → 五判据 |
| RENAMED | src 空、backup 有、dst 有 | **跳过复制直接建 junction** |
| JUNCTIONED/JUNCTION_OK | junction 已建 | 五判据复验 / 建议应用复检 |
| SRC_REBUILT | src+backup+dst 三者都在（应用重建了源目录, **事故形态**） | **不自动修**：报告后按微信专项 `--repair` 流程走（增量合并新数据 → 改名 stale → 重建 junction） |
| STUCK_BACKUP_PRESENT | 数据停在 _backup、源位置空 | **exit 4 停下等人工**，绝不自动碰 |

**回滚铁律**：先 `os.rename(backup, src)` 恢复数据，再清理现场；**永不先删任何东西**。回滚失败 → `STUCK_BACKUP_PRESENT` → exit 4。

### 进程关闭与锁探测（事故第一道防线）

1. **进程识别双判据**：主判据 = 进程 ExecutablePath 含应用关键字（`Get-CimInstance Win32_Process`）；辅助 = 映像名清单。进程名随版本变（实测字典里的 `WeChat.exe` 真名是 `Weixin.exe`），**别信写死的名单**，解释器进程全部排除防自杀
2. **关闭后二次确认**：taskkill 后轮询最长 30s，任一进程残留 → **中止该目录，绝不进入复制**
3. **目录锁探测 `probe_lock()`**：①试写+改名往返 ②**目录改名往返**（等2s再改回，杀不干净的进程立刻暴露）③3次快照（文件数/字节/最新mtime）完全一致才算静默。改名前还会再探一次（把"复制→改名"之间的写入窗口压到秒级）

### Junction 五判据验证（杜绝"先判失效后判生效"的翻转）

v1.1 只查 reparse 位——占位符/去重/DFS 同为 0x400、卷瞬时不可达返回 -1，agent 两分钟内判定翻转就是这么来的。v1.2 `check_junction()` 五判据，**UNKNOWN 不算通过**：
①reparse 位（带重试，None=不确定）②`realpath(src)` 归一化 == dst ③穿透 scandir+stat ④**写入探针**（在 src 建临时文件，确认真实落在 dst）⑤dst 文件数 > 0（空链接也是坏的）。任何一条 BROKEN/UNKNOWN → 回滚重来。

### 删备份四道门

`--delete-backup` 必须全过才删，缺一跳过：
①状态机状态 ≥ JUNCTION_OK ②备份与 junction 目标内容比对一致 ③`--i-know <目录末段>` 显式确认 ④备份已过保留期（`--older-than N`，默认 7 天）。

### 手工 8 步（仅脚本不可用时的 fallback）

**目标盘选择规则（通用，不写死盘符）**：
1. 扫描阶段自动枚举 D~Z 全部盘符（`GetLogicalDrives`），验证存在且可写，列出所有可用数据盘
2. 用户明确指定（`--target D`）→ 用用户指定的盘（校验存在，否则回退自动）
3. 未指定 → 自动选**空闲空间最大的非系统盘**
4. **容量校验**：目标盘空闲 ≥ B类待迁移总量 × 1.2 倍；不足时提示只迁移最大的前几项、或先做 A 类清理腾空间
5. 没有 data 盘 → 仅输出扫描结果，跳过迁移环节
6. Junction 统一放在 `<目标盘>:\JunctionData\<目录名>`

```bash
# ① 确认源目录大小
# ② 关闭应用进程（用 Get-CimInstance 按路径关键字找 PID, 杀完轮询确认归零）
# ③ 复制（robocopy 退出码 1=成功；不要用 /COPYALL，需管理员权限会失败）
robocopy "C:\...\X" "D:\JunctionData\X" /E /COPY:DAT /R:3 /W:5 /MT:16 /NFL /NDL /NJH /NJS /NP
# ④ 验证：单遍并发双树比对（文件数+字节数）
# ⑤ 锁探测（改名往返）通过后, 原目录改名 _backup（失败=仍有进程锁，回②）
# ⑥ 建 Junction：subprocess ['cmd','/c','mklink','/J',src,dst]，失败回退 PowerShell New-Item
# ⑦ 五判据验证（reparse/realpath/穿透/写入探针/dst非空）
# ⑧ 启动应用实测，正常后过四道门删 _backup
```

**为什么用 Junction 不用 symlink**：`mklink /D` 符号链接需要管理员权限；Junction 不需要，且本地磁盘间转发功能完全等价。

**目标目录不要预先 mkdir**：已存在的空目录会让 robocopy 报冲突，让 robocopy 自建。

---

## 微信专项（v1.2 新增 —— 必读）

**微信数据不能当普通 B 类迁**，三个实测事实：
1. **聊天库不在你以为的地方**：微信 4.x 数据根由 `%APPDATA%\Tencent\xwechat\config\51*.ini` 里的单行路径指定（可为任意盘任意路径）。实测某机器该 ini 指向 `E:\...\22_Wechat\微信附件`——按旧流程去迁 `Roaming\Tencent\xwechat` 只迁了运行时，聊天库根本没动，这正是数据"分裂"的结构性诱因
2. **进程名随版本变**：主进程是 `Weixin.exe` 不是 `WeChat.exe`；后台还有 `wechat-backend.exe`/`WeChatDataAnalysis.exe`/`WeChatPlayer.exe` 等（不同机器不同版本组合不同）。所以只认"路径含 weixin/wechat 关键字"这个判据，名称清单只作 fallback
3. **聊天库是加密 SQLite**：两份数据无法合并，分裂 = 丢失

**工具 `scripts/wechat_doctor.py`**：
```bash
python scripts/wechat_doctor.py --detect            # 数据位置(读ini)+进程盘点（只读）
python scripts/wechat_doctor.py --migrate --target E  # 强制备份(校验通过才继续) → 关进程(二次确认) → 锁探测 → 迁移
python scripts/wechat_doctor.py --check             # 迁移后五步复检: 穿透/归属/可读/写入探针/静默采样
python scripts/wechat_doctor.py --repair --yes      # SRC_REBUILT 修复（增量合并, 不删任何数据, 须 --yes）
python scripts/wechat_doctor.py --purge-backup --older-than 30 --i-know wechat  # 清强制备份(四道门)
```

**执行纪律**：
- `--detect` 发现数据根**不在 C 盘** → 报告"聊天库不在 C 盘，无需迁移"，结束
- `--migrate` 每个目录先做完整只读备份并**校验通过**，才开始迁移；备份失败/校验不一致 → 取消迁移，源数据未动
- 迁移顺序：先聊天数据根（含 db_storage）→ 再运行时目录，一次一个
- 迁移后：让用户启动微信**亲眼看聊天记录完整** → `--check` 五步全过 → 备份保留 30 天 → 才许 `--purge-backup`

---

## 事故复盘：微信聊天记录丢失 4 天（v1.1 → v1.2 的动因）

用户（2026-08-28~09-01）用 v1.1 清理 C 盘，迁移微信后聊天记录消失。因果链——**每一环都是 skill 设计缺陷，不是 agent 手滑**：

| # | 环节 | 缺陷 | v1.2 对策 |
|---|---|---|---|
| 1 | 扫描判 `Roaming\Tencent\xwechat` 为 B类 | 聊天库其实由 config ini 指向别处，迁的只是运行时 | S类分类 + wechat_doctor 读 ini |
| 2 | 迁移走完整路径入参 | 代码对完整路径返回**空进程列表，一个都没杀** | 完整路径也按关键字解析进程 |
| 3 | 字典写 `WeChat.exe` | 真名 `Weixin.exe`，后台进程全漏 | 路径关键字主判据 + 名称仅 fallback |
| 4 | 杀完 sleep 0.5s 就开工 | 微信自动重启往源目录写了 972MB | kill_and_confirm 轮询 30s + 锁探测 |
| 5 | agent 用 `robocopy /MOVE` | 复制后删源，把"残留"当垃圾搬走 | /MOVE 列入红灯，代码层拦截 |
| 6 | 验证→改名之间分钟级窗口 | 新数据进了 `_backup`，junction 指向旧拷贝 | 锁探测复检压窗口 + 静默快照 |
| 7 | 中断后重跑"目标已存在就跳过" | 永久卡死，junction 始终没建成 | 状态机 + 续跑表 |
| 8 | 单靠 reparse 位判 junction | agent 两分钟内"先判失效、后改口生效" | 五判据 + UNKNOWN 不算通过 |
| 9 | 同会话清空回收站 14647 项 | 合同/密码导出等个人文件全灭 | recycle_bin.py 明细 + 确认门 |

结局：旧数据救回，但 4 天新消息因聊天库加密无法合并，**实质丢失**。

## 踩坑记录（实测）

| 坑 | 解法 |
|---|---|
| bash 里 `cmd /c mklink` 引号转义层层出错 | 用 PowerShell 工具的 `New-Item -ItemType Junction` |
| robocopy `/COPYALL` 报需要管理员权限 | 用 `/COPY:DAT` |
| `taskkill /IM "CodeBuddy CN.exe"` 报"没有找到进程"但其实在杀 | 用双斜杠 `taskkill //F //IM`（git-bash）或 PowerShell 工具 |
| wmic 输出含中文时 python subprocess decode utf-8 崩 | 改用 `tasklist + grep` |
| `mv` 目录报 Permission denied | 有隐藏进程占用：查 tasklist 里应用全家桶（输入法/文档/云服务组件都可能锁） |
| bash 里 `python -c "...'C:\\'..."` 语法错 | 用 heredoc（`python3 << 'PYEOF'`）+ `'C:/'` |
| **Python 3.12+ 检测不到 junction** | `entry.is_dir(follow_symlinks=False)` 对 junction 返回 False，会被扫描脚本静默跳过 → 必须用 `GetFileAttributesW` 的 REPARSE_POINT(0x400) 属性判断 |
| **os.walk 穿透 junction 虚报大小** | 父目录里嵌套 junction（如 Docker\wsl）会把 E 盘数据算进 C 盘 → os.walk 循环里剪枝 junction 子目录 |
| **GetLogicalDrives 位掩码索引** | 盘符对应 bit = `ord(字母)-65`（A=bit0），不要用 enumerate 序号（D 是 bit3 不是 bit0） |
| **盘符参数带不带冒号** | 内部工具函数要兼容 `'E'`/`'E:'`/`'E:/'` 三种写法，统一 rstrip 后再拼路径；否则 `'E:'+'\:/'`=`'E::/'` 静默失败返回 -1 |
| **`--target` 指定不存在的盘** | 必须校验：不存在/不可写时打印警告并回退自动选择 |
| Junction 后应用"以为"还在C盘 | 这是特性不是bug：应用无感，新增文件自动落数据盘 |
| Temp 暴涨先别慌 | 先 ls 看大文件内容，很可能是单个崩溃转储 |
| **批量清缓存的正确姿势（实测对比）** | **以第一层目录为单位试删**：`for entry in "$DIR"/*; do rm -rf "$entry" 2>/dev/null; done`，被占用整目录跳过。不要 ①Python 逐文件容错遍历（几万小文件+Defender 逐个扫，超时且缓冲输出全丢）②先统计大小再删（两遍遍历翻倍）③robocopy 镜像法（对允许部分失败的缓存是杀鸡用牛刀）。Temp/CrashDumps 这类纯缓存直接删；其他目录先看内容 |
| **海量小文件/超长路径大树删除** | 用 **robocopy /MIR 空目录镜像法**（见阶段3）：Windows 原生 API 批量删 + 天然处理 >260 字符长路径。rm -rf 遇长路径静默失败、遇几十万小文件极慢 |
| **bash 调 mklink 引号地狱 → Python 列表参数** | `subprocess.run(['cmd','/c','mklink','/J',src,dst])` 列表形式传参无转义问题；失败再回退 PowerShell `New-Item -ItemType Junction` |
| **迁移验证不要两遍独立 os.walk** | 单遍并发双树比对：一次遍历中同时收集源/目标的 (相对路径,大小) 集合再比对（`migrate_junction.py` 的 `verify_trees`），比两遍 walk 快约一倍 |
| **robocopy 提速参数** | `/MT:16` 多线程 + 同命令跑两遍（第2遍 robocopy 只拷差异, 把第1遍被锁文件补齐, 秒级）。robocopy 退出码 0~7 都算成功, ≥8 才是失败 |
| **OneDrive 占位符会让 readlink 崩** | reparse point（0x400）不都是 junction：OneDrive 占位符 `os.readlink` 抛 **ValueError** 而非 OSError，`_safe_readlink` 要两个都接住 |
| **完整路径入参 = 零杀进程（事故根因）** | v1.1 对完整路径返回空进程列表直接开迁。进程识别必须"路径关键字 + 名称"双判据，完整路径也解析（按父目录名/目录名匹配） |
| **进程名写死必翻车** | 实测字典写 `WeChat.exe` 真名是 `Weixin.exe`；`wetype.exe` 不存在（真名 `wetype_service.exe` 等）。名称只作 fallback，主判据 = 进程 ExecutablePath 含关键字（Get-CimInstance） |
| **taskkill 后必须二次确认** | 杀完 sleep 0.5s 就开工 = 赌运气。轮询最长 30s 直到进程归零，残留即中止 |
| **robocopy /MOVE、/MIR 绝不用于迁移路径** | /MOVE 复制后删源——把应用还在写的数据当垃圾搬走就是分裂。红灯命令只允许黄灯白名单（A类缓存）用 |
| **"目标已存在就跳过" = 中断后永久卡死** | 中断残留（复制一半/已改名未建链接）重跑时会被这条逻辑永久挡住。必须状态机+增量续跑（robocopy 天然只拷差异） |
| **reparse 位单点判定会"翻转"** | GetFileAttributesW 未声明 restype 时返回值不可靠；卷瞬时不可达返回 -1 会被误判"不是 junction"。判定要带重试+UNKNOWN 态，且用写入探针实测数据落点 |
| **`realpath` 比对必须归一化** | 大小写/尾部斜杠/`\\?\` 前缀都会造成假不等；dst 为空串时"穿透访问"恒真——空链接要靠"d st文件数>0"这条判据抓出来 |
| **微信聊天库位置查 config ini** | `%APPDATA%\Tencent\xwechat\config\51*.ini` 单行路径即数据根（编码可能是 utf-8/utf-16/gbk，多分支解码）。ini 指向别的盘 → 聊天库根本不在 C 盘 |
| **回收站绝不能整体清空** | `Clear-RecycleBin` 一把梭 = 14647 项个人文件消失（真实事故）。$I 文件头 8 字节是版本号（v1=int32/v2=int64），v2: size@8、filetime@16、utf-16le 路径@24；非当前用户 SID 目录 PermissionError 跳过 |
| **$I v2 有两种布局，新版是变长**（实测漏扫 2 万项） | 新版 Windows 的 $I 仅 114/196 字节：24字节头 + 4字节路径长度(uint32, **单位=字符数**) + 路径×2字节(utf-16-le, 无填充)，总长 = 28+len×2；旧版是 544 字节定长（520 字节路径 + `\0` 填充）。**判据不能用 `len>=544`**——路径正好 258 字符时 `28+258×2=544` 撞边界，会被误判成定长、解出乱码。正确做法：**自洽性校验优先试探变长**（读 namelen，检查 `28+namelen×2` 是否恰为文件长度或其后仅剩 `\0` 填充），不自洽才退回定长。沙箱 fixture 必须两种布局都造，否则真机新版回收站全军覆没、静默返回 0 项（看着像"回收站是空的"） |
| **A类白名单按前缀匹配 → TEMP 下任何东西都视为可删** | 白名单放行 `%TEMP%` 前缀，意味着**用户放在 TEMP 下的个人文件会被 A 类清理无差别删除**。两个后果：① 清理前必看 TEMP 大文件内容（实测 185GB 的 Temp 其实是 WSL 崩溃转储，但也可能混个人文件）；② **测试沙箱绝不能建在 %TEMP% 下**——实测把沙箱挪到 TEMP 后所有测试路径都命中白名单，安全门形同虚设（T3 的 backup 被真删，连锁毁掉 T5）。沙箱建在 `tests/` 下 |
| **回收站"$I 名义大小"≠ 可释放空间（实测差 44%）** | `$I` 记录的 size 是文件删除时的原始大小，但 `$R` 实体可能已被系统清理/跨盘消失。实测：名义 16.26GB vs **实际占用 9.04GB**，且"保留期前 54 项"里 `$R` 实体存在的**是 0 项**——全是孤儿记录，清了也释放不了 1 字节。报告必须同时给"名义/实际"两个数、`--scan` 的 Top20 按**实际占用**排序，否则用户会为虚账白高兴并误判清理优先级 |
| **自测脚本不应产生任何删除动作** | 两处踩坑：① 结尾 `rmtree(沙箱)` 被安全策略判定为批量删除而中断；② 用"先全量拷再删一半"模拟半程中断，删除动作同样累积触发拦截。正确做法：用 `robocopy /XF <文件列表>` **天然拷出残缺副本**（零删除）；沙箱用带时间戳目录名（不覆盖所以不必删）；跑完保留供勘查 |
| **Bash 的 `rm` 删不了 C 盘文件，且绝不能进回收站** | 两个连环坑：① 本机 `rm` 被 safe-delete shim 接管，它把 `C:/Users/...` 当相对路径拼到 cwd 上（`E:\...\C:\Users\...`），`CanonicalizePath` 失败 → **fail-closed 拒绝删除，文件原样保留**。删 C 盘文件**改用 PowerShell 工具 `Remove-Item -LiteralPath <路径> -Force`**。② 就算 shim 正常工作也不能用——它走回收站（genie-trash），而**回收站本身就在 C 盘**：删 61.7GB 文件送回收站，C 盘空间**一字节都不释放**，还可能撑爆回收站配额。清 C 盘必须**永久删除**（`Remove-Item` 不走回收站），所以更要靠前置的"列清单+用户确认"把关 |
| **WSL 崩溃转储会反复吃掉几十 GB** | `%LOCALAPPDATA%\Temp\wsl-crashes\*.dmp` 是 WSL2 的进程终止转储（实测 61.7GB / 109GB / 74GB）。**dump 大小 ≈ WSL2 VM 当时的内存映射**，不是进程实际占用——没配 `%USERPROFILE%\.wslconfig` 时 WSL2 默认可吃宿主 80% 内存。判据：dump 文件名含容器内进程路径（如 `_var_www_onlyoffice_documentserver_server_tools_pluginsmanager`），但**容器日志正常、Windows 事件日志无任何错误** → 不是真崩溃，是容器/WSL 关闭（shutdown）时进程被终止触发的转储。解法：配 `.wslconfig` 限内存（`[wsl2] memory=8GB`）把 dump 上限压到 8GB；并用 `docker stop` 正常停容器而非强杀。定位时对比 dump 时间戳（UTC）与容器日志的 shutdown 时间 |

## 测试
- `scripts/scan_c_drive.py` 一键检测脚本（阶段1的全部扫描+五分类建议+回收站概览+敏感数据探测），可直接运行验证：
  ```bash
  python scripts/scan_c_drive.py --quick            # 快速模式（只读）
  python scripts/scan_c_drive.py --quick --json out.json   # 结果落盘复用
  ```
- `scripts/migrate_junction.py` 批量迁移脚本（状态机版），`--plan`/`--dry-run` 只读验证：
  ```bash
  python scripts/migrate_junction.py --dirs qqex --plan       # 看计划与续跑建议
  python scripts/migrate_junction.py --dirs qqex --dry-run    # 预演, 不修改任何文件
  ```
- `scripts/wechat_doctor.py` 微信专项（--detect 只读）
- `scripts/recycle_bin.py` 回收站明细（--scan 只读）
- **沙箱自测**（39 项断言，全绿才发布）：
  ```bash
  python scripts/tests/run_selftest.py [沙箱目录]
  ```
  覆盖 T1–T9：完整路径进程判据 / 占用目录 ABORT / 安全门拦截 / 黄灯白名单 / RENAMED·COPIED 残留续跑 / SRC_REBUILT 合并不丢数据 / 回收站解析与确认门 / **$I 双布局兼容（含 258 字符边界）**。

  自测的两条硬规矩（都踩过）：
  1. **零删除动作** —— 半程中断用 `robocopy /XF` 造残缺副本，不用"拷完再删一半"；沙箱用带时间戳目录名，跑完保留不删
  2. **沙箱不能建在 %TEMP% 下** —— 否则所有路径命中 A 类白名单，安全门测试全部假通过
