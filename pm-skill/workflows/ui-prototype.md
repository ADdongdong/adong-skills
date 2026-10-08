# UI 原型生成工作流

## 概述

根据产品需求、阶段描述或需求编号，生成严格遵守指定设计规范的 HTML 原型。
支持三种核心模式：**直接描述生成**（模式 A）、**需求驱动生成**（模式 B）、**调整已有原型**（模式 D）。

**模式 B（`--req`）是最智能的模式——不盲目生成，先通过 wiki 检索历史页面和相关功能，综合展示后再让用户确认方向。**

---

## 设计规范加载（所有模式共用）

### 规范文件结构

设计规范文件位于 `design/DESIGN-{name}.md`。每个规范文件包含：

```yaml
# YAML frontmatter — 结构化 Token
colors:         # 颜色 Token → CSS 值
typography:     # 字体 Token → CSS 属性
rounded:        # 圆角 Token → px 值
spacing:        # 间距 Token → px 值
components:     # 组件规格 → 完整 CSS 属性集
```

加上 Markdown body 中的设计哲学、Do's/Don'ts、响应式规则、布局原则等非结构化约束。

### 加载步骤

1. **读取规范文件**: `design/DESIGN-{name}.md`
2. **解析 YAML frontmatter**: 提取所有结构化 Token
3. **解析 Markdown body**: 提取以下关键信息：
   - 设计哲学（Overview）
   - 布局规则（Layout section）
   - 组件细节（Components section）
   - Do's and Don'ts（强制性约束列表）
   - 响应式断点（Responsive Behavior section）
   - 阴影/深度规则（Elevation & Depth section）
   - 字体替代方案（Typography → Note on Font Substitutes）
4. **构建 Token 映射表**: 将所有 `{token.refs}` 解析为实际 CSS 值

### Token 解析规则

规范文件使用 `{category.token}` 引用语法。例如：
- `{colors.primary}` → `#0066cc`
- `{typography.hero-display}` → `font-family: "SF Pro Display"...; font-size: 56px; ...`
- `{rounded.pill}` → `border-radius: 9999px`
- `{spacing.section}` → `80px`

组件 Token 引用基础 Token：
- `{component.button-primary}` → 展开为完整的 CSS 属性集

**解析算法**:
1. 遍历 YAML 中的所有值
2. 匹配 `{xxx.yyy}` 模式
3. 递归展开直到所有引用变为具体 CSS 值
4. 对 `{colors.xxx}` → hex 字符串
5. 对 `{typography.xxx}` → 5 个 CSS 属性 (font-family, font-size, font-weight, line-height, letter-spacing)
6. 对 `{rounded.xxx}` → border-radius 值
7. 对 `{spacing.xxx}` → px 值

---

## 模式 A：直接描述生成

适用于用户直接描述功能/页面需求，或指定阶段编号。

### Step 1: 解析需求

**输入来源**（按优先级）:
1. 用户直接描述的功能/页面需求
2. Phase 编号：读取 `.planning/phases/NN-name/NN-PRD.md` 和 `NN-MM-PLAN.md`
3. PRD 文件：读取 `prd/{name}/v{N}/prd.md`

**提取内容**:
- 页面/功能名称
- 需要展示的信息架构
- 需要哪些 UI 组件（按钮、卡片、导航、表单等）
- 布局结构（单列、多列、网格、全幅 tile 等）
- 交互需求（点击、hover、表单提交等）

**如果需求描述不清晰**：用 AskUserQuestion 澄清（最多 2 个问题）：
- "这个页面面向什么用户角色？"
- "需要展示哪些关键信息？"
- "有哪些核心操作？"

### Step 2: 组件映射

将需求的 UI 元素映射到设计规范的组件：

