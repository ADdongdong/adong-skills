# c-drive-cleanup 🧹

Windows C盘空间清理与迁移的 Agent Skill —— 把"检测 → 清理 → 迁移"的完整经验沉淀成可复用的工作流。

## 这是什么

一个 [WorkBuddy](https://www.workbuddy.cn) / Claude 风格的 Agent Skill。安装后，对 Agent 说"帮我清理C盘"，它会按**实测验证过的流程**执行，而不是现场发挥：

```
检测(只读扫描) → 分类决策 → A类清理 → B类Junction迁移 → 验证后删备份
```

## 核心方法论

**三分类决策**（本次对话实测沉淀）：

| 分类 | 判断标准 | 处理方式 |
|---|---|---|
| **A类** | 删了不影响使用（纯缓存/崩溃转储/临时文件） | 直接删除 |
| **B类** | 删了影响使用、但迁移后不影响（应用数据） | Junction 迁移到数据盘 |
| **C类** | 系统核心/运行时依赖（Windows/Microsoft/conda） | 不动 |

**为什么用 Junction 不用 symlink**：`mklink /D` 符号链接需要管理员权限；Junction（目录联接）不需要，且本地磁盘间转发功能完全等价。

## 包含内容

| 文件 | 说明 |
|---|---|
| `SKILL.md` | 完整工作流：五阶段流程、A/B/C实测清单、Junction八步迁移标准流程、**12条踩坑记录** |
| `scripts/scan_c_drive.py` | 一键检测脚本（只读安全）：磁盘总览、目录占用排序、Junction识别、A/B/C分类建议、**目标盘自动探测+容量校验** |
| `scripts/migrate_template.bat` | Junction迁移一键脚本模板（适用于运行中被锁的应用目录，含两遍robocopy+失败自动回滚） |

## 亮点：踩坑驱动的知识

SKILL.md 里每一条"坑"都是真机调试换来的，例如：

- `mklink /D` 符号链接要管理员权限，**Junction 不需要**（本地磁盘场景完全够用）
- 大目录被锁不一定是主进程：**输入法（WeType）、腾讯文档（拿通达信目录当 user-data-dir）** 都会锁
- Python 3.12+ 的 `is_dir(follow_symlinks=False)` 对 junction 返回 False → 必须用 `GetFileAttributesW` 的 reparse 属性判断
- `os.walk` 会穿透 junction 把其他盘的数据算进来 → 必须剪枝
- Temp 目录暴涨先别慌：实测 111GB 的 Temp 其实是**单个 WSL 崩溃转储文件**
- `wmic` 输出中文遇 GBK 会崩 → 改用 `tasklist + grep`
- `robocopy /COPYALL` 要管理员权限 → 用 `/COPY:DAT`

完整清单见 [SKILL.md](SKILL.md) 的踩坑记录表。

## 使用

### 方式一：作为 Agent Skill 安装

把本目录放入 `~/.workbuddy/skills/`（或 `.claude/skills/`），Agent 会根据触发词（清理C盘 / C盘满了 / 迁移到数据盘 / Junction迁移）自动加载。

### 方式二：直接跑检测脚本

```bash
python scripts/scan_c_drive.py            # 完整扫描 + 分类建议
python scripts/scan_c_drive.py --quick    # 快速模式
python scripts/scan_c_drive.py --target D # 指定迁移目标盘
```

输出示例：

```
C盘: 总 343GB | 剩余 191.1GB
迁移目标盘: E: (剩余 129.7GB)   ← 自动选空闲最大的非系统盘

### A类: 可直接清理 ###
   2.44 GB  Temp        临时文件（先看大文件内容）

### B类: 建议Junction迁移到数据盘 ###
  14.70 GB  Docker      （先 wsl --shutdown, 迁 wsl 子目录）

容量校验: B类待迁移 3.4GB | 目标盘 E: 空闲 129.7GB (需≥1.2倍)
✓ 容量充足 (余量 38.4 倍)
```

## 安全性

- 检测脚本**只读**，不删除不修改任何文件
- 清理/迁移前必须列出清单并经用户确认
- 迁移流程自带安全机制：两遍 robocopy（第2遍补齐被锁文件）→ 原目录只改名不删除 → Junction 创建失败自动回滚 → 确认应用正常后才删备份

## 验证记录

本 skill 的迁移流程已在真实机器上完成 **15+ 个目录、约 127GB 数据**的迁移，全部启动验证通过、零事故：WPS、Chrome、QQ/微信/企微、飞书、VS Code、通达信、JetBrains、Docker、CodeBuddy 等。

## License

MIT
