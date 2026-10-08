---
name: pm-req
description: "需求全生命周期管理。从竞品分析、会议纪要、用户输入中提取需求，去重&冲突检测，联动 wiki 台账存储，支持状态管理和针对性调研。"
argument-hint: "<generate|list|show|update|research|dedup> [args]"
---

# /pm-req — 需求全生命周期管理

触发 `pm-skill`，管理产品需求的完整生命周期：提取→去重→存储→查看→状态管理→针对性调研。

## 子命令

| 子命令 | 用法 | 功能 |
|--------|------|------|
| `generate` | `/pm-req generate <source-type> <path-or-text>` | 从来源提取需求，去重检测，存储到台账 |
| `list` | `/pm-req list [--status=<s>] [--priority=<p>] [--source=<s>]` | 查看需求列表，支持多维筛选 |
| `show` | `/pm-req show <id>` | 查看单条需求完整详情 |
| `update` | `/pm-req update <id> --status=<s> [--priority=<p>]` | 更新需求状态/优先级 |
| `research` | `/pm-req research <id>` | 针对某条需求做深度调研 |
| `dedup` | `/pm-req dedup` | 全量去重检查 |

---

## 子命令详解

### 1. `/pm-req generate` — 需求提取 & 入库

从各种来源提取需求，自动去重和冲突检测，写入 wiki 台账和 REQUIREMENTS.md。

**来源类型（source-type）**:

| 类型 | 说明 | 示例 |
|------|------|------|
| `competitive-analysis` | 竞品分析报告 | `competitive-analysis .planning/phases/01-discovery/竞品对比分析.md` |
| `meeting` | 会议纪要/录音转写 | `meeting .planning/meetings/2026-06-05.md` |
| `user-text` | 用户直接输入的文字描述 | `user-text "用户需要微信登录、手机号注册、记住密码"` |
| `document` | 任意文档（PRD、研究等） | `document prd/payment/v1/prd.md` |

**工作流**（详见 `workflows/requirement-management.md`）：

1. **读取来源内容** — 来源内容为非结构化文本，不做预处理
2. **识别需求意图 & 逐条结构化** — 严格遵循**三不原则**（参考 `references/requirement-extraction.md`）：
   - **不脑补**：来源没说的，绝不自己填充
   - **不推断**：来源暗示但不明确的，标记 [待确认]
   - **不跳过**：关键字段缺失时，必须标记并让用户确认
3. **完整性校验（强制）** — 逐字段检查：标题、描述、用户价值、优先级、验收标准
   - 关键字段全部确认 → A 组（可直接入库）
   - 有关键字段缺失 → B 组（需补充，逐条向用户确认）
4. **BLOCKING gate 1 — 展示 & 确认**：
   ```
   ✅ 可直接入库（{M} 条）
   ⚠️ 需要你补充信息（{K} 条）← 逐条 AskUserQuestion 确认缺失字段
   ```
5. **BLOCKING gate 2 — 三重校验（强制）**：
   - **去重检查**：相似度 ≥ 85% 疑似重复 → 展示对比 → 等用户决策
   - **冲突检测**：功能互斥/范围矛盾 → 标记 → 等用户决策
   - **状态校验**：默认 pending，检查无异常
   - **三条全部通过才能入库，任一条未通过 → 必须用户决策**
6. **写入台账** — 仅通过三重校验的需求：
   - 写入 wiki entities：`wiki/entities/REQ-XXX.md`
   - 更新 `REQUIREMENTS.md`
   - 更新 wiki index/glossary

**关键规则**：
- 三不原则强制执行：不脑补、不推断、不跳过
- 缺失字段 → AskUserQuestion 确认，不自填
- 去重 + 冲突 + 状态三重校验全部通过才入库
- 入库即干净：新需求必须无冲突、无异常状态
- 中文输出

---

### 2. `/pm-req list` — 需求列表

查看所有需求，支持多种筛选维度。

**筛选参数**：
- `--status=<s>` — 按状态筛选（pending/researching/planned/in-dev/done/on-hold/cancelled）
- `--priority=<p>` — 按优先级筛选（P0/P1/P2）
- `--source=<s>` — 按来源筛选（competitive-analysis/meeting/user-text/document）

**无参数时**显示全部需求总览，按状态分组。

**输出示例**：
```
📊 需求总览 (共 15 条)

📥 待评审 (3):
| ID | 标题 | 优先级 | 来源 | 创建日期 |
|----|------|--------|------|----------|
| REQ-012 | 微信登录 | P1 | user-text | 06-05 |
| REQ-013 | 手机号注册 | P1 | user-text | 06-05 |
| REQ-014 | 自动登录记住密码 | P2 | user-text | 06-05 |

🔍 调研中 (2):
| ID | 标题 | 优先级 | 调研日期 | 调研人 |
|----|------|--------|----------|--------|
| REQ-008 | 实时协作编辑 | P1 | 06-03 | AI |
| REQ-010 | AI 语音降噪 | P0 | 06-04 | AI |

📋 已规划 (6):
...

🚧 研发中 (3):
...

✅ 已交付 (1):
...
```

---

### 3. `/pm-req show <id>` — 需求详情

展示单条需求的完整信息：