| 需求 UI 元素 | → 设计规范组件 | 说明 |
|-------------|--------------|------|
| 主操作按钮 | `button-primary` | 主要 CTA |
| 次要操作 | `button-secondary-pill` | "了解更多"等 |
| 导航 | `global-nav` / `sub-nav-frosted` | 顶部导航 |
| 卡片列表 | `store-utility-card` | 网格布局卡片 |
| 文本链接 | `text-link` | 行内链接 |
| 搜索框 | `search-input` | 搜索输入 |
| 页面底部 | `footer` | 页脚 |
| 全幅内容区 | `product-tile-light/dark/parchment` | Hero / 功能展示区 |

**如果需求中某 UI 元素在规范中没有对应组件**:
1. 使用基础 Token（颜色、字体、圆角、间距）构建
2. 严格遵循 Do's/Don'ts 约束
3. 在生成的 HTML 注释中标注 "自定义组件——规范中无对应组件，基于基础 Token 构建"
4. Style 必须与已有组件协调一致

### Step 3: 布局设计

**通用布局原则**（基于设计规范）:
1. 内容最大宽度按规范定义（如 Apple 规范: ~980px 文本, ~1440px 产品网格）
2. 垂直节奏按规范的 spacing 系统
3. 移动优先或桌面优先取决于规范的响应式策略
4. 节与节之间的分隔优先使用颜色交替（而非边框/阴影）

**布局草图**（生成前在心里构建）:
```
┌──────────────────────────────────────┐
│  global-nav (44px)                   │
├──────────────────────────────────────┤
│  sub-nav / 页面标题 (52px)           │
├──────────────────────────────────────┤
│                                      │
│  Hero / 主内容区                      │
│  (product-tile / 自定义布局)          │
│                                      │
├──────────────────────────────────────┤
│  功能卡片区                           │
│  (store-utility-card grid)           │
│                                      │
├──────────────────────────────────────┤
│  详细信息区                           │
│                                      │
├──────────────────────────────────────┤
│  footer                              │
└──────────────────────────────────────┘
```

### Step 4: 代码生成

#### 4.1 HTML 结构

生成的 HTML 必须是**独立的单文件**，包含：
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{页面名称} — {设计规范名称} 原型</title>
  <!--
    PM-Skill UI Prototype
    设计规范: {design-spec-name}
    生成时间: {timestamp}
    需求描述: {requirement-summary}
    关联需求: {REQ-IDs}          ← 如来自 --req 模式
    规范文件: design/DESIGN-{name}.md
    历史功能参考: {wiki-refs}     ← 如来自 --req 模式
  -->
  <style>
    /* 所有 CSS 在此 */
  </style>
</head>
<body>
  <!-- 所有 HTML 在此 -->
</body>
</html>
```

#### 4.2 CSS 生成规则

**强制性规则——每个 CSS 值必须可追溯到设计规范 Token**:

**颜色**:
```css
/* ✅ 正确: 来自规范 Token */
color: #0066cc;           /* {colors.primary} */
background-color: #f5f5f7; /* {colors.canvas-parchment} */

/* ❌ 错误: 自创颜色 */
color: #0088dd;           /* 规范中不存在! */
background: linear-gradient(...); /* 规范禁止! */
```

**字体**:
```css
/* ✅ 正确: 来自规范 Token */
.hero {
  font-family: "SF Pro Display", system-ui, -apple-system, sans-serif;
  font-size: 56px;
  font-weight: 600;
  line-height: 1.07;
  letter-spacing: -0.28px;
}

/* ❌ 错误: 自创字体组合 */
.title {
  font-size: 48px;        /* 规范中没有此尺寸! 用 56px (hero-display) 或 40px (display-lg) */
  font-weight: 700;       /* 规范没有 700! 用 600 */
}
```

**圆角**:
```css
/* ✅ 正确: 来自规范 Token */
border-radius: 18px;      /* {rounded.lg} */
border-radius: 9999px;    /* {rounded.pill} */
border-radius: 0;         /* {rounded.none} */

