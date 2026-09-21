# vibe-hub-skill

> **上游**：<https://github.com/oil-oil/vibe-hub-skill> · MIT · 191★ · 术语库站点 <https://vibe-hub.org>
> **本类收录 1 个**：表达与沟通。
> **上游路径根**：`skills/vibehub/`（skill 名是 `vibehub`，**与仓库名不同**）
> **安装**：`npx skills add oil-oil/vibe-hub-skill`（上游 README 给出的方式）；或把上游 `skills/vibehub/` 复制到 `~/.codebuddy/skills/vibehub/`。
> **本机已安装**：`~/.codebuddy/skills/vibehub/`（含 `SKILL.md`、`vibehub.config.json`、`agents/openai.yaml`、`scripts/vibehub.mjs`）。运行需 **Node ≥ 20** 与联网。

## 表达与沟通

| Skill | 用途与触发场景 |
|---|---|
| `vibehub` | 在任何 Vibe Coding 编程任务**及其后续补充**中持续识别准确术语：即使用户已经让 agent 完成了一部分代码、正在追加修改，或只用口语描述效果、交互、状态和问题（如"鼠标放上去有个小提示""点完变一下颜色""内容太长省略"），也照样继续完成当前任务，并在进度或结果中**自然**告知对应的 UI / 网页 / 软件 / Git / AI Agent / 设计术语、通俗解释与 VibeHub 内链。用户要求"说专业一点"、改写需求、询问"这叫什么"，或看不懂 agent 回复时同样使用。**表达已经准确且没有值得补充的术语时，不要硬加教学。** |

## 它实际做的两件事

1. **把模糊描述改成可直接交给 agent 的准确需求** —— 保留原意、语气与约束，不擅自增加框架、组件库、参数或实现方案。
2. **主动指出用户刚描述但没说出口的技术概念** —— 每轮最多 1~3 个真正影响沟通的术语，不开课、不凑数量。

## 运行方式（本机已验证）

```
node "<skill_dir>/scripts/vibehub.mjs" resolve --query "<术语>" --compact
```

- 先按上下文推断 1~3 个稳定术语，再**一次批量查询**验证名称与链接；高置信度时只传一个候选。
- **只使用解析器返回的 `url`**，不自行拼接或伪造链接。
- 只发送脱敏后的短术语，不传源代码、密钥、客户信息、内部网址、邮箱或本地路径。
