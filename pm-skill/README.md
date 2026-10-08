# PM Skill v3 — 产品经理全生命周期管理助手

产品经理的结构化工作系统。将模糊的产品想法转化为可执行的阶段计划，
通过**引导式提问、系统化研究、模板化输出、严格验证**，
覆盖从 0 到 1 的完整产品生命周期。

---

## 理念

**Ask → Plan → Execute → Verify → Transition**

每个阶段都有 **BLOCKING gate** —— Agent 必须停下来等待你确认，不会一口气冲到底。
Agent 是你的**思考伙伴**，挑战模糊需求，揭示隐藏假设，而不是被动打字员。

---

## 命令详解

### 一、核心生命周期（6 个命令）

按顺序执行，形成完整的 PM 工作闭环：

---

### `/pm-init [产品名称]`

**做什么**：从零开始创建一个 PM 项目。通过引导式对话提取产品愿景、需求和路线图。

**什么时候用**：
- 有新产品想法，想系统化推进
- 需要把模糊的"我想做 X"变成清晰的阶段计划

**使用示例**：

```
/pm-init "AI 驱动的代码审查助手"
```

**交互过程**：
1. Agent 提出 2-4 个问题（如"目标用户是谁？""核心差异化在哪？""有什么时间限制？"）
2. 你回答后，Agent 继续追问，直到理解清晰
3. Agent 展示"产品理解总结"——**等待你确认**
4. 确认后，Agent 展示路线图（如：阶段 1 发现 → 阶段 2 策略 → 阶段 3 PRD → 阶段 4 执行 → 阶段 5 发布）
5. **再次等待你确认**——确认后生成 `.planning/` 目录

**产出物**：

```
.planning/
├── PROJECT.md          # 产品愿景、核心价值、目标用户、约束条件
├── REQUIREMENTS.md     # V1/V2/Out of Scope 需求分类
├── ROADMAP.md          # 5 个阶段的路线图（目标、成功标准、依赖）
├── STATE.md            # 项目状态记忆（当前阶段、决策、待办）
└── config.json         # 工作流配置（可调 gates、粒度等）
```

> 之后你可以随时说「继续」或 `/pm-plan 1` 进入第一阶段规划。

---

### `/pm-plan <阶段编号>`

**做什么**：为指定阶段创建详细执行计划。包括阶段讨论、领域研究和任务分解。

**什么时候用**：
- 完成项目初始化后，准备正式开始第一阶段
- 完成上一阶段后，规划下一阶段

**使用示例**：

```
/pm-plan 1     # 规划阶段 1（通常是"产品发现 & 市场研究"）
/pm-plan 2     # 规划阶段 2（通常是"产品策略 & 定位"）
```

**交互过程**：
1. Agent 加载项目上下文（PROJECT.md、ROADMAP.md、STATE.md）
2. 根据阶段类型，进行**阶段讨论**："这个阶段你最想得到的产出是什么？"
3. **等待你确认**阶段范围
4. Agent 执行**领域研究**：
   - 发现阶段 → 搜索竞品信息、市场规模（WebSearch）
   - 策略阶段 → 研究策略框架、商业模式（WebSearch）
   - 如已安装 llm-wiki-skill → 自动搜索已有知识库
5. Agent 创建 **PLAN.md**：
   - **Must-haves 验证标准**（truths/artifacts/key_links）
   - **任务分解**（2-3 个任务/计划，每个有验收标准）
6. 展示完整计划 → **等待你确认**

**产出物**（在 `.planning/phases/01-discovery/` 下）：

```
01-CONTEXT.md           # 阶段讨论中做出的决策
01-RESEARCH.md          # 竞品分析、用户画像、市场数据
01-01-PLAN.md           # 可执行计划（含验收标准）
```

> **BLOCKING gate**: Agent 会两次停下来等你——确认阶段范围 + 确认执行计划。

---

### `/pm-execute <阶段编号>`

**做什么**：执行已批准的计划。逐任务读取、产出、验证、记录。

**什么时候用**：
- `/pm-plan` 完成且你已确认"继续"后

**使用示例**：

```
/pm-execute 1   # 执行阶段 1 的所有计划任务
```

**交互过程**：
1. Agent 读取 PLAN.md，确认所有依赖已就绪
2. **逐任务执行**：
   - Task 1: 读取参考文件 → 产出（如「搜索 Top 5 竞品并整理分析」）→ 对照验收标准验证 → 记录进度
   - Task 2: 同上
   - 如果任务标记为 `checkpoint:human-verify` → **暂停等你确认**
3. 全完成后生成 SUMMARY.md，更新 STATE.md

**产出物**：