/* ❌ 错误: 自创圆角 */
border-radius: 10px;      /* 规范 Token 中没有 10px! */
```

**间距**:
```css
/* ✅ 正确: 来自规范 Token */
padding: 80px 0;          /* {spacing.section} */
gap: 24px;                /* {spacing.lg} */
margin-bottom: 48px;      /* {spacing.xxl} */

/* ❌ 错误: 自创间距 */
padding: 60px 0;          /* 规范 spacing 中没有 60px! 用 48px 或 80px */
```

**阴影**:
```css
/* ✅ 正确: 严格使用规范定义的唯一阴影 */
box-shadow: rgba(0, 0, 0, 0.22) 3px 5px 30px 0;

/* ❌ 错误: 自创阴影 */
box-shadow: 0 2px 8px rgba(0,0,0,0.15);  /* 规范中不存在! */
```

#### 4.3 交互状态

按规范定义交互状态：
```css
/* 默认按钮 */
.btn-primary {
  background-color: #0066cc;
  color: #ffffff;
  border-radius: 9999px;
  padding: 11px 22px;
  /* ... */
}

/* Active/Press: scale(0.95) — 按规范定义 */
.btn-primary:active {
  transform: scale(0.95);
}

/* Focus: 2px solid primary-focus — 按规范定义 */
.btn-primary:focus-visible {
  outline: 2px solid #0071e3;
  outline-offset: 2px;
}

