---
name: pm-wiki
description: "桥接到 llm-wiki-skill。检测安装状态，委托 wiki 操作（编译、查询、检查等）。"
argument-hint: "<op> [args]"
---

# /pm-wiki — Wiki 桥接

触发 `pm-skill`，检测并委托操作给 llm-wiki-skill。

## 工作流

### 步骤 1: 检测安装

```bash
# 检测 llm-wiki-skill 是否可用
ls .wiki/ 2>/dev/null || which wiki 2>/dev/null
```

**如未安装**:
```
⚠️ 未检测到 llm-wiki-skill。

此功能需要 llm-wiki-skill（专业级 wiki 知识库引擎）。

📦 安装:
   git clone https://github.com/lgwanai/pm-skill ~/.claude/skills/llm-wiki-skill
   cd ~/.claude/skills/llm-wiki-skill && pip install -e .

安装后重启 Claude Code 即可。详见 https://github.com/lgwanai/pm-skill
```

**如已安装** → 步骤 2

### 步骤 2: 路由操作

| 操作 | 委托到 | 说明 |
|------|--------|------|
| `/pm-wiki compile <path>` | `/wiki-compile <path>` | 摄入文档到 wiki |
| `/pm-wiki query <q>` | `/wiki-query <q>` | 搜索 wiki 知识库 |
| `/pm-wiki status` | `/wiki-status` | wiki 统计信息 |
| `/pm-wiki lint` | `/wiki-lint` | 健康检查 |
| `/pm-wiki init` | `/wiki-init` | 初始化 wiki 目录 |
| `/pm-wiki consolidate` | `/wiki-consolidate` | 知识固化 |

### 步骤 3: 执行 & 汇报

调用对应的 llm-wiki-skill 命令，将结果返回给用户。

## 详细参考

`references/wiki-integration.md` — 完整的集成指南和最佳实践。

## 关键规则

- 先检测再操作
- 未安装时提供清晰的安装指引
- 中文输出