```
REQ-008: 实时协作编辑
━━━━━━━━━━━━━━━━━━━━━━

状态: 🔍 调研中
优先级: P1
来源: meeting（2026-05-20 产品评审会）
用户价值: 高 — 目标用户群中 68% 期望协作功能

描述:
支持多人同时编辑同一篇笔记，实时同步内容变更，
包含光标位置显示和冲突解决机制。

用户故事:
作为知识工作者，我希望和团队成员同时编辑一篇会议纪要，
以便实时补充各自记录的要点，避免版本合并的麻烦。

验收标准:
1. 2-5 人同时编辑同一文档不丢内容
2. 其他用户的编辑 3 秒内同步到我的屏幕
3. 网络断开后恢复时自动合并离线编辑

关联需求: REQ-005（笔记结构化）、REQ-011（权限管理）
冲突需求: 无
标签: #协作 #实时同步 #核心体验

调研记录:
- 竞品调研: Notion(CRDT)、飞书(OT)、Google Docs(OT) — 详见 REQ-008-RESEARCH.md
- 技术可行性: CRDT 更适合移动端弱网场景
- 用户验证: 目标用户群 68% 期望协作功能（来源：用户调研报告 v1）

历史:
- 2026-05-20: 创建（来源：产品评审会议纪要）
- 2026-06-03: 状态变更 pending → researching
```

---

### 4. `/pm-req update <id>` — 状态更新

更新需求状态或优先级：

```
/pm-req update REQ-008 --status=planned
/pm-req update REQ-012 --priority=P0
/pm-req update REQ-015 --status=cancelled

✅ REQ-008 状态更新: researching → planned
   备注: 调研完成，纳入 Phase 3 PRD 范围
```

**状态流转规则**：
- `pending → researching`: 开始调研
- `researching → planned`: 调研完成，纳入规划
- `planned → in-dev`: 进入研发（通常由研发侧更新，PM 可手动标记）
- `in-dev → done`: 已交付
- 任意状态 → `on-hold` / `cancelled`: 暂缓或取消

每次状态变更记录时间和备注。

---

### 5. `/pm-req research <id>` — 需求针对性调研

对单条需求进行深度调研，不同于 `/pm-research` 的宏观产品研究。

**工作流**：
1. **加载需求上下文** — 读取需求详情、关联需求、已有调研记录
2. **竞品功能调研** — 搜索竞品在该功能上的实现方式
3. **用户需求验证** — 搜索用户对该功能的期望和痛点
4. **可行性分析** — 技术趋势、实现方案对比
5. **生成调研报告** — 写入 `REQ-XXX-RESEARCH.md`
6. **更新需求状态** — `pending → researching`（如当前为 pending）

**输出示例**：
```
🔍 REQ-008 "实时协作编辑" 调研完成

竞品参考:
- Notion: CRDT 方案，支持离线编辑+在线同步
- 飞书文档: OT 方案，国内协作体验标杆
- Google Docs: OT 方案，协作功能最成熟

差异化机会:
- 移动端弱网场景下的协作体验（竞品多聚焦桌面端）
- 语音笔记场景的实时转写协作（独特场景）

建议: 纳入 Phase 3 PRD，优先级 P1

📄 详细报告: REQ-008-RESEARCH.md
```

---

### 6. `/pm-req dedup` — 全量去重

扫描所有需求，检测疑似重复或高度相似的需求对：

```
🔍 需求去重扫描完成

⚠️ 疑似重复 (2 对):

1. REQ-003 "登录状态持久化" ↔ REQ-014 "自动登录记住密码"
   相似度: 89%（标题）+ 95%（描述语义）
   建议: 合并或明确父子关系

2. REQ-007 "数据导出 CSV" ↔ REQ-019 "报表导出功能"
   相似度: 72%（功能重叠）
   建议: 明确各自范围（CSV vs 多格式？导出 vs 报表？）

选择处理方式: [逐对处理] [全部标记] [忽略]
```

---

## 需求状态模型

```
📥 待评审 (pending)         ← 新提取的需求默认状态
    ↓ /pm-req research
🔍 调研中 (researching)     ← 正在调研可行性、竞品方案
    ↓ /pm-req update --status=planned
📋 已规划 (planned)         ← 已纳入阶段计划
    ↓ （研发侧更新 / PM 手动）
🚧 研发中 (in-dev)          ← 正在开发
    ↓
✅ 已交付 (done)            ← 已完成

⏸️ 暂缓 (on-hold)          ← 暂时搁置（可从任意状态转入）
❌ 已取消 (cancelled)       ← 明确不做（可从任意状态转入）
```

**PM 核心关注**: `pending → researching → planned`（从需求识别到纳入规划）
**追踪关注**: `in-dev → done`（了解研发进度，非 PM 操作）

---

## Wiki 台账集成

需求存储在 llm-wiki-skill 的 `wiki/entities/` 目录中，每条需求是一个结构化实体。

**存储格式**：遵循 `templates/REQUIREMENT-ITEM.md` 模板，含完整 YAML frontmatter。

**集成点**：
- **生成时**: `wiki-query` 查重 → 新需求写入 `wiki/entities/REQ-XXX.md`
- **查看时**: `wiki-query` 语义检索关联需求
- **去重时**: `wiki-query` 语义相似度检测

**降级方案**（无 wiki 时）：
- 需求仅存储在 `REQUIREMENTS.md` 表格中
- 去重依赖标题精确匹配
- 语义检索不可用（提示用户安装 wiki）

详见 `references/wiki-integration.md` § Requirements Ledger。

---

## 产出物

- `wiki/entities/REQ-XXX.md` — 需求实体（如 wiki 可用）
- 更新的 `REQUIREMENTS.md` — 需求可追溯性矩阵
- `REQ-XXX-RESEARCH.md` — 需求针对性调研报告（research 子命令）
- 更新的 wiki index/glossary（如 wiki 可用）

## 关键规则

- 需求提取后不自动入库 — BLOCKING gate 等待用户确认
- 去重不静默合并 — 必须用户决策
- 冲突不静默覆盖 — 必须用户决策
- 每条需求标注来源，保持可追溯性
- Wiki 不可用时自动降级，不阻塞工作流
- 中文输出
