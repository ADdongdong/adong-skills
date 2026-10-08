---
name: pm-help
description: "显示 pm-skill 所有命令参考和用法指南"
argument-hint: "[command]"
---

# /pm-help — 命令帮助

显示 pm-skill 的所有可用命令和用法指南。

## 工作流

1. 如果用户提供了 `[command]` 参数（如 `/pm-help init`），显示该命令的详细帮助：
   - 读取对应的 `commands/pm/{command}.md` 文件
   - 展示命令的完整工作流、产出物和关键规则

2. 如果无参数，显示完整命令列表（从 SKILL.md 的命令清单中提取）：

```
## pm-skill 命令参考

### 核心生命周期
/pm-init [project-name]      初始化新 PM 项目
/pm-plan <N>                 规划阶段 N
/pm-execute <N>              执行阶段 N
/pm-verify <N>               验证阶段 N 完成度
/pm-transition               完成当前阶段，切换到下一阶段
/pm-next                     自动检测并执行下一步

### PM 领域工具
/pm-research <topic>         市场/用户/竞品研究
/pm-prd <description>        多轮 PRD 生成
/pm-strategy <product>       策略画布工作坊
/pm-release <version>        发布 & GTM 规划
/pm-ui <desc> --design <S>   UI 原型生成（需指定设计规范）
/pm-quick <task>             轻量临时任务

### 工具命令
/pm-health [--repair]        项目健康检查
/pm-config [key=value]       配置管理
/pm-todo [add/list/done]     TODO 管理
/pm-wiki <op> [args]         wiki 知识库操作（需 llm-wiki-skill）
/pm-help [command]           显示此帮助

### 快速开始
/pm-init "你的产品名称"      ← 从这里开始
```

## 关键规则

- 中文输出
- 如有 `[command]` 参数，先读取对应 command 文件再展示
- 帮助信息从 SKILL.md 命令清单中提取，保持一致性
