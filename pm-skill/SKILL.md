---
name: pm-skill
description: "产品经理全生命周期管理助手。覆盖从项目初始化、产品发现、策略制定、PRD 生成、执行规划到发布上线的完整工作流。命令：/pm-init, /pm-plan, /pm-execute, /pm-verify, /pm-transition, /pm-next, /pm-research, /pm-prd, /pm-strategy, /pm-release, /pm-req, /pm-ui, /pm-quick, /pm-health, /pm-help, /pm-config, /pm-todo, /pm-wiki。集成 deerflow-skill（Web 研究引擎）和 llm-wiki-skill（知识库引擎）提供专业级调研和知识管理能力。"
---

# PM Skill — 产品经理全生命周期管理助手

产品经理的结构化工作系统，将模糊的产品想法转化为可执行的阶段计划，
通过引导式提问、系统化研究、模板化输出和严格验证，覆盖从 0 到 1 的完整产品生命周期。

**核心理念**: 引导式工作流（Ask → Plan → Execute → Verify → Transition）。
每个阶段都有 BLOCKING gate——你必须停下来等待用户确认，不能一口气冲到底。

**CRITICAL RULE**: 在每个 BLOCKING gate 处 STOP and WAIT for user confirmation。
不要在单轮对话中从规划跳到执行。

---

## 命令清单

所有命令以 `/pm-<name>` 形式调用（如 `/pm-init`、`/pm-plan 1`）。
命令自动加载对应的 workflow 文档。

### 核心生命周期命令（6 个）

| 命令 | 别名 | 功能 |
|------|------|------|
| `/pm-init [project-name]` | `/pm-new` | 初始化 PM 项目：引导提问→需求提取→路线图→创建 .planning/ 结构 |
| `/pm-plan <N>` | `/pm-phase` | 规划阶段 N：加载上下文→阶段讨论→研究→PRD→任务分解→must_haves |
| `/pm-execute <N>` | `/pm-exec` | 执行阶段 N 的所有计划：逐任务读取→产出→验证→记录 |
| `/pm-verify <N>` | `/pm-check` | 验证阶段 N 完成度：must_haves 检查、缺口分析 |
| `/pm-transition` | `/pm-next-phase` | 完成当前阶段→更新上下文→准备下一阶段 |
| `/pm-next` | — | 自动检测当前状态，建议/执行下一步 |

### PM 领域工具命令（6 个）

| 命令 | 功能 |
|------|------|
| `/pm-research <topic>` | 市场/用户/竞品研究：Web 搜索 + wiki 查询 + 综合报告（支持 `--req <id>` 针对性需求调研） |
| `/pm-prd <description>` | 多轮 PRD 生成：发现→wiki 搜索→专家挑战→模板选择→生成→结晶 |
| `/pm-strategy <product>` | 9 区块策略画布工作坊 |
| `/pm-release <version>` | 发布 & GTM 规划 |
| `/pm-req <generate|list|show|update|research|dedup>` | 需求全生命周期管理：提取→去重→台账存储→状态管理→针对性调研 |
| `/pm-ui <desc> --design <spec> [--adjust <file>]` | UI 原型生成：根据需求/阶段生成 HTML 原型，严格遵守设计规范，支持迭代调整 |
| `/pm-quick <task>` | 轻量临时任务（跳过完整生命周期） |

### 工具命令（4 个）

| 命令 | 功能 |
|------|------|
| `/pm-health [--repair]` | .planning/ 目录完整性检查 + 自动修复 |
| `/pm-help [command]` | 显示所有命令或特定命令的详细帮助 |
| `/pm-config [key=value]` | 查看/编辑 .planning/config.json |
| `/pm-todo [add/list/done]` | 项目 TODO 管理 |
| `/pm-wiki <op> [args]` | 桥接到 llm-wiki-skill（编译、查询、检查等） |

---

## 命令-工作流映射