```
01-01-SUMMARY.md        # 执行总结（完成什么、决策、偏差）
实际的交付物文件          # 如竞品分析表、用户画像文档等
```

> 每个任务独立验证，不会批量跳过。产出物必须是实质化文档（无占位符）。

---

### `/pm-verify <阶段编号>`

**做什么**：验证阶段交付物是否满足 PLAN.md 中定义的 must_haves（真相/产物/关键关联）。

**什么时候用**：
- 阶段所有计划执行完成后

**使用示例**：

```
/pm-verify 1    # 验证阶段 1 的产出是否达标
```

**交互过程**：
1. Agent 收集阶段所有 PLAN.md 的 must_haves
2. **自动化检查**：
   - 文件是否存在？（`ls` 检查）
   - 内容是否实质化？（grep 检测 `[待补充]` `TODO` `TBD` 等占位符）
   - 文件长度是否 ≥ 模板预期的 80%？
3. **Must-haves 验证**：
   - Truths: "竞品分析涵盖 5 家竞品" → grep 竞品名 → ✅/❌
   - Artifacts: "RESEARCH.md 存在且 ≥ 50 行" → `wc -l` → ✅/❌
   - Key Links: "PRD 引用了研究中的用户画像" → grep 交叉引用 → ✅/❌
4. 生成 VERIFICATION.md，展示通过/缺口
5. **等待你确认**——尤其有关键缺口时需要你决策

**产出物**：

```
01-VERIFICATION.md       # 验证报告（通过率、缺口分析、修复建议）
```

**验证结果示例**：

```
✅ Truths: 3/3 通过
✅ Artifacts: 2/2 通过
⚠️ Key Links: 1/2 通过 — PRD 未引用 RESEARCH.md 的用户画像数据
🚩 关键缺口: 0   ⚠️ 非关键缺口: 1
建议: 非关键缺口可接受 → 允许 transition
```

---

### `/pm-transition`

**做什么**：完成当前阶段，更新所有项目状态文件，准备进入下一阶段。

**什么时候用**：
- 阶段验证通过后（无关键缺口）

**使用示例**：

```
/pm-transition
```

**交互过程**：
1. Agent 做**完成性检查**：所有 PLAN 都有 SUMMARY？VERIFICATION 无关键缺口？
2. 更新 **PROJECT.md**：需求状态 moved to Validated，追加本阶段决策
3. 更新 **ROADMAP.md**：标记阶段 ✅ Complete + 日期
4. 更新 **STATE.md**：Position 移至下一阶段
5. 展示过渡摘要："阶段 1 完成！下一阶段预览…"
6. **等待你确认**切换

**产出物**：更新的 PROJECT.md、ROADMAP.md、STATE.md

**建议流程**：

```
/pm-transition   # 完成阶段 1
/pm-plan 2       # 开始规划阶段 2
```

---

### `/pm-next`

**做什么**：自动检测当前项目状态，告诉你下一步该做什么。

**什么时候用**：
- 隔了几天回来继续项目，忘了上次做到哪
- 不确定下一步该执行哪个命令

**使用示例**：

```
/pm-next
```

**输出示例**：

```
📍 当前状态: Phase 2 — 有 PLAN.md，无 SUMMARY.md
🚀 建议下一步: /pm-execute 2
```

---

### 二、PM 领域工具（7 个命令）

这些命令可独立使用，也可嵌入生命周期流程。

---

### `/pm-research <研究主题>`

**做什么**：执行结构化产品研究——竞品分析、市场研究、用户画像、技术趋势。
自动使用 WebSearch 搜索，如有 llm-wiki-skill 还会搜索已有知识库。

**什么时候用**：
- 需要了解竞品格局（"市面上的 X 产品有哪些？"）
- 需要估算市场规模（"中国在线教育市场规模多大？"）
- 需要分析用户群体（"谁在用这类产品？痛点是什么？"）
- 独立研究或在 `/pm-plan` 发现阶段自动触发

**使用示例**：

```
/pm-research "AI 代码审查工具竞品分析"
/pm-research "中国 SaaS 市场 2025-2026 趋势"
/pm-research "Z 世代社交产品用户行为"
```

**产出物**：

```
RESEARCH.md             # 在项目根目录或 .planning/phases/NN-name/ 下
```

**研究报告包含**：执行摘要、研究问题、方法论、竞争格局/市场分析/用户画像、关键洞察、可执行建议、数据来源。

**搜索策略**（Agent 自动执行）：
1. WebSearch 多角度搜索（产品名 + 竞品、行业 + 市场规模、用户 + 痛点）
2. 如有 wiki → `wiki query "相关主题"` 搜索已有知识
3. WebFetch 深度读取关键来源
4. 所有数据标注来源，区分"数据"和"洞察"

