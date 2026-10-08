---
name: c-drive-cleanup
description: Windows系统盘(C盘)空间清理与迁移全流程方案。当用户提到"清理C盘"、"C盘满了/空间不足"、"释放磁盘空间"、"迁移到其他盘/数据盘"、"Junction迁移"、"软链接迁移"时使用。核心方法论：检测→分类→清理→迁移→验证，含完整的Windows Junction迁移标准流程、可复用检测脚本与踩坑记录。任何Windows机器可直接使用（路径全部走环境变量，目标盘自动探测）。
agent_created: true
version: "1.0.0"
display_name: "C盘清理与迁移"
display_name_en: "C Drive Cleanup & Migration"
description_zh: "Windows C盘空间清理与Junction迁移全流程：检测扫描→A/B/C分类（直接清理/迁移/不动）→清理执行→Junction八步迁移→验证删备份。含实测沉淀的应用安全清单、隐藏进程占用排查、12条踩坑记录，附一键检测脚本，任何Windows机器可用。"
description_en: "Full workflow for Windows C drive cleanup and Junction migration: read-only scan, A/B/C classification (clean/migrate/keep), cleanup, 8-step junction migration, verify then remove backup. Battle-tested app safety list, hidden process lock diagnosis, 12 pitfalls, one-shot scan script. Works on any Windows machine."
visibility: "public"
---

# Windows系统盘(C盘)清理与迁移全流程

## 通用性说明（任何 Windows 机器可直接使用）
- 脚本通过 `os.path.expanduser('~')` / `%USERPROFILE%` / `%SystemDrive%` 环境变量定位路径，**不依赖任何特定用户名或盘符**
- 迁移目标盘自动探测：`--target D` 指定，或自动选空闲最大的非系统盘；没有数据盘时仅输出扫描结果
- A/B/C 分类清单为**常见应用参考模板**（按应用名匹配），遇到清单外应用按判断标准归类即可

## 方法论总览

```
检测(只读扫描) → 分类决策 → 清理(A类) → 迁移(B类) → 验证后删备份
```

**核心判断原则**（与用户确认过的规则）：
- 删了**不影响使用**的 → 直接删除（A类：纯缓存/崩溃转储/临时文件）
- 删了**影响使用、但迁移后不影响**的 → Junction 迁移（B类：应用数据）
- 系统/运行时核心，动不得 → 保持不动（C类）
- **用户个人静态文件** → 报告后征求用户选择，确认后才代办（D类：桌面/文档/图片/音乐/视频/下载）

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
- 微信/QQ 默认保存位置常指向文档/桌面，迁移后要同步改软件设置
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
| `AppData\Local\Google` (Chrome) | ~10GB | 关 chrome.exe |
| `AppData\Roaming\Tencent` | ~9GB | **隐藏占用：WeType 输入法(wetype_*)、企微 WXWork、腾讯文档 TencentDocs 都会锁** |
| `AppData\Roaming\LarkShell` (飞书) | ~6GB | 关 Feishu/Lark |
| `AppData\Roaming\Code` (VS Code) | ~2GB | 若 VS Code 内嵌于 CodeBuddy，**不能关宿主**，用 python shutil.copytree 容错复制 |
| `AppData\Roaming\TDAppDesktop` (通达信) | ~2GB | **隐藏占用：TencentDocs.exe 拿它当 --user-data-dir** |
| `AppData\Roaming\JetBrains` + `AppData\Local\JetBrains` | ~1.5GB | 两个都要迁 |
| `AppData\Local\Docker\wsl` | ~15GB | 先 `wsl --shutdown`；迁完启动 Docker Desktop 验证 `docker images`；官方替代方案：Docker Desktop Settings → Resources → Disk image location |
| `.codebuddy` / `.codebuddycn` | ~0.6GB | 关 CodeBuddy CN（tasklist 名 "CodeBuddy CN.exe"） |
| 其他：QQ浏览器(QQEX)、钉钉(DingTalk)、Xmind、语雀、夸克、Steam 等 | 各<1.5GB | 同标准流程 |

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
2. 逐项目录删（可批量 rm，但先关占用进程）
3. 删完复查磁盘空间，汇报释放量

### ⚠️ 先确认环境有没有 bulk-delete 守卫（2026-09-15 实测，必读）

在 WorkBuddy / CodeBuddy 这类带安全钩子的环境里，**agent 侧的大批量删除会被直接阻断**，表现为日志里出现：

```
[safe-delete][SAFE_DELETE_BULK_CONFIRM_REQUIRED] {"count":9999,"threshold":50,"scope":"turn",...}
```

- 守卫文件：`<WorkBuddy>/resources/app.asar.unpacked/cli/vendor/shim/safe-delete-bulk-guard.cjs`
- 阈值 50 **文件/轮**，超限 **fail-closed 直接拒绝**（不弹交互确认）
- **只删单文件/小目录（≤50 文件）能过** —— 所以 109GB 的单个 `.dmp` 能删掉，但 npm-cache 这类几万小文件的目录一律被拒
- 换 Python `shutil.rmtree` **同样被拦**（拦截在更底层，不是 shell 层），别浪费时间换工具重试
- 相关 env：`CODEBUDDY_SAFE_DELETE_BULK_THRESHOLD`、`SAFE_DELETE_BULK_STATE_DIR`

**正确处置（不要试图绕过守卫）**：判定标准是"单目录文件数 > 50 且总数大"→ 直接把清理动作**下沉成用户双击的一键脚本**，与"特殊场景：Agent/应用自身数据目录"同一套思路：