/* Hover: 规范如无定义，使用微妙的亮度变化 */
.btn-primary:hover {
  filter: brightness(1.05);
}
```

**重要**: 如果规范未定义 Hover 状态，使用 `brightness(1.05)` 或 `opacity(0.9)` 作为默认 Hover 反馈。不得自创复杂的 Hover 动画。

#### 4.4 JavaScript（最小化）

仅添加功能性交互所需的 JS：
- 导航切换（hamburger menu）
- 表单验证
- Tab 切换
- 简单的显示/隐藏

所有 JS 内联在 `<script>` 标签中，不引入外部库（除非规范明确要求）。

#### 4.5 响应式

按规范的响应式断点生成：
```css
/* 按规范定义的断点 */
@media (max-width: 1068px) { /* small desktop */ }
@media (max-width: 833px)  { /* tablet */ }
@media (max-width: 640px)  { /* phone */ }
@media (max-width: 419px)  { /* small phone */ }
```

响应式行为遵守规范的 Collapsing Strategy。

### Step 5: 设计合规检查（自查清单）

生成代码后，逐项检查：

- [ ] 所有颜色值来自规范 Token？有无自创颜色？
- [ ] 所有字体尺寸来自规范 typography Token？有无偏离尺寸？
- [ ] 所有圆角值来自规范 rounded Token？有无中间值？
- [ ] 所有间距值来自规范 spacing Token？有无自创间距？
- [ ] 阴影使用严格遵守规范？有无额外阴影？
- [ ] 有无使用渐变？（如果规范禁止）
- [ ] 字体族是否正确？有无遗漏 fallback？
- [ ] 交互状态是否按规范定义实现？
- [ ] 按钮圆角是否匹配其语义（pill → 9999px, utility → sm, card → lg）？
- [ ] Body copy 行高是否 ≥ 规范定义的最小值？
- [ ] 响应式断点是否匹配规范？

### Step 6: 输出（BLOCKING Gate）

**BLOCKING Gate**: 展示原型摘要 → 等待用户确认。

输出摘要应包含：
- **页面名称**和文件路径
- **使用的设计规范**
- **使用的关键组件**: 列出规范组件和 Token
- **自定义部分**: 标注任何规范外构建的组件（含理由）
- **设计合规状态**: 自查结果

**用户确认后**：
1. 写入 `prototypes/{name}.html`（或用户指定的路径）
2. 返回文件绝对路径

---

## 模式 B：需求驱动生成（`--req <id>`）

**这是核心智能模式。在生成一行代码之前，先通过 wiki 充分检索历史页面、相关功能、已有原型，然后用结构化的研究报告让用户做决策。绝不跳过研究步骤盲目生成。**

### Step 1: 加载需求详情

**1.1 优先从 wiki 台账读取**（如 llm-wiki-skill 可用）:

```
/wiki-query "REQ-XXX"  → 获取需求实体完整内容
```

需求实体包含：
- 标题和描述
- 用户故事（As a… I want… So that…）
- 验收标准（Acceptance Criteria）
- 优先级（P0/P1/P2）
- 状态（pending/researching/planned/in-progress/delivered）
- 关联功能模块
- 竞品参考
- 调研记录（如有 REQ-XXX-RESEARCH.md）

**1.2 降级方案**（wiki 不可用）:

- 读取 `.planning/REQUIREMENTS.md`，grep 该需求编号对应的条目
- 读取 `wiki/entities/REQ-XXX.md`（如 wiki 目录存在但 CLI 不可用，直接用 Read）
- 读取 `REQ-XXX-RESEARCH.md`（如存在，获取调研上下文）

### Step 2: 检索历史上下文

**这是关键步骤——在生成任何代码前，做充分的多维度检索。**

#### 2.1 Wiki 全量检索（llm-wiki-skill）

搜索三个维度：

**维度 1 — 历史页面 & 界面**:
```
/wiki-query "页面 界面 原型 前端 {需求关键词1} {需求关键词2}"
/wiki-query "UI wireframe mockup {需求核心功能}"
```
目的：发现已有页面、已设计的界面、已讨论的 UI 方案。

**维度 2 — 相关功能模块**:
```
/wiki-query "{需求关联功能} 功能模块 页面结构"
/wiki-query "{产品名} 导航结构 信息架构"
```
目的：理解该功能在产品整体信息架构中的位置，避免生成孤立的"无上下文页面"。

**维度 3 — 已有原型引用**:
```
/wiki-query "prototype html {需求关键词}"
/wiki-query "原型文件 页面 {需求核心功能}"
```
目的：检查 wiki 中是否记录了已有原型文件路径。

#### 2.2 本地原型文件扫描

**扫描 `prototypes/` 目录**:
```bash
ls prototypes/*.html 2>/dev/null
```

**读取每个原型的元数据注释**（前 20 行）:
```bash
head -20 prototypes/*.html | grep -E "(需求描述|关联需求|设计规范|生成时间)"
```

**匹配分析**:
- 检查原型关联的需求编号是否与当前需求相关
- 检查原型描述是否覆盖当前需求的全部/部分功能
- 计算功能覆盖率：高 (>70%) / 中 (30-70%) / 低 (<30%)

#### 2.3 阶段文档检索

**查找需求在 PRD 中的原始定义**:
```bash
grep -r "REQ-XXX" .planning/phases/ prd/ --include="*.md" -l
```

**提取相关章节**:
- 该需求在 PRD 中属于哪个模块/章节
- 同模块下还有哪些关联需求（它们可能共享同一个页面）
- PRD 中对该功能的界面描述、交互要求

#### 2.4 竞品/调研资料检索

```
/wiki-query "{需求关键词} 竞品 最佳实践 UI 交互"
```

或读取 `REQ-XXX-RESEARCH.md` 中的竞品调研部分。

### Step 3: 综合 & 决策（BLOCKING Gate #1 — 强制执行）

**将以上所有检索结果综合为一份结构化的「生成前研究报告」，展示给用户。**

Agent 必须输出以下格式的研究报告：

```markdown
# {REQ-ID} 原型生成前研究

## 1. 需求概要
- **编号**: {REQ-ID}
- **标题**: {需求标题}
- **描述**: {需求描述}
- **优先级**: {P0/P1/P2} | **状态**: {当前状态}
- **用户故事**: {用户故事}
- **验收标准**:
  - AC1: ...
  - AC2: ...

## 2. Wiki 检索结果

### 2.1 历史相关功能（找到 N 个）
| 功能/实体 | 关联度 | 说明 |
|-----------|--------|------|
| {实体名 1} | 高/中/低 | {该功能与当前需求的关系} |
| {实体名 2} | 高/中/低 | ... |

### 2.2 相关页面/界面引用（找到 M 个）
| 页面 | 关联度 | 来源 |
|------|--------|------|
| {页面描述} | 高/中/低 | {wiki 实体 / PRD 章节} |

### 2.3 历史 UI 模式（如发现）
- {产品中已有的 UI 交互模式}
- {规范中已使用的组件组合}

## 3. 已有原型检查

### 3.1 扫描结果
| 原型文件 | 关联需求 | 功能覆盖率 | 操作建议 |
|----------|----------|-----------|----------|
| prototypes/xxx.html | REQ-XXX, REQ-YYY | 70% | ⭐ 建议在此基础上调整 |
| prototypes/yyy.html | REQ-ZZZ | 20% | 仅作参考 |

### 3.2 综合判断
- ✅ **找到高匹配原型**: prototypes/xxx.html（覆盖率 ~70%）
  → **推荐操作**: 在现有原型上增量调整，增加 {缺失的功能}
- 或
- ❌ **未找到匹配原型**
  → **推荐操作**: 新建原型页面

## 4. PRD 上下文

### 4.1 需求在 PRD 中的位置
- **PRD 章节**: {章节名}
- **所属模块**: {模块名}
- **关联需求（同模块）**: REQ-AAA, REQ-BBB, REQ-CCC
  → 这些需求可能共享同一页面

### 4.2 PRD 中的界面描述（如有）
{PRD 中对该功能的界面/交互描述原文}

## 5. 生成方案（待确认）

### 方案 A: 调整已有原型（如找到高匹配原型）
- **目标文件**: prototypes/xxx.html
- **当前内容**: {已有原型摘要}
- **需新增**: {缺失功能列表}
- **需修改**: {需调整的部分}

### 方案 B: 创建新原型
- **页面名称**: {建议名称}
- **页面定位**: {在产品信息架构中的位置}
- **布局结构**: {整体布局}
- **使用组件**（映射到设计规范）:
  | UI 元素 | 设计规范组件 | Token |
  |---------|-------------|-------|
  | 顶部导航 | global-nav + sub-nav-frosted | 44px + 52px |
  | 主操作区 | button-primary | pill, #0066cc |
  | ... | ... | ... |
- **需集成展示的历史功能**: {从 wiki 检索到的关联功能}
- **参考的历史 UI 模式**: {已有产品 UI 范式}

## 6. 请确认

请选择：
  **A.** 在现有原型 {文件名} 上调整——补充 {缺失功能}
  **B.** 创建新原型页面——按上述方案 B 生成
  **C.** 补充更多信息——我有额外的需求说明
```

**此 gate 绝对不可跳过。必须等待用户选择 A/B/C 后才进入下一步。**

#### 用户选择后的处理：

**选择 A（调整已有原型）**:
→ 进入模式 D（调整已有原型）流程
→ 在现有原型上增量修改
→ 更新 HTML 注释中的关联需求列表

**选择 B（创建新原型）**:
→ 进入模式 A 的 Step 2-6（组件映射 → 布局设计 → 代码生成 → 合规检查 → 输出）
→ **关键**: 生成时融入 Step 2 检索到的所有上下文：
  - 历史功能模块的 UI 模式（保持一致性）
  - 关联需求的界面元素（方便后续集成）
  - PRD 中的界面描述（确保与产品设计一致）
  - 竞品调研中的最佳实践

**选择 C（补充信息）**:
→ 用户在 Gate 处提供额外信息
→ Agent 更新生成方案后，回到 Step 3 再次展示 → 等待确认
→ 循环直到用户选择 A 或 B

### Step 4: 执行生成（新建或调整）

**根据 Step 3 用户选择进入对应流程。**

#### 如选 B（新建）— 增强版生成

相比模式 A 的直接描述生成，需求驱动模式在生成时必须额外做到：

1. **融入历史 UI 模式**: 如 wiki 检索发现产品已有类似功能使用特定的 UI 模式（如"表格+行内操作"），新原型应保持一致。
2. **为关联需求预留接口**: 如 PRD 中同一模块有 3 个关联需求，新原型应预留它们的入口（导航项、Tab、卡片槽位等）。
3. **引用调研结论**: 如竞品调研发现某种交互更优，优先采用。
4. **在 HTML 注释中记录所有参考来源**:
   ```html
   <!--
     关联需求: REQ-XXX, REQ-AAA, REQ-BBB（同模块）
     历史功能参考: {wiki-entity-1}, {wiki-entity-2}
     竞品参考: {competitor-name}
     PRD 来源: prd/{name}/v{N}/prd.md §{章节}
   -->
   ```

### Step 5: 输出 & 关联

1. **写入原型文件**: `prototypes/{name}.html`
2. **HTML 注释完整记录**: 设计规范、关联需求、历史参考、生成时间
3. **可选回链**: 如 wiki 可用，在需求实体中追加原型文件路径引用

---

## 模式 D：调整已有原型

### Step 1: 加载上下文

1. **读取已有 HTML 文件**
2. **从 HTML 注释中提取元数据**:
   ```html
   <!--
     PM-Skill UI Prototype
     设计规范: apple
     关联需求: REQ-XXX, REQ-YYY
     生成时间: 2024-06-05
     ...
   -->
   ```
3. **如元数据不可用**: 要求用户通过 `--design` 指定设计规范
4. **加载对应的设计规范文件**
5. **如调整来自 --req 模式**: 读取需求详情和关联 wiki 实体

### Step 2: 确认变更（BLOCKING Gate）

**在修改任何代码前，先展示变更方案并等待确认：**

```
# 原型调整方案

## 当前原型
- 文件: prototypes/dashboard.html
- 内容摘要: {当前包含的主要区域和功能}
- 设计规范: {规范名}
- 关联需求: {REQ-IDs}

## 请求的变更
- {变更项 1: 新增/修改/删除}
- {变更项 2: ...}

## 影响分析
- 新增组件: {列表，映射到规范 Token}
- 修改区域: {列表}
- 保持不变: {列表}

## 依赖/冲突检查
- ✅ 无冲突
- 或
- ⚠️ 注意: {潜在问题}

是否确认执行以上变更？[确认/修改方案/取消]
```

**必须等待用户确认后再进入代码修改。**

### Step 3: 应用变更

1. 在现有 HTML 结构上增量修改
2. 新增元素：严格使用设计 Token
3. 修改元素：保持已有 Token 一致，不混用不同规范
4. 删除元素：清理相关 CSS 规则
5. 更新元数据注释：添加调整记录

**变更标注**（在 HTML 注释中）:
```html
<!-- [ADJUSTED: 2024-06-05] 新增搜索栏 {component.search-input} — 关联 REQ-XXX -->
<div class="search-bar">
  ...
</div>
```

### Step 4: 设计合规再检查

对新修改的部分执行 Step 5 的合规检查。

### Step 5: 输出

- 默认原地更新
- 或写入 `prototypes/{name}-v{version}.html` 作为新版本
- 标注变更摘要

---

## 关键约束

### 硬约束（违反即为 Bug）

1. **所有颜色值必须来自规范 Token**。不得使用规范外的任何 hex 颜色。规范中 undefined 的颜色使用最近 Token 的合理变体，并在注释中标注。
2. **所有字体规格必须来自规范 typography Token**。不得使用规范外的字号/字重组合。
3. **所有圆角值必须来自规范 rounded Token**。规范定义了几个圆角层级就只能用这几个。
4. **阴影使用必须遵守规范的 Elevation 规则**。如果规范说"只有一个 shadow"，就只能有一个 shadow。
5. **禁止装饰性渐变**（除非规范明确定义）。
6. **禁止自创 animation/transition**（除非规范明确定义交互状态）。

### 软约束（尽量避免）

1. 尽量使用规范组件而非从头构建
2. 尽量保持布局比例与规范示例一致
3. 尽量使用规范定义的间距系统进行空间组织

### 流程约束

4. **需求驱动模式（--req）必须先检索 wiki、再展示研究报告、获得用户确认后才生成——绝不跳过研究步骤盲目生成**
5. **调整已有原型前必须先展示变更方案并等待确认——绝不直接修改文件**
6. **所有 BLOCKING gate 强制执行——不得在一轮对话中从检索直接跳到最后输出**

---

## 完整示例

### 示例 1：需求驱动生成

```
用户: /pm-ui --req REQ-008 --design apple
```

**执行过程**:

1. **加载需求**:
   - 读取 wiki/entities/REQ-008.md
   - 获取: "项目管理仪表盘——项目列表卡片视图、新建项目按钮、全局搜索"

2. **Wiki 检索**:
   - `/wiki-query "项目 管理 页面 界面 仪表盘"` → 找到 3 个相关实体
   - `/wiki-query "项目 列表 卡片 功能模块"` → 找到 2 个关联功能
   - 扫描 `prototypes/` → 未找到匹配原型

3. **BLOCKING Gate #1 — 展示研究报告**:
   ```
   # REQ-008 原型生成前研究
   ...
   ## 5. 生成方案
   推荐方案 B: 创建新原型 "项目管理仪表盘"
   - 布局: global-nav → sub-nav → 工具栏(搜索+新建) → 卡片网格 → footer
   - 使用组件: search-input, button-primary, store-utility-card
   - 需集成: 项目统计模块（来自 wiki 实体 "项目概览"）
   
   请确认: [A/B/C]
   ```

4. **用户选择 B** → 进入代码生成

5. **生成 HTML** → 融入历史功能信息 → 合规检查 → 输出 `prototypes/dashboard.html`

### 示例 2：需求驱动 → 发现已有原型 → 调整

```
用户: /pm-ui --req REQ-012 --design apple
```

**执行过程**:

1. **加载需求**: REQ-012 "项目搜索筛选功能"
2. **Wiki 检索**: 发现已有原型 `prototypes/dashboard.html`（关联 REQ-008）覆盖率 70%
3. **BLOCKING Gate #1**:
   ```
   推荐方案 A: 在已有原型 prototypes/dashboard.html 上调整
   - 当前内容: 项目卡片网格、新建按钮、全局导航
   - 需新增: 搜索栏 + 筛选面板
   - 需修改: 工具栏区域重新布局
   
   请确认: [A/B/C]
   ```
4. **用户选择 A** → 进入模式 D → **BLOCKING Gate #2**: 展示变更方案 → 确认 → 增量修改

---

## 与 PM 生命周期的集成

`/pm-ui` 与 PM 阶段协同工作：

| PM 阶段 | /pm-ui 用途 | 推荐模式 |
|---------|------------|---------|
| /pm-init 后 | 基于需求快速生成低保真原型验证方向 | 模式 A |
| /pm-plan 阶段 | 为 PRD 生成配套的 UI 原型辅助沟通 | 模式 A |
| /pm-execute 阶段 | 需求驱动生成原型，迭代调整 | **模式 B（--req）** |
| /pm-verify 阶段 | 用原型做可用性走查检查 must_haves | 模式 D |
| /pm-prd 后 | 为 PRD 中的关键页面生成原型 | 模式 A 或 B |

**典型使用模式**:
```
/pm-init "产品名"
  → /pm-plan 1
  → /pm-execute 1
  → /pm-req generate competitive-analysis ...    ← 提取需求
  → /pm-req research REQ-008                    ← 需求调研
  → /pm-ui --req REQ-008 --design apple          ← 需求驱动生成原型（先检索 wiki，确认后生成）
  → /pm-verify 1                                 ← 用原型辅助验证
```
