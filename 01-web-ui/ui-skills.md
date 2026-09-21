# ui-skills — 界面质量修复

> **上游**：<https://github.com/ibelick/ui-skills> · MIT · 8.8k★
> **本类收录 7 个**：全部属于本分类，不跨分类 —— 本文件即该合集的完整索引。
> **上游路径根**：`skills/<name>/`
> **安装**：上游提供 `ui-skills` CLI（只有 `list` / `get` / `start` / `categories` 四个命令，**没有 install**）—— 用 `get <slug>` 取正文后组装成 `SKILL.md`；或直接把上游 `skills/<name>/` 目录复制到 `~/.codebuddy/skills/<name>/`。
> 本机 `~/.codebuddy/skills/` 下这 7 个**都已安装**。

## A1 设计语言与规范

| Skill | 用途与触发场景 |
|---|---|
| `create-design-md` | 从既有产品仓库或公开站点产出一份 `DESIGN.md`（设计语言、视觉体系、设计令牌与规范），给编码 agent 一份长期可用的界面上下文。触发：要记录/重建某个产品的设计体系、抽取设计令牌。**不改产品源码**，也不把偶然的实现写法提升为设计决策。 |
| `ui-skills-root` | UI 相关工作开始前，通过 ui-skills CLI 选出**最小够用**的 UI skill 上下文。触发：任何界面任务动工前的选型。 |

## A2 界面质量修复

| Skill | 用途与触发场景 |
|---|---|
| `baseline-ui` | 快速清理 UI 代码的间距、层级、排版与小布局问题。触发：界面需要一次快速的打磨/清理。 |
| `improve-ui` | 对现有界面按**它自己的设计证据**做审计，找出可验证的 UI 问题，并写出可交给另一个 agent 实施的自治计划。触发：评审 / 改进 / 清理界面但不替换其身份、排查设计系统漂移、准备设计交接。**对产品源码严格只读**。 |
| `fixing-accessibility` | 审计并修复 HTML 无障碍问题：ARIA 标注、键盘导航、焦点管理、颜色对比度、表单报错。触发：新增交互控件 / 表单 / 弹窗，或评审 WCAG 合规。 |
| `fixing-metadata` | 审计并修复 HTML 元数据：页面标题、meta description、canonical、Open Graph、Twitter card、favicon、JSON-LD 结构化数据、robots 指令。触发：做 SEO、修社交分享预览、新页面要正确的 meta。 |
| `fixing-motion-performance` | 审计并修复动画性能问题：布局抖动、合成属性、滚动联动动效、模糊效果。触发：动画卡顿、过渡掉帧，或评审 CSS/JS 动画性能。 |

## 上游用法要点

- `ui-skills-root` 是这套合集的**入口**：先选最小上下文，再进具体 skill。
- `improve-ui` 与 `baseline-ui` 容易混：前者**只出审计与计划、不改代码**；后者**直接动手改**。