| 命令 | 加载工作流 | 产出物 |
|------|-----------|--------|
| `/pm-init` | `workflows/init-project.md` | PROJECT.md, REQUIREMENTS.md, ROADMAP.md, STATE.md, config.json |
| `/pm-plan <N>` | `workflows/plan-phase.md` | NN-CONTEXT.md, NN-RESEARCH.md, NN-PRD.md, NN-MM-PLAN.md |
| `/pm-execute <N>` | `workflows/execute-plan.md` | NN-MM-SUMMARY.md, PM 交付物（研究报告/PRD/策略画布等）, 更新 STATE.md |
| `/pm-verify <N>` | `workflows/verify-work.md` | NN-VERIFICATION.md |
| `/pm-transition` | `workflows/transition.md` | 更新 PROJECT.md, ROADMAP.md, STATE.md |
| `/pm-research` | `workflows/research.md` | RESEARCH.md |
| `/pm-prd` | `workflows/prd-generation.md` | prd/{name}/v1/prd.md + changelog.md |
| `/pm-release` | `workflows/release-gtm.md` | RELEASE.md, GTM.md |
| `/pm-req` | `workflows/requirement-management.md` | wiki/entities/REQ-XXX.md, 更新 REQUIREMENTS.md, REQ-XXX-RESEARCH.md |
| `/pm-ui` | `workflows/ui-prototype.md` | prototypes/{name}.html |
| `/pm-health` | `workflows/health.md` (来自 spec-skill 模式) | 健康报告 + 自动修复 |
| `/pm-quick` | *(内联轻量)* | 快速计划 + 总结 |

---

## 完整生命周期流程

```
/pm-init "产品名称"
  │  引导式提问（BLOCKING gate）
  │  创建 PROJECT.md / REQUIREMENTS.md / ROADMAP.md / STATE.md / config.json
  │  预设阶段类型：发现 → 策略 → PRD → 执行 → 发布
  ▼
/pm-plan 1（发现阶段）
  │  加载上下文 → 阶段讨论（BLOCKING）→ 研究 → 创建 PLAN.md
  │  BLOCKING gate：确认计划
  ▼
/pm-execute 1
  │  逐任务执行（读取→产出→验证→记录）→ 生成 SUMMARY.md
  │  ├── /pm-req generate competitive-analysis <报告路径>  ← 从竞品分析提取需求
  │  ├── /pm-req research <id>                            ← 针对性需求调研
  │  └── /pm-req list                                      ← 查看需求全景
  ▼
/pm-verify 1
  │  验证 must_haves → 创建 VERIFICATION.md
  │  BLOCKING gate：确认验证结果
  ▼
/pm-transition
  │  更新 ROADMAP.md（阶段 1 完成）→ STATE.md → 准备阶段 2
  │  BLOCKING gate：确认切换
  ▼
/pm-plan 2（策略阶段）→ /pm-execute 2 → /pm-verify 2 → /pm-transition
  ...

📋 并行需求管理轨道（贯穿所有阶段）:
  /pm-req generate <source> → /pm-req list → /pm-req research <id> → /pm-req update <id>
```

## 阶段类型

PM 项目的阶段类型（在 ROADMAP.md 中定义）：

| 阶段类型 | 典型产出 | 适用命令 |
|----------|---------|---------|
| **发现（Discovery）** | 竞品分析、用户画像、市场规模、机会评估 | /pm-research |
| **策略（Strategy）** | 产品愿景、价值主张、商业模式、OKR | /pm-strategy |
| **PRD** | 产品需求文档、用户故事、验收标准 | /pm-prd |
| **执行（Execution）** | 里程碑规划、功能规格、风险预案 | /pm-execute |
| **发布（Release）** | 发布说明、GTM 计划、上线清单 | /pm-release |

## 与 llm-wiki-skill 集成

pm-skill **不重新实现** wiki 功能，而是通过 `/pm-wiki` 桥接命令委托给 llm-wiki-skill。