---

### `/pm-prd <产品描述>`

**做什么**：以产品专家身份执行**多轮对话**生成专业 PRD。
不是简单录单——Agent 会挑战你的假设、搜索知识库、检测冲突。

**什么时候用**：
- 需求已基本清晰，需要输出正式 PRD 文档
- 需要结构化地梳理需求、用户故事、验收标准
- 需要版本管理的 PRD（支持后续修订）

**使用示例**：

```
/pm-prd "做一个商户对账系统，商户可以上传账单、自动匹配交易记录、生成差异报告"
/pm-prd revise 商户对账系统 "增加多币种对账支持"
```

**完整交互过程**（5 个 Phase）：

**Phase 1: 研究 & 发现**（4 轮对话）：
- Round 1 — **开放提问**：Agent 问 2-4 个问题（"对账频率？""差异怎么处理？""权限控制？"）
- Round 2 — **知识库搜索**：搜索 wiki 中是否有相关数据模型、已有需求
- Round 3 — **专家挑战**：Agent 从逻辑、边界、缺失项、优先级角度挑战需求
  - 🚩 "对账匹配规则是什么？模糊匹配还是精确匹配？"
  - ⚠️ "大文件上传（>100MB）怎么处理？"
  - 💡 "建议 V1 只做单币种，V2 加多币种"
- Round 4 — **缺口分析**：综合信息缺口、设计缺口
- **GATE**: Agent 展示「研究总结」 → **等待你选择**（继续生成 / 补充信息 / 深入探讨）

**Phase 2: 模板选择**：
- Agent 自动检测产品类型（ToB/ToC/Backend）
- 展示检测结果和模板结构 → **等待你确认**

**Phase 3: PRD 生成**：
- 写入 `prd/{项目名}/v1/prd.md`（8-9 个章节，全部实质化）
- 写入 `prd/{项目名}/v1/changelog.md`

**Phase 4: 结晶**：
- 如有 wiki，PRD 中的新实体/概念自动回流知识库

**Phase 5: 修订**：
- `/pm-prd revise <项目名> <变更>` → 自动判断 Major/Minor 版本号

**产出物**：

```
prd/商户对账系统/
├── v1/
│   ├── prd.md           # 完整 PRD（产品概述、用户故事、功能清单、边界情况、版本规划…）
│   └── changelog.md     # 版本变更记录
├── v2/                  # Major 修订
└── v1.1/                # Minor 修订
```

> **关键规则**：Agent **绝不**在单轮对话中从提问跳到生成——BLOCKING gate 强制等待。

---

### `/pm-strategy <产品名称或问题>`

**做什么**：9 区块策略画布工作坊。逐步引导你完成产品战略的每个维度。

**什么时候用**：
- 需要明确产品定位和差异化
- 面对多种方向，需要系统化梳理战略取舍
- 为 PRD 阶段提供战略输入

**使用示例**：

```
/pm-strategy "AI 代码审查助手"
/pm-strategy "面向东南亚的跨境支付产品"
```

**交互过程**（Agent 引导你逐一完成 9 个区块）：

1. **愿景 & 目标** — "这个产品 3 年后的愿景是什么？"
2. **目标细分市场** — "优先级最高的用户群体是谁？为什么从这里开始？"
3. **痛点 & 价值** — "用户现在怎么解决这个问题？有什么不满？"
4. **价值主张**（JTBD 格式） — "作为 X，当 Y，我想要 Z，以便 W"
5. **战略权衡** — "你选择不做什么？（好策略 = 学会说不）"
6. **关键指标** — "北极星指标是什么？反指标是什么？"
7. **增长引擎** — "用户怎么发现你的产品？（病毒/使用/UGC/推荐）"
8. **核心能力** — "团队有什么优势？需要建设什么？"
9. **防御 & 护城河** — "如果巨头明天进入，你怎么活下来？"

**产出物**：

```
STRATEGY.md             # 完整策略画布（9 个区块 + 待验证假设清单）
```

---

### `/pm-release <版本号或功能名>`

**做什么**：发布 & Go-to-Market 规划。从发布说明到渠道选择到倒计时清单。

**什么时候用**：
- 产品即将发布，需要系统化的上线计划
- 需要定义目标客户和 GTM 渠道策略

**使用示例**：

```
/pm-release "V1.0 MVP"
/pm-release "AI 自动修复功能"
```

