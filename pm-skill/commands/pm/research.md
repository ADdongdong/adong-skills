---
name: pm-research
description: "执行市场/用户/竞品研究。驱动 deerflow-skill 进行 Web 深度调研，结合 llm-wiki-skill 知识库查询，生成结构化研究报告。"
argument-hint: "<topic or file> [--req <id>]"
---

# /pm-research — 产品研究

触发 `pm-skill`，执行产品研究并生成结构化报告。

支持两种模式：
- **宏观研究**：`/pm-research <topic>` — 产品级别的市场/用户/竞品研究
- **需求调研**：`/pm-research --req <id>` — 针对单条需求的深度调研（委托给 `/pm-req research`）

## 用法

```
/pm-research "AI 代码审查工具竞品分析"       # 宏观：竞品格局研究
/pm-research --req REQ-008                    # 微观：单条需求针对性调研
```

## 研究引擎

pm-skill 驱动两个外部 skill 协同完成深度调研：

| Skill | 角色 | 何时使用 |
|-------|------|----------|
| **deerflow-skill** | Web 研究引擎 | Web 搜索、竞品信息采集、多维度并行调研 |
| **llm-wiki-skill** | 知识引擎 | 已有知识库检索、历史研究复用 |

> **如未安装 deerflow-skill**：降级为 Agent 原生 WebSearch（能力有限）。
> 安装：`git clone https://github.com/lgwanai/deerflow-skill ~/.claude/skills/deerflow`
> 详见 `references/deerflow-integration.md`。

## 工作流

1. **定义研究问题** — 参考 `workflows/research.md`：
   - 用户想研究什么？（竞品、市场、用户、技术趋势……）
   - 研究范围和深度？→ 决定 deerflow 模式
   - 输出格式偏好？

2. **确定研究模式**（基于深度）：

| 深度 | deerflow 模式 | 说明 |
|------|--------------|------|
| 快速 | `/deer --flash` | 快速事实查询，无需多步推理 |
| 标准 | `/deer` | 常规 Web 调研，带思考 |
| 深度 | `/deer --pro` | 结构化分析，含规划和任务追踪 |
| 全面 | `/deer --ultra` | 并行子代理各自研究一个维度 |

3. **执行研究**（三引擎协作）：
   - **deerflow-skill**（如有）：`/deer --ultra "深度调研 {研究问题}"`
     - 自动分解为并行子任务（如 5 个子代理各研究一家竞品）
     - 输出结构化调研结果
   - **llm-wiki-skill**（如有）：`/wiki-query "{研究主题}"`
     - 搜索已有实体、概念、关系
     - 补充历史研究结论
   - **Agent 原生 WebSearch**（降级方案）：直接搜索 + WebFetch

4. **综合** — pm-skill 整合三方结果：
   - 交叉验证来源
   - 提炼关键发现和洞察
   - 区分"数据"和"推断"

5. **生成报告** — 遵循 `templates/RESEARCH.md`：
   - 执行摘要
   - 研究对象和方法
   - 主要发现（数据驱动的结论）
   - 竞品/市场/用户详细分析
   - 关键洞察
   - 可执行建议
   - 来源（所有 URL + wiki 引用）

6. **（可选）结晶** — 如 llm-wiki-skill 可用，将关键发现结晶回知识库

## 产出物

- `RESEARCH.md` — 研究报告（工作目录根下或 `.planning/phases/NN-name/`）

## 示例

```
/pm-research "AI 代码审查工具竞品分析"
/pm-research "中国 SaaS 市场 2025-2026 趋势"
/pm-research "Z 世代社交产品用户行为研究"
```

## 研究领域

参考 `references/domain/` 中的领域知识：
- **竞品分析**: `references/domain/market-research.md`
- **用户研究**: `references/domain/discovery-methods.md`
- **市场规模**: TAM/SAM/SOM 方法论
- **技术趋势**: Web 搜索 + 行业报告

## 关键规则

- 优先使用 deerflow-skill 做 Web 调研（能力远超 Agent 原生 WebSearch）
- 所有数据标注来源
- 区分数据（可验证）和洞察（推断）
- 中文输出
