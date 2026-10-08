# PM 框架图谱

> 产品经理常用框架和方法论的综合参考。
> 内容综合自 pm-skills 的 8 个插件，在 Agent 执行 PM 工作流时按需引用。

---

## 产品发现框架

### 机会解决方案树（Teresa Torres）
4 层结构：期望结果 → 机会 → 解决方案 → 实验
- 从结果回推，而非从功能出发
- 每层 3-5 个节点

### 假设类型（8 种风险）
- 价值（用户会用它吗？）、可用性（用户能用吗？）
- 可行性（我们能做吗？）、生存能力（能持续吗？）
- 道德（应该做吗？）、GTM（能到达用户吗？）
- 战略对齐（符合公司方向吗？）、团队（有合适的人吗？）

### 优先级排序
- **Opportunity Score**: Importance × (1 - Satisfaction)
- **ICE**: Impact × Confidence × Ease
- **RICE**: Reach × Impact × Confidence / Effort
- **Kano Model**: Basic / Performance / Excitement 需求

### 实验设计
- A/B 测试、假门测试、原型测试、落地页测试
- 预购测试（测试付费意愿，不只是兴趣）
- XYZ+S 假设：X% of Y will Z if we S

---

## 产品策略框架

### 策略画布（9 区块）
1. 愿景、2. 细分市场、3. 痛点 & 价值、4. 价值主张（JTBD）
5. 战略权衡、6. 关键指标、7. 增长引擎、8. 核心能力、9. 防御

### 商业模式画布（Strategyzer）
9 模块：客户细分、价值主张、渠道、客户关系、收入流、
核心资源、关键活动、关键伙伴、成本结构

### 精益画布（Ash Maurya）
问题、解决方案、独特价值主张、不公平优势、客户细分、
关键指标、渠道、成本结构、收入流

### 竞争分析
- **Porter's Five Forces**: 竞争对手、供应商、买方、替代品、新进入者
- **SWOT**: 优势、劣势、机会、威胁
- **PESTLE**: 政治、经济、社会、技术、法律、环境

### 定价策略
- 基于价值、基于竞争、基于成本
- 价格弹性分析
- 支付意愿测试

---

## 执行框架

### PRD 写作
- 8 章节通用模板
- ToB/ToC 专用模板
- 版本管理（Major.Minor）

### OKR（Objectives & Key Results）
- Objective: 激励人心、可实现的 3 个月目标
- Key Results: 3-5 个可衡量的结果
- 与公司 OKR 对齐

### 用户故事
- 3C: Card（卡片）、Conversation（对话）、Confirmation（确认）
- INVEST: Independent, Negotiable, Valuable, Estimable, Small, Testable
- JTBD 工作故事: "当 [情境]，我想要 [动机]，以便 [结果]"

### 优先级排序框架
| 框架 | 公式 | 适用场景 |
|------|------|----------|
| Opportunity Score | Importance × (1 - Satisfaction) | 用户问题排序 |
| ICE | Impact × Confidence × Ease | 快速排序 |
| RICE | Reach × Impact × Confidence / Effort | 大规模排序 |
| Kano | Basic/Performance/Excitement | 功能分类 |
| MoSCoW | Must/Should/Could/Won't | 迭代规划 |

---

## 研究方法

### 用户画像
- JTBD、痛点、期望收益
- 人口统计 + 行为特征

### 市场细分
- 3-5 个细分市场
- 人口统计、JTBD、产品契合度

### 市场规模
- TAM / SAM / SOM
- 自上而下 + 自下而上

### 用户访谈（《妈妈测试》原则）
- 问他们的人生，不问你的创意
- 问过去的具体行为，不问未来的假设
- 不多说（推销），多听
- 寻找承诺信号（不是夸奖）

---

## GTM & 增长框架

### 增长飞轮（5 种类型）
1. 病毒式：用户邀请用户
2. 使用型：使用越多价值越大
3. 协作型：团队内价值随人数增长
4. UGC 型：用户内容吸引新用户
5. 推荐型：现有用户推荐新用户

### GTM 动作（7 种）
入站营销、出站销售、付费数字、社群、合作伙伴、ABM、PLG

### 沙滩头细分（4 标准）
紧迫痛点、付费意愿、可赢取份额、推荐潜力

### 北极星指标（7 验证标准）
反映核心价值、可衡量长期成功、敏感于产品决策、
团队可影响、可测量追踪、不为零和、滞后指标

---

## 置信度评分模型（保留自 pm-skill v2）

```
Confidence = (source_count / (source_count + 2)) × recency_weight

source_count: 多少个文档/来源提到这个信息
recency_weight: 1.0 (≤30天) → 0.7 (30-90天) → 0.4 (>90天)
```

- **HIGH** (≥0.7): 多个最近来源确认
- **MEDIUM** (0.4-0.7): 单一来源或较旧来源
- **LOW** (<0.4): 推断或过期来源

每次确认重置 recency clock。矛盾时保留双方说法，标记 SUPERSEDED 链。

---

## 更新指南

- 按需引用，不强制加载全部
- 新增框架 → 追加到对应分类
- 中文输出（保留英文术语）