**交互过程**（8 步）：
1. 确认发布范围和级别（🚀 Major / 📦 Feature / 🔧 Minor）
2. 生成**发布说明**（用户视角的功能描述，非技术 Changelog）
3. **沙滩头细分**分析——最先服务哪类用户？
4. **ICP**（理想客户画像）定义——包括"取消资格标准"
5. **消息 & 价值主张**设计——针对不同受众的消息变体
6. **GTM 渠道**选择——入站/出站/付费/社群/合作伙伴/PLG
7. **发布倒计时**——从 D-14 到 D+30 的具体任务
8. **成功指标**——北极星 + 输入指标 + 监控频率

**产出物**：

```
RELEASE.md              # 发布说明（用户视角）
GTM.md                  # GTM 计划（沙滩头、ICP、渠道、倒计时、指标）
```

---

### `/pm-req <操作> [参数]`

**做什么**：需求全生命周期管理。从竞品分析、会议纪要、用户输入中提取需求，自动去重和冲突检测，联动 wiki 台账存储，支持状态管理和针对性调研。

**什么时候用**：
- 竞品分析完成后，想从中提取功能需求
- 开完产品评审会，需要把讨论的功能点整理成需求列表
- 用户/老板给了一段文字描述，需要拆解成结构化需求
- 查看当前所有需求的状态
- 针对某条具体需求做深度调研

**子命令详解**：

**`/pm-req generate <source-type> <path-or-text>`** — 需求提取 & 入库

从指定来源提取需求，自动去重和冲突检测，写入台账。

来源类型：
| 类型 | 说明 | 示例 |
|------|------|------|
| `competitive-analysis` | 竞品分析报告 | `competitive-analysis .planning/phases/01-discovery/竞品对比分析.md` |
| `meeting` | 会议纪要 | `meeting docs/meetings/2026-06-05.md` |
| `user-text` | 用户文字输入 | `user-text "需要微信登录、手机号注册、记住密码"` |
| `document` | 任意文档 | `document prd/payment/v1/prd.md` |

**交互过程**：
1. Agent 读取来源内容
2. 提取候选需求（信号词识别 + 优先级推断）
3. 去重检查（标题匹配 + wiki 语义检索）
4. 冲突检测（逻辑矛盾、范围矛盾）
5. 分三类展示：
   - ✅ 新增 — 可直接入库
   - ⚠️ 疑似重复 — 列出相似已有需求，等用户判断
   - 🚩 冲突 — 标记矛盾，等用户决策
6. **等待用户确认** → 写入 wiki 台账 + REQUIREMENTS.md

**`/pm-req list [--status=<s>] [--priority=<p>] [--source=<s>]`** — 需求列表

按状态分组展示所有需求，支持多维度筛选。

```
/pm-req list                        # 全部需求总览
/pm-req list --status=researching   # 只看调研中的需求
/pm-req list --priority=P0          # 只看 P0 需求
/pm-req list --source=meeting       # 只看会议产生的需求
```

**`/pm-req show <id>`** — 需求详情

展示单条需求的完整信息：描述、用户故事、验收标准、竞品参考、调研记录、变更历史。

**`/pm-req update <id> --status=<s>`** — 状态更新

```
/pm-req update REQ-008 --status=planned        # 调研完成，纳入规划
/pm-req update REQ-012 --priority=P0           # 提升优先级
/pm-req update REQ-015 --status=cancelled       # 明确不做
```

**`/pm-req research <id>`** — 需求针对性调研

对单条需求进行深度调研（竞品功能实现、用户需求验证、可行性分析），不同于 `/pm-research` 的宏观产品研究。

```
/pm-req research REQ-008
# → 调研竞品在该功能上的做法
# → 验证用户需求强度
# → 分析可行性
# → 生成 REQ-008-RESEARCH.md
# → 自动更新状态: pending → researching
```

**`/pm-req dedup`** — 全量去重

扫描所有需求，检测疑似重复的需求对，逐对处理。

**需求状态流转**：
```
📥 待评审 → 🔍 调研中 → 📋 已规划 → 🚧 研发中 → ✅ 已交付
                  ↓ 任意状态 ↓
              ⏸️ 暂缓    ❌ 已取消
```

**产出物**：
- `wiki/entities/REQ-XXX.md` — 需求台账实体（如 wiki 可用）
- 更新的 `REQUIREMENTS.md` — 需求可追溯性矩阵
- `REQ-XXX-RESEARCH.md` — 需求针对性调研报告

**典型流程示例**：
```
/pm-execute 1                          # 完成竞品分析
/pm-req generate competitive-analysis .planning/phases/01-discovery/竞品对比分析.md
                                       # 从竞品分析中提取需求
                                       # Agent 展示候选需求 → 你确认 → 入库
/pm-req list --status=pending          # 查看待评审需求
/pm-req research REQ-008               # 对"实时协作编辑"做针对性调研
/pm-req update REQ-008 --status=planned # 调研完成，纳入 Phase 3 规划
/pm-req list                           # 查看更新后的需求全景
```

