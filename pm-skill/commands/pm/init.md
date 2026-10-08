---
name: pm-init
description: "初始化新的 PM 项目。完整初始化流程：引导提问→需求提取→路线图创建→.planning/ 目录结构。"
argument-hint: "[project-name]"
---

# /pm-init — 新建 PM 项目

触发 `pm-skill`，执行项目初始化工作流。

## 工作流

1. **欢迎 & 检测** — 检查是否已存在 `.planning/` 目录
   - 如存在：询问是重新初始化、合并还是取消
   - 如不存在：进入提问环节

2. **引导式提问（BLOCKING）** — 参考 `references/questioning.md`：
   - 第一轮：开放式提问 "告诉我你想做什么产品？"
   - 循环（Ask → Wait → Ask）：每次 ≤ 4 个问题，追问直到理解清晰
   - 挑战模糊表述，明确边界
   - 总结需求范围 → STOP → 等待用户确认

3. **需求提取** — 将确认的需求分类：
   - V1（必须做）：核心差异化功能
   - V2（后续做）：增强和完善
   - 不做（Out of Scope）：明确排除

4. **路线图创建** — 按照标准 PM 阶段分解：
   - 阶段 1：产品发现 & 市场研究
   - 阶段 2：产品策略 & 定位
   - 阶段 3：PRD & 需求定义
   - 阶段 4：执行规划
   - 阶段 5：发布 & GTM
   - （根据项目规模和 granularity 设置调整阶段数）
   - 每个阶段包含：目标、依赖、成功标准

5. **初始化（BLOCKING）** — 展示完整路线图 → STOP → 等待用户说"继续"
   - 创建 `.planning/` 目录结构
   - 生成 PROJECT.md, REQUIREMENTS.md, ROADMAP.md, STATE.md, config.json

## 产出物

- `.planning/PROJECT.md` — 产品项目简介（愿景、核心价值、约束、关键决策）
- `.planning/REQUIREMENTS.md` — 产品需求（含 V1/V2/Out of Scope 分类）
- `.planning/ROADMAP.md` — 产品路线图（阶段分解 + 成功标准）
- `.planning/STATE.md` — 项目状态记忆（< 100 行）
- `.planning/config.json` — PM 工作流配置

## 关键规则

- **STOP and WAIT** for user confirmation before creating any files
- 使用 `references/questioning.md` 的提问策略
- 遵循 `templates/PROJECT.md` 和 `templates/ROADMAP.md` 模板结构
- 检查 `.planning/` 是否已存在 — 如存在，提供选项
- 中文输出