**检测逻辑**（在需要 wiki 的工作流中执行）：
1. 检查当前工作目录是否有 `.wiki/` 目录（llm-wiki-skill 标记）
2. 检查 `wiki` CLI 是否可用：`which wiki` 或 `python3 -c "import scripts.wiki"`
3. 如未安装，提示用户：

```
此功能需要 llm-wiki-skill（专业级 wiki 引擎）。
安装方法：
  git clone https://github.com/lgwanai/pm-skill ~/.claude/skills/llm-wiki-skill
  # 或通过 Claude Code 插件市场安装

安装后，wiki 功能将自动启用。
```

**集成触点**：
- `/pm-research` → wiki-query 搜索已有知识，新发现结晶回 wiki
- `/pm-prd` → wiki-query 验证需求、检测冲突，PRD 决策结晶回 wiki
- `/pm-strategy` → wiki-query 竞品情报，策略决策结晶回 wiki
- `/pm-wiki compile/query/lint/status` → 直接委托所有 wiki 操作

详见 `references/wiki-integration.md`。

---

## 与 deerflow-skill 集成

pm-skill **不重新实现** Web 研究能力，而是通过 `/pm-research` 等命令驱动 deerflow-skill 执行深度调研。

**三者协作模式**：

| Skill | 角色 | 核心能力 |
|-------|------|----------|
| **pm-skill** | PM 工作流编排 | 生命周期管理、引导式提问、模板化输出、验证 |
| **deerflow-skill** | 研究引擎 | Web 搜索、竞品调研、多步推理、并行子代理 |
| **llm-wiki-skill** | 知识引擎 | 知识编译、混合检索（BM25+向量+图谱）、记忆固化 |

```
/pm-research "竞品分析"
  │
  ├── pm-skill: 引导定义研究范围、问题、深度
  ├── deerflow-skill: /deer --ultra 并行搜索竞品 + 采集信息
  ├── llm-wiki-skill: /wiki-query 搜索已有知识库
  └── pm-skill: 综合 → RESEARCH.md → 结晶回 wiki
```

**检测逻辑**（在需要深度研究时执行）：
1. 检查 `~/.claude/skills/deerflow/` 目录是否存在
2. 检查 `python3 -c "import deerflow"` 是否成功
3. 如未安装，提示用户：

```
此功能需要 deerflow-skill（专业级 Web 研究引擎）。安装方法：
  git clone https://github.com/lgwanai/deerflow-skill ~/.claude/skills/deerflow
  cd ~/.claude/skills/deerflow
  cp config.example.yaml config.yaml
  # 编辑 config.yaml 填入 API keys
  pip install deerflow-harness langchain langchain-anthropic langchain-openai tavily-python httpx pyyaml

安装后重启 Claude Code 即可。详见 https://github.com/lgwanai/deerflow-skill
```

**deerflow 模式选择**：

| 模式 | 命令 | 适用场景 |
|------|------|----------|
| 快速 | `/deer --flash` | 快速事实查询（如"Crunchbase 上 X 公司的融资额"） |
| 标准 | `/deer` | 常规调研（如"搜索 X 领域的最新趋势"） |
| 专业 | `/deer --pro` | 结构化分析、竞品对比 |
| 超级 | `/deer --ultra` | 全面深度调研、多维度并行竞品分析 |

**集成触点**：
- `/pm-research` → 首选 deerflow --ultra 执行 Web 调研，综合后生成 RESEARCH.md
- `/pm-prd`（研究阶段）→ deerflow --pro 补充行业最佳实践
- `/pm-strategy` → deerflow --pro 搜索竞品策略和定位
- 详见 `references/deerflow-integration.md`

---

## 配置

项目配置存储在 `.planning/config.json`。关键设置：