> **关键规则**：需求提取后 BLOCKING gate 等用户确认；去重不自动合并；冲突不静默覆盖。Wiki 不可用时自动降级，不阻塞工作流。

---

### `/pm-ui <描述 | --req <id>> --design <规范> [--adjust <文件>]`

**做什么**：根据需求、需求编号或阶段描述生成 HTML 原型。**设计规范是必选项**——每个颜色、字体、圆角、间距、阴影都必须来自规范文件。

**三种模式**：

| 模式 | 用法 | 说明 |
|------|------|------|
| **需求驱动**（推荐⭐） | `--req <id> --design <spec>` | 先检索 wiki 历史页面和相关功能，确认后生成——最智能 |
| 直接描述 | `"描述" --design <spec>` | 从文字描述直接生成 |
| 调整已有 | `--adjust <file> --design <spec>` | 在已有原型上增量修改 |

**设计规范**：

`--design` 参数指向 `design/` 目录下的规范文件：

| `--design` 值 | 对应文件 | 描述 |
|---------------|---------|------|
| `apple` | `design/DESIGN-apple.md` | Apple 风格——SF Pro 字体、Action Blue 单强调色、全幅磁贴布局 |

> 新增规范只需将 `.md` 文件放入 `design/` 目录，即可通过 `--design <文件名不含 .md>` 引用。

**使用示例**：

```
# 需求驱动（推荐）
/pm-ui --req REQ-008 --design apple              # wiki 检索 → 确认 → 生成

# 直接描述
/pm-ui "用户注册页" --design apple
/pm-ui "phase-1 核心页面" --design apple --output prototypes/v2

# 调整已有
/pm-ui "增加搜索栏和筛选面板" --design apple --adjust prototypes/dashboard.html
```

**需求驱动模式交互过程**（`--req`——5 步，含 1 个 BLOCKING gate）：

1. **加载需求** — 从 wiki 台账读取需求详情（描述、用户故事、验收标准、关联功能）
2. **检索历史上下文** — wiki 搜索历史页面/界面 + 扫描已有原型文件 + 读取 PRD 上下文
3. **展示研究报告（BLOCKING Gate）** — 综合展示：需求概要 + 历史功能 + 已有原型匹配度 + 生成方案（调整 vs 新建）→ **等待你决策**
4. **执行生成** — 用户选择后：调整已有原型（确认变更后增量修改）或 创建新原型（融入历史 UI 模式和关联功能）
5. **输出 & 关联** — 写入 `prototypes/{name}.html`，反向更新 wiki 需求条目记录原型路径

**设计约束（硬约束）**：

- ✅ 所有颜色值必须可追溯到规范 Token
- ✅ 所有字体规格必须使用规范 typography Token
- ✅ 所有圆角值必须来自规范 rounded Token
- ✅ 阴影使用严格遵守规范（如 Apple 只有 1 个产品阴影）
- ❌ 禁止自创颜色、字体、圆角、阴影
- ❌ 禁止装饰性渐变（除非规范明确定义）
- ❌ 禁止跳过研究步骤盲目生成（--req 模式）

**产出物**：

```
prototypes/
└── dashboard.html       # 独立 HTML 文件（内联 CSS + JS，无外部依赖）
    # 内含元数据注释：设计规范名、生成时间、需求描述、关联需求编号、历史功能参考
```

---

---

### `/pm-quick <任务描述>`

**做什么**：快速执行一个 PM 任务，跳过完整生命周期。

**什么时候用**：
- 临时查询："帮我查一下 A 产品和 B 产品的功能对比"
- 快速草稿："写一个登录功能的 PRD 草稿"
- 格式转换："把这个功能列表转成用户故事格式"
- 即兴分析："分析一下这个 Landing Page 为什么转化率低"

**使用示例**：

```
/pm-quick "Notion、Confluence、飞书文档的功能对比"
/pm-quick "把这段需求描述转成用户故事"
/pm-quick "这个 SaaS 定价页有什么问题？给出优化建议"
```

**与完整生命周期对比**：

| | `/pm-quick` | 完整流程 |
|---|---|---|
| 确认 Gate | 无 | 多个 BLOCKING gates |
| 计划 | 跳过 | PLAN.md + must_haves |
| 验证 | 跳过 | 自动化 + 人工验证 |
| 状态记录 | 可选 | STATE.md 更新 |
| 适用 | 一次性查询/草稿 | 系统化产品项目 |

---

### 三、工具命令（5 个命令）

---

### `/pm-health [--repair]`

**做什么**：检查 `.planning/` 目录的完整性。`--repair` 自动修复缺失文件。

**使用示例**：

