# PRD 生成工作流

## 概述

以产品专家身份执行多轮对话生成 PRD。流程分为 4 个 Phase，每 Phase 之间有 BLOCKING gate。

## 前置条件

- 用户提供了产品需求描述
- 有工作目录（用于存储 PRD 文件）
- （可选）llm-wiki-skill 可用以搜索已有知识库

## 执行步骤

### Phase 1: 研究 & 发现（BLOCKING — 4 Rounds）

参考 `references/prd-research.md` 的详细方法。

**Round 1: 开放发现**

- 读取用户需求，识别清晰的点和模糊的点
- 提出 2-4 个聚焦问题（使用 AskUserQuestion 工具）
- 关键问题角度：
  - 问题 & 用户："谁有这个问题？他们现在怎么解决的？"
  - 成功标准：""做好"是什么样的？怎么衡量？"
  - 核心流程："用户的核心工作流是什么？"
  - 约束："时间、平台、合规、预算方面的限制？"
- **规则**：每次 ≤ 4 个问题，跟随线索深入，不按脚本走

**Round 2: 知识库搜索**

搜索已有 wiki（如可用）：
- 关键词搜索：`rg "关键词" wiki/ -l`
- 实体搜索：`rg "关键词" wiki/entities/ -l`
- 概念搜索：`rg "关键词" wiki/concepts/ -l`
- 交叉引用：读找到的页面，追踪关联链接

报告发现：
```
✅ Wiki 确认: {符合已有知识的需求}
⚠️ Wiki 冲突: {与已有数据/模型矛盾的需求}
🔍 Wiki 缺失: {wiki 没有覆盖的领域}
💡 Wiki 补充: {已有知识能增加的深度}
```

**Round 3: 专家挑战**

从以下角度挑战需求：
1. **逻辑检查**："实时分析需要 T+0 数据，但系统是 T+1 批处理——怎么协调？"
2. **边界情况**："如果商户今天零交易怎么办？"
3. **缺失项**："没提到权限——商家应该看到其他商家的数据吗？"
4. **优先级**："能不能拆成多期？什么是真正的 P0？"

标记：🚩 Blocker / ⚠️ Risk / 💡 Suggestion

**Round 4: 缺口分析**

综合：
- **信息缺口**：用户还必须提供什么？
- **设计缺口**：什么决策过早或不足？
- **验证缺口**：怎么判断 PRD 完整？

**GATE — 研究总结**：

```
## 研究总结

**产品**: {name}
**类型**: {ToC/ToB/Backend/Mini-Program}
**Wiki 覆盖度**: {good/moderate/poor}

### 确认
- {wiki 确认的要点}

### 冲突
- 🚩 {阻塞级冲突}

### 风险
- ⚠️ {风险}  💡 {建议}

### 缺失信息
- {用户需补充的}

---
1. 继续生成 PRD — 信息足够
2. 补充信息 — 让我补充更多细节
3. 深入探讨 — 在特定方面深入研究
```

**STOP. WAIT for user choice（1/2/3）.**

### Phase 2: 模板选择（GATED）

用户选择"继续"后：

1. 根据需求关键词自动检测模板类型（参考 `references/collect.md`）
2. 展示检测结果：
   ```
   我分析你的需求，这是一个 **ToC/ToB/Backend** 产品。
   PRD 将按以下结构编写：
   1. 产品概述
   2. 用户故事
   3. 功能清单
   4. [类型特定章节]
   
   这个模板合适吗？还是需要换一个？
   ```

3. **WAIT for confirmation** — 用户可以覆盖自动检测

### Phase 3: PRD 生成

模板确认后，生成 PRD：

1. 读取对应模板（`templates/PRD-TOB.md` 或 `templates/PRD-TOC.md` 或 `templates/PRD-GENERIC.md`）
2. 填充所有章节：
   - 基于研究对话中的用户输入
   - 基于 wiki 搜索结果
   - 基于专家挑战的结论
3. 规则：
   - **每个章节必须实质化** — 不留 `[placeholder]`
   - **引用 wiki 来源**：`参见: wiki/entities/xxx.md`
   - **表格用真实数据**，不给样例
   - **P0/P1/P2 映射到阶段路线图**
   - **版本信息头**:
     ```
     | 文档版本 | V1.0 |
     | 创建日期 | {date} |
     | 关联阶段 | Phase N |
     ```

4. 写入文件：
   ```
   {workspace}/prd/{project-name}/v1/prd.md
   {workspace}/prd/{project-name}/v1/changelog.md
   ```

### Phase 4: 结晶（知识回流）

PRD 生成后，将关键决策结晶回 wiki（如 llm-wiki-skill 可用）：

1. **新实体**: PRD 中发现的新概念/系统/角色 → 写入 wiki entities
2. **新概念**: PRD 中推导的设计原则/方法论 → 写入 wiki concepts
3. **更新 index/glossary/log**

### Phase N: 修订（版本管理）

用户请求修订：`/pm-prd revise {project-name} {change}`

1. 读取最新版本的 PRD 和 changelog
2. 确定版本号：
   - Major（结构调整、新章节）→ V2.0, V3.0
   - Minor（细节补充、错误修正）→ V1.1, V1.2
3. 应用变更，创建新版本目录
4. 更新 changelog

## 关键规则

- **Phase 1 GATE 是强制的** — 绝不跳过研究直接生成 PRD
- **Phase 2 GATE 是强制的** — 绝不跳过模板确认
- **你是产品专家** — 挑战模糊需求，揭示隐藏假设
- **每个章节实质化** — 不留 `[placeholder]`
- **中文输出**
