# deerflow-skill 桥接指南

> 本文档定义 pm-skill 如何与 deerflow-skill 集成。
> deerflow-skill 是 pm-skill 的**研究引擎**，负责 Web 搜索、竞品分析和深度调研。

---

## 角色分工

| Skill | 角色 | 核心能力 |
|-------|------|----------|
| **pm-skill** | PM 工作流编排 | 生命周期管理、引导式提问、模板化输出、验证 |
| **deerflow-skill** | 研究引擎 | Web 搜索、竞品调研、多步推理、并行子代理 |
| **llm-wiki-skill** | 知识引擎 | 知识编译、混合检索（BM25+向量+图谱）、记忆固化 |

三者协作模式：

```
/pm-research "竞品分析"
  │
  ├── pm-skill: 引导定义研究范围、问题、深度
  │
  ├── deerflow-skill: 执行 Web 搜索 + 竞品信息采集
  │     └── /deer --ultra "深度调研 Top 5 竞品..."
  │
  ├── llm-wiki-skill: 搜索已有知识库
  │     └── /wiki-query "竞品相关..."
  │
  └── pm-skill: 综合结果 → 生成 RESEARCH.md → 结晶回 wiki
```

---

## 检测机制

在需要深度研究的工作流开始时，检测 deerflow-skill 是否可用：

```bash
# 方法 1: 检查 skill 目录
ls ~/.claude/skills/deerflow/ 2>/dev/null

# 方法 2: 检查 CLl (如果 PATH 中已配置)
which deerflow 2>/dev/null

# 方法 3: 检查 deerflow-harness 包
python3 -c "import deerflow" 2>/dev/null
```

## 安装提示

如未检测到 deerflow-skill：

```
⚠️ 此功能需要 deerflow-skill（专业级 Web 研究引擎）。

📦 安装方法：
   git clone https://github.com/lgwanai/deerflow-skill ~/.claude/skills/deerflow
   cd ~/.claude/skills/deerflow
   cp config.example.yaml config.yaml
   # 编辑 config.yaml，填入 API keys（DEEPSEEK_API_KEY + TAVILY_API_KEY）

   pip install deerflow-harness langchain langchain-anthropic langchain-openai tavily-python httpx pyyaml

   安装后重启 Claude Code 即可自动加载。

🔗 详情: https://github.com/lgwanai/deerflow-skill

---
当前操作将在没有 deerflow 增强的情况下继续（使用 Agent 原生 WebSearch）。
```

---

## deerflow-skill 命令速查

| 命令 | 模式 | 适用场景 |
|------|------|----------|
| `/deer --flash <q>` | 快速模式（无思考/规划/子代理） | 快速事实查询 |
| `/deer <prompt>` | 标准模式（思考，无规划） | 常规调研 |
| `/deer --pro <prompt>` | 专业模式（思考 + 规划） | 结构化分析、竞品对比 |
| `/deer --ultra <prompt>` | 超级模式（思考 + 规划 + 并行子代理） | 全面深度调研、多维度竞品分析 |

> `--ultra` 模式下，deerflow 会将复杂任务分解为多个子代理并行执行。
> 例如"深度调研 Top 5 竞品" → 5 个子代理各自研究一个竞品 → 并行完成。

---

## PM 工作流中的集成点

### /pm-research 中的 deerflow 集成

```
1. 研究定义阶段（pm-skill 引导）:
   - 明确研究问题、范围、深度
   - 选择 deerflow 模式:
     - 快速查询 → /deer --flash
     - 标准调研 → /deer
     - 深度分析 → /deer --pro
     - 全面调研 → /deer --ultra

2. 执行研究（deerflow-skill 承担）:
   /deer --ultra "深度调研 {产品领域} 的竞品格局：
   - 识别 Top 5 直接竞品
   - 每家竞品的功能、定价、GTM 策略
   - 市场趋势和关键数据
   - 差异化机会分析"

3. 综合整理（pm-skill 承担）:
   - 将 deerflow 输出整理为 RESEARCH.md
   - 补充 wiki 搜索结果
   - 提炼关键洞察和可执行建议
   - 结晶回 llm-wiki-skill
```

### /pm-prd 中的 deerflow 集成

PRD 研究阶段（Phase 1, Round 2）可用 deerflow 补充 wiki 搜索：

```
# 先用 wiki 搜索内部知识
rg "关键词" wiki/ -l

# 如果 wiki 覆盖不足 → 用 deerflow 补充外部信息
/deer --pro "调研 {需求领域} 的行业最佳实践和常见方案"
```

### /pm-strategy 中的 deerflow 集成

策略制定前用 deerflow 搜索竞品策略：

```
/deer --pro "调研 {竞品A} 和 {竞品B} 的产品策略：
- 他们的目标市场和定位
- 定价模式和盈利方式
- 最近的产品动向
- 用户评价和市场反馈"
```

---

## 典型协作示例

### 场景：新产品竞品调研

```
用户: /pm-research "AI 代码审查工具的竞品分析"

pm-skill:
  → 检测 deerflow-skill: ✅ 可用
  → 检测 llm-wiki-skill: ✅ 可用
  → 确认研究深度: 标准 / 深度

pm-skill 引导研究定义:
  "我们来明确研究范围：
  - 主要竞品: GitHub Copilot Code Review, CodeRabbit, Sourcery, ...
  - 分析维度: 功能、定价、目标用户、差异化
  - 深度: 深度（完整竞品矩阵 + 市场分析）
  我将启动 deerflow-skill --ultra 模式执行并行调研。"

deerflow --ultra 执行:
  → 子代理 1: 研究 GitHub Copilot Code Review
  → 子代理 2: 研究 CodeRabbit
  → 子代理 3: 研究 Sourcery
  → 子代理 4: 研究 DeepSource
  → 子代理 5: 研究 SonarQube
  （并行执行，各自搜索 + 分析）

pm-skill 综合:
  → 读取 deerflow 输出
  → wiki-query 搜索已有竞品知识
  → 生成 RESEARCH.md:
      - 执行摘要
      - 竞品矩阵（5 家 × 6 维度）
      - 关键洞察
      - 差异化建议
  → 结晶回 wiki
```

---

## 配置参考

### deerflow-skill 的 config.yaml 示例

```yaml
# ~/.claude/skills/deerflow/config.yaml

llm:
  provider: deepseek
  model: deepseek-chat
  api_key: ${DEEPSEEK_API_KEY}
  base_url: https://api.deepseek.com

search:
  provider: tavily
  api_key: ${TAVILY_API_KEY}

fetch:
  provider: jina
  api_key: ${JINA_API_KEY}
```

### pm-skill 的 config.json 设置

```json
{
  "workflow": {
    "deerflow_enabled": true,
    "_deerflow_enabled_comment": "启用 deerflow-skill 作为 Web 研究引擎。如未安装，降级到 Agent 原生 WebSearch。"
  }
}
```

---

## 更新指南

- deerflow-skill 升级后更新命令速查
- 新增研究场景 → 追加到集成点
- 中文输出