```
/pm-health              # 检查
/pm-health --repair     # 检查并自动修复
```

**检查维度**：
- 结构完整性（必需文件、目录存在？）
- 内容有效性（config.json 是有效 JSON？STATE.md < 100 行？）
- 阶段一致性（ROADMAP 中的阶段数 vs `phases/` 目录数）
- 完成性（每个完成的阶段有 SUMMARY + VERIFICATION？）

**输出示例**：

```
## .planning/ 健康报告
✅ .planning/ 存在
✅ phases/ 存在
✅ PROJECT.md / REQUIREMENTS.md / ROADMAP.md / STATE.md / config.json 全部存在
Phase 1: ✅ Plans(1) ✅ Summary ✅ Verified
Phase 2: ⚠️ Plans(1) ✅ Summary ❌ Verified
总体评分: 8/10
```

---

### `/pm-help [命令名]`

**做什么**：显示所有命令或特定命令的详细帮助。

**使用示例**：

```
/pm-help                # 显示全部 18 个命令
/pm-help init           # 显示 /pm-init 的详细工作流和示例
/pm-help prd            # 显示 /pm-prd 的完整 5 Phase 交互过程
```

---

### `/pm-config [key=value]`

**做什么**：查看或修改 `.planning/config.json` 中的工作流设置。

**使用示例**：

```
/pm-config                      # 查看当前配置
/pm-config mode=yolo            # 改为自动模式（跳过确认 gates，谨慎使用）
/pm-config granularity=fine     # 细粒度阶段（8-12 个阶段）
/pm-config wiki_enabled=false   # 禁用 wiki 集成
```

**常用配置项**：

| 设置 | 可选值 | 作用 |
|------|--------|------|
| `mode` | `interactive` / `yolo` | 每步确认 / 自动批准 |
| `granularity` | `coarse` / `standard` / `fine` | 3-5 / 5-8 / 8-12 阶段 |
| `wiki_enabled` | `true` / `false` | 启用 llm-wiki-skill 集成 |
| `prd_gates` | `true` / `false` | PRD 生成时的 BLOCKING gates |
| `research` | `true` / `false` | 规划前自动研究 |

---

### `/pm-todo <操作>`

**做什么**：管理项目 TODO。支持添加、查看、完成。

**使用示例**：

```
/pm-todo list                               # 查看所有 TODO
/pm-todo add "确认支付渠道的合规要求"         # 添加 TODO
/pm-todo add "补充异常流程的 PRD 章节"        # 再添加一条
/pm-todo done TODO-001                       # 标记完成
```

**优先级**：P0（阻塞当前阶段）/ P1（本阶段内处理）/ P2（可延后）

---

### `/pm-wiki <操作> [参数]`

**做什么**：桥接到 llm-wiki-skill，使用专业的 wiki 知识库引擎。
自动检测是否已安装，未安装时提供安装指引。

**使用示例**：

```
/pm-wiki status                                 # 查看 wiki 统计
/pm-wiki compile "竞品分析报告.md"               # 摄入文档到 wiki
/pm-wiki query "支付网关的架构设计"              # 搜索 wiki 知识库
/pm-wiki lint                                   # wiki 健康检查
/pm-wiki init                                   # 初始化 wiki 目录
```

**安装 llm-wiki-skill**（如未安装）：

```bash
git clone https://github.com/lgwanai/pm-skill ~/.claude/skills/llm-wiki-skill
cd ~/.claude/skills/llm-wiki-skill && pip install -e .
```