```python
# 生成 .bat：必须 CRLF + ASCII，否则 cmd 下中文乱码/标签跳转失败
BAT = '''@echo off
setlocal
for /f %%a in ('powershell -NoProfile -Command "[math]::Round((Get-PSDrive C).Free/1GB,2)"') do set BEFORE=%%a
call :wipe "%LOCALAPPDATA%\\npm-cache" "npm cache"
...
pause
exit /b 0

:wipe
set "TGT=%~1"
if exist "%TGT%" (
  rd /s /q "%TGT%" >nul 2>&1
  if exist "%TGT%" (echo   [SKIP] %NAME% - files in use) else (echo   [ OK ] %NAME%)
) else (echo   [ -- ] %NAME% - not found)
exit /b 0
'''
open(path, 'wb').write(BAT.replace('\n', '\r\n').encode('ascii'))  # 关键：写 bytes
```

脚本要点：`rd /s /q` + `2>nul` 容错、被占用整目录 SKIP、前后用 `Get-PSDrive C` 报空间差、ASCII 无中文。生成后用 present_files 交给用户双击，不要自己 `start` 它。

---

## 阶段4：B类 Junction 迁移标准流程（8步）

**目标盘选择规则（通用，不写死盘符）**：
1. 扫描阶段自动枚举 D~Z 全部盘符（`GetLogicalDrives`），验证存在且可写，列出所有可用数据盘
2. 用户明确指定（`--target D`）→ 用用户指定的盘（校验存在，否则回退自动）
3. 未指定 → 自动选**空闲空间最大的非系统盘**
4. **容量校验**：目标盘空闲 ≥ B类待迁移总量 × 1.2 倍（迁移过程中源数据还在，需要余量）；不足时提示只迁移最大的前几项、或先做 A 类清理腾空间
5. 没有 data 盘 → 仅输出扫描结果，跳过迁移环节
6. Junction 统一放在 `<目标盘>:\JunctionData\<目录名>`（保持命名与源目录一致，方便回溯）

以源目录 `C:\...\X`、目标盘 `D:` 为例：

```bash
# ① 确认源目录大小
# ② 关闭应用进程
taskkill /F /IM <进程名>.exe /T
# 隐藏占用用 CommandLine 扫描（wmic 输出中文遇 GBK 会崩，改用 tasklist+grep）:
tasklist | grep -i -E "应用名关键词"
# ③ 复制（robocopy 退出码 1=成功；不要用 /COPYALL，需管理员权限会失败）
robocopy "C:\...\X" "D:\JunctionData\X" /E /COPY:DAT /R:3 /W:5 /MT:8 /NFL /NDL /NJH /NJS /NP
# ④ 验证：文件数 + 字节数双对比（python os.walk）
# ⑤ 原目录改名（失败=仍有进程锁，回②排查）
mv "C:\...\X" "C:\...\X_backup"
# ⑥ 建 Junction —— 必须用 PowerShell 工具：
New-Item -ItemType Junction -Path 'C:\...\X' -Target 'D:\JunctionData\X'
# ⑦ 验证 junction：reparse 属性 + os.readlink + 穿透访问文件
# ⑧ 启动应用实测（如 docker images），正常后删除 _backup
```

**为什么用 Junction 不用 symlink**：`mklink /D` 符号链接需要管理员权限；Junction 不需要，且本地磁盘间转发功能完全等价。

**目标目录不要预先 mkdir**：已存在的空目录会让 robocopy 报冲突，让 robocopy 自建。

### 特殊场景：Agent/应用自身数据目录（运行中无法直接迁移）
AI/IDE 运行中无法"自杀式"迁移（杀进程即断会话）。沉淀方案：改 `scripts/migrate_template.bat` 模板的三个变量（源目录/目标目录/进程名，源目录用 `%USERPROFILE%` 环境变量不写死用户名），用户双击运行：
```
robocopy 复制(第1遍) → taskkill 杀应用 → robocopy 增量补复制(第2遍) → ren 原目录为 _backup → mklink /J → 日志+失败回滚
```
关键点：两遍 robocopy（第2遍补齐第1遍被锁的文件）；改名失败自动重试；Junction 失败自动回滚改名。

---

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
| **环境内置 bulk-delete 守卫阻断大批量删除** | 单轮 >50 文件即 `SAFE_DELETE_BULK_CONFIRM_REQUIRED` 直接拒绝（fail-closed，无交互确认）；换 Python `shutil.rmtree` 一样被拦。**别重试、别绕**，改成生成"用户双击 .bat"（见阶段3）。反过来说：单个 109GB 的 .dmp 是 1 个文件，<50 所以能直接删 |
| **bash 的 `rm` 被 safe-delete shim 劫持成 trash** | 路径混用 `C:\Users\x\...` 反斜杠 + `/` 会让 trash canonicalize 失败 → `SAFE_DELETE_FAIL_CLOSED`，文件一个没删。**统一用 POSIX 路径 `/c/Users/x/...`**，别用 `$USERPROFILE`（它展开成反斜杠形式） |
| **`du -sh` 大目录在默认 120s 超时下被 SIGTERM** | 统计 GB 级目录别在 bash 前台跑 `du`；用 `run_in_background` + 输出重定向到文件，或改用 Python `os.scandir` 递归并剪枝 junction |
| **Windows `.bat` 中文乱码 / 标签跳转失效** | 必须 **CRLF + ASCII** 写：`open(p,'wb').write(BAT.replace('\n','\r\n').encode('ascii'))`。用 Write 工具写 LF + UTF-8 的 .bat 在 cmd 下会出问题；脚本里注释也用英文 |

## 测试
本 skill 附带 `scripts/scan_c_drive.py` 一键检测脚本（阶段1的全部扫描+分类建议），可直接运行验证。