| 设置 | 选项 | 默认值 | 用途 |
|------|------|--------|------|
| `mode` | `interactive`, `yolo` | `interactive` | 每步确认 vs. 自动批准 |
| `granularity` | `coarse`, `standard`, `fine` | `standard` | 阶段粒度（3-5 / 5-8 / 8-12 阶段） |
| `workflow.research` | boolean | `true` | 规划前进行领域研究 |
| `workflow.deerflow_enabled` | boolean | `true` | 启用 deerflow-skill 作为 Web 研究引擎 |
| `workflow.wiki_enabled` | boolean | `true` | 启用 llm-wiki-skill 集成 |
| `workflow.prd_gates` | boolean | `true` | PRD 生成启用 BLOCKING gates |
| `gates.confirm_roadmap` | boolean | `true` | 路线图确认 gate |

完整 schema 见 `templates/config.json`。

---

## 模板 & 模式

所有模板位于 `templates/` 目录。

### 核心规划模板
- `templates/PROJECT.md` — 产品项目简介（愿景、核心价值、约束、关键决策）
- `templates/ROADMAP.md` — 产品路线图（阶段分解、成功标准、进度追踪）
- `templates/STATE.md` — 跨会话状态记忆（位置、决策、阻断项、指标）
- `templates/REQUIREMENTS.md` — 产品需求（含可追溯性矩阵）
- `templates/config.json` — 工作流配置

### 阶段执行模板
- `templates/PLAN.md` — 可执行阶段计划（含 must_haves、XML 任务结构）
- `templates/SUMMARY.md` — 执行总结
- `templates/VERIFICATION.md` — 验证报告
- `templates/RESEARCH.md` — 研究报告
- `templates/STRATEGY.md` — 9 区块策略画布
- `templates/TODO.md` — TODO 面板

### PRD 模板
- `templates/PRD-GENERIC.md` — 通用 PRD 模板（8 章节）
- `templates/PRD-TOB.md` — ToB/后台产品 PRD 模板
- `templates/PRD-TOC.md` — ToC/消费产品 PRD 模板

### 发布模板
- `templates/RELEASE.md` — 发布说明
- `templates/GTM.md` — Go-to-Market 计划

---

## 工作流文档

- `workflows/init-project.md` — 项目初始化：提问→需求→路线图
- `workflows/plan-phase.md` — 阶段规划：上下文→讨论→研究→PRD→计划
- `workflows/execute-plan.md` — 计划执行：读取→产出→验证→记录
- `workflows/verify-work.md` — Must-haves 验证 + 缺口分析
- `workflows/transition.md` — 阶段完成 + 状态更新
- `workflows/research.md` — 独立研究流程
- `workflows/prd-generation.md` — PRD 生成（多轮专家对话）
- `workflows/release-gtm.md` — 发布 & GTM 流程

## 参考资料

- `references/questioning.md` — 产品发现提问策略（改编自 spec-skill）
- `references/verification-patterns.md` — PRD/需求验证模式
- `references/prd-research.md` — PRD 研究方法论（保留自 v2）
- `references/collect.md` — PRD 模板类型检测规则（保留自 v2）
- `references/pm-frameworks.md` — PM 框架图谱（综合参考）
- `references/wiki-integration.md` — llm-wiki-skill 桥接指南
- `references/domain/` — PM 领域能力参考（发现、策略、研究、GTM）

---

## 关键规则

1. **中文优先**: 所有输出使用中文（保留英文专业术语）。
2. **BLOCKING gates 强制执行**: 绝对不要在单轮对话中从研究跳到 PRD 生成。
3. **模板驱动**: 每个产物对应一个模板文件。生成前先读取模板。
4. **知识积累**: 每次研究/PRD 的结论都应通过 llm-wiki-skill 结晶回知识库。
5. **挑战用户**: 你是思考伙伴，不是打字员。质疑模糊需求，揭示隐藏假设。
6. **状态追踪**: 每次关键操作后更新 STATE.md（保持 < 100 行）。
7. **纯 skill 定义**: 不依赖 Python 脚本。Agent 原生能力（Read, Write, Grep, AskUserQuestion）完成所有操作。