> llm-wiki-skill 提供 BM25+向量+知识图谱的多路混合搜索、自动知识结晶、记忆层级固化等能力。详见 [GitHub](https://github.com/lgwanai/pm-skill)。

---

## 典型工作流示例

### 完整项目流程

```
# 1. 从零开始
/pm-init "AI 代码审查助手"
#    → 引导式对话（3-4 轮提问）
#    → 确认产品理解
#    → 展示 5 阶段路线图
#    → 确认 → 生成 .planning/

# 2. 第一阶段：产品发现 & 市场研究
/pm-plan 1
#    → 确认阶段范围
#    → Agent 搜索竞品（GitHub Copilot、CodeRabbit、Sourcery…）
#    → 生成竞品分析报告 + 用户画像
#    → 展示执行计划 → 确认

/pm-execute 1
#    → 执行竞品分析任务
#    → 执行用户研究任务
#    → 生成 SUMMARY.md

/pm-verify 1
#    → 验证竞品报告 ≥ 5 家、用户画像 ≥ 3 个…
#    → 全部通过 ✅

/pm-transition
#    → 阶段 1 完成 → 进入阶段 2

# 3. 第二阶段：产品策略 & 定位
/pm-plan 2
/pm-strategy "AI 代码审查助手"   # 可在 plan 中嵌入策略工作坊
/pm-execute 2
/pm-verify 2
/pm-transition

# 4. 第三阶段：PRD 生成
/pm-plan 3
#    → 或直接用独立命令：
/pm-prd "AI 代码审查助手：自动扫描 PR、给出代码质量建议、支持自定义规则"
#    → 多轮专家对话
#    → 自动检测模板（ToB/开发者工具）
#    → 生成 prd/ai-code-review/v1/prd.md

/pm-execute 3
/pm-verify 3
/pm-transition

# 5. 第四阶段：执行规划 → 第五阶段：发布 GTM
/pm-plan 4 → /pm-execute 4 → /pm-verify 4 → /pm-transition
/pm-plan 5 → /pm-release "V1.0 MVP" → /pm-execute 5 → /pm-verify 5
```

### 快速场景

```
# 场景：只想做个竞品分析，不需要完整项目
/pm-research "国内外 AI 代码审查工具竞品分析"
# → 生成 RESEARCH.md，包含 5+ 竞品深度对比

# 场景：临时写个 PRD 草稿
/pm-quick "写一个用户权限管理的 PRD 草稿，RBAC 模型"
# → 快速生成，不经过完整生命周期

# 场景：隔了一周回来继续
/pm-next
# → 📍 Phase 2 — 有 SUMMARY 无 VERIFICATION → 建议 /pm-verify 2
```

---

## 目录结构

```
pm-skill/
├── SKILL.md                       # 主定义：18 个命令 + 完整工作流
├── README.md                      # 本文档
├── package.sh                     # 打包分发脚本
│
├── design/                        # 设计规范
│   └── DESIGN-apple.md            # Apple 风格设计规范（色彩/字体/组件/布局）
│
├── commands/pm/                   # 18 个斜杠命令
│   ├── init.md                    # /pm-init — 初始化项目
│   ├── plan.md                    # /pm-plan — 规划阶段
│   ├── execute.md                 # /pm-execute — 执行阶段
│   ├── verify.md                  # /pm-verify — 验证阶段
│   ├── transition.md              # /pm-transition — 阶段切换
│   ├── next.md                    # /pm-next — 自动检测下一步
│   ├── research.md                # /pm-research — 产品研究
│   ├── prd.md                     # /pm-prd — PRD 生成
│   ├── strategy.md                # /pm-strategy — 策略工作坊
│   ├── release.md                 # /pm-release — 发布规划
│   ├── ui.md                      # /pm-ui — UI 原型生成
│   ├── quick.md                   # /pm-quick — 快速任务
│   ├── health.md                  # /pm-health — 健康检查
│   ├── help.md                    # /pm-help — 命令帮助
│   ├── config.md                  # /pm-config — 配置管理
│   ├── todo.md                    # /pm-todo — TODO 管理
│   └── wiki.md                    # /pm-wiki — Wiki 桥接
│
├── workflows/                     # 10 个工作流（Agent 按步执行）
│   ├── init-project.md            # 引导提问 → .planning/ 结构
│   ├── plan-phase.md              # 上下文加载 → 讨论 → 研究 → PLAN.md
│   ├── execute-plan.md            # 读 → 实现 → 验证 → 提交
│   ├── verify-work.md             # 自动化检查 + must_haves 验证
│   ├── transition.md              # 阶段完成 → 状态更新
│   ├── research.md                # 多源搜索 → 综合 → 报告
│   ├── prd-generation.md          # 4 轮对话 + 专家挑战 + 结晶
│   ├── requirement-management.md  # 需求提取 → 去重 → 台账 → 状态管理
│   ├── ui-prototype.md            # 加载规范 → 组件映射 → 生成 HTML → 合规检查
│   └── release-gtm.md             # 发布说明 → GTM 渠道 → 倒计时
│
├── templates/                     # 15 个输出模板 + config.json
│   ├── PROJECT.md                 # 产品项目简介
│   ├── REQUIREMENTS.md            # 需求（含可追溯性）
│   ├── ROADMAP.md                 # 产品路线图
│   ├── STATE.md                   # 跨会话状态记忆
│   ├── PLAN.md                    # 可执行计划（含 must_haves）
│   ├── SUMMARY.md                 # 执行总结
│   ├── VERIFICATION.md            # 验证报告
│   ├── RESEARCH.md                # 研究报告
│   ├── STRATEGY.md                # 9 区块策略画布
│   ├── PRD-GENERIC.md             # 通用 PRD（8 章节）
│   ├── PRD-TOB.md                 # ToB/企业产品 PRD
│   ├── PRD-TOC.md                 # ToC/消费产品 PRD
│   ├── RELEASE.md                 # 发布说明
│   ├── GTM.md                     # GTM 计划
│   ├── TODO.md                    # TODO 面板
│   └── config.json                # PM 工作流配置
│
└── references/                    # 11 个领域知识 & 模式参考
    ├── questioning.md             # 产品发现提问策略
    ├── verification-patterns.md   # 验证模式（占位符/grep/交叉引用检测）
    ├── prd-research.md            # PRD 研究方法论（4 轮对话流程）
    ├── collect.md                 # PRD 模板类型自动检测规则
    ├── pm-frameworks.md           # PM 框架图谱（发现/策略/执行/GTM）
    ├── wiki-integration.md        # llm-wiki-skill 桥接指南
    ├── deerflow-integration.md    # deerflow-skill 桥接指南
    └── domain/                    # PM 领域能力参考
        ├── discovery-methods.md   # 产品发现技术
        ├── strategy-frameworks.md # 策略框架
        ├── market-research.md     # 市场研究方法
        └── gtm-patterns.md        # GTM 模式 & 剧本
```

---

## 外部 Skill 集成

pm-skill 驱动两个专业 skill 协同工作，自己不重新实现它们的功能：

| Skill | 角色 | 核心能力 | 安装 |
|-------|------|----------|------|
| **deerflow-skill** | 🔍 研究引擎 | Web 搜索、竞品调研、多步推理、并行子代理 | [GitHub](https://github.com/lgwanai/deerflow-skill) |
| **llm-wiki-skill** | 📚 知识引擎 | 知识编译、混合检索（BM25+向量+图谱）、记忆固化 | [GitHub](https://github.com/lgwanai/pm-skill) |

**协作模式**：

```
/pm-research "竞品分析"
  ├── pm-skill: 引导定义研究范围、问题、深度
  ├── deerflow-skill: /deer --ultra 并行搜索竞品 + 采集信息
  ├── llm-wiki-skill: /wiki-query 搜索已有知识库
  └── pm-skill: 综合 → RESEARCH.md → 结晶回 wiki
```

> 两个外部 skill 均为**可选增强**。如未安装，pm-skill 会降级使用 Agent 原生能力（WebSearch、文件搜索等）。

### 安装 deerflow-skill

```bash
git clone https://github.com/lgwanai/deerflow-skill ~/.claude/skills/deerflow
cd ~/.claude/skills/deerflow
cp config.example.yaml config.yaml
# 编辑 config.yaml 填入 API keys（DEEPSEEK_API_KEY + TAVILY_API_KEY）
pip install deerflow-harness langchain langchain-anthropic langchain-openai tavily-python httpx pyyaml
```

### 安装 llm-wiki-skill

```bash
git clone https://github.com/lgwanai/pm-skill ~/.claude/skills/llm-wiki-skill
cd ~/.claude/skills/llm-wiki-skill && pip install -e .
```

---

## 依赖

零外部 Python 依赖。仅使用 Agent 原生能力：Read、Write、Grep、AskUserQuestion。

**可选增强**：
- [deerflow-skill](https://github.com/lgwanai/deerflow-skill) — Web 研究引擎（搜索、调研、并行代理）
- [llm-wiki-skill](https://github.com/lgwanai/pm-skill) — 知识库引擎（编译、混合检索、记忆固化）

---

## 打包

```bash
./package.sh  # → dist/pm-skill-YYYYMMDD.zip
```

---

## 从 v2 升级

| v2 | v3 |
|----|----|
| `/wiki <path>` | `/pm-wiki compile <path>`（桥接到 llm-wiki-skill） |
| `/prd <desc>` | `/pm-prd <desc>`（保留多轮对话 + 新增 must_haves 验证） |
| — | `/pm-init` → `/pm-plan` → `/pm-execute` → `/pm-verify` → `/pm-transition` |
| — | `/pm-research`、`/pm-strategy`、`/pm-release`、`/pm-quick` |
| — | `.planning/` 目录约定、STATE.md 跨会话状态、BLOCKING gates |
| SKILL.md 单体 (~370 行) | SKILL.md + 18 commands/ + 10 workflows/ + 16 templates/ + 10 references/ + design/ |

---

## 参考

- [spec-skill](https://github.com/anthropics/claude-code) — Ask→Plan→Execute 生命周期管理模式
- [pm-skills](https://github.com/lgwanai/pm-skills) — 65 项 PM 技能的领域框架参考
- [deerflow-skill](https://github.com/lgwanai/deerflow-skill) — Web 研究引擎
- [llm-wiki-skill](https://github.com/lgwanai/pm-skill) — 知识库引擎
- [LLM Wiki v2](https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2) — 知识生命周期方法论
