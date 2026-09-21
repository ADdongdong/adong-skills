# 第三方来源与许可

本仓库收录两类内容，权利归属不同：

| 类别 | 内容 | 本仓库如何处置 |
|---|---|---|
| **自建** | 6 个 skill 的完整文件本体（`awesome-design-md`、`mermaid-doc-renderer`、`xd-dev-handbook`、`hahadong-push-github`、`c-drive-cleanup`、`feynman-tutor-skill`） | 入库并适用根目录 `LICENSE`（MIT） |
| **收藏** | 44 个第三方 skill 的索引条目 | **只登记名称、用途、出处与安装方式，不复制其代码** |

> **唯一例外**：`01-web-ui/awesome-design-md/design-md/**` 内的 74 份 `DESIGN.md` 派生自
> [`VoltAgent/awesome-design-md`](https://github.com/VoltAgent/awesome-design-md)（MIT），
> 属**完整再分发**。该 skill 的 `SKILL.md`（索引与使用规则）为本仓库作者自写。

## 收藏项的上游仓库

下表为索引条目的来源。**本仓库不承载其代码**，安装请回到上游。

| 上游仓库 | 权利人 | 许可 | ★（2026-09-21） | 本仓库收录 |
|---|---|---|---|---|
| [`JimLiu/baoyu-skills`](https://github.com/JimLiu/baoyu-skills) | JimLiu | MIT | 26.0k | 21 个 skill |
| [`ibelick/ui-skills`](https://github.com/ibelick/ui-skills) | ibelick | MIT | 8.8k | 7 个 skill |
| [`plannotator/effective-html`](https://github.com/plannotator/effective-html) | plannotator | MIT | 3.2k | 6 个 skill |
| [`ConardLi/garden-skills`](https://github.com/ConardLi/garden-skills) | ConardLi | MIT | 12.6k | 5 个 skill |
| [`tt-a1i/archify`](https://github.com/tt-a1i/archify) | tt-a1i | MIT | 68.6k | 1 个 skill |
| [`helloianneo/ian-xiaohei-illustrations`](https://github.com/helloianneo/ian-xiaohei-illustrations) | helloianneo (Ian) | MIT | 11.9k | 1 个 skill |
| [`Cocoon-AI/architecture-diagram-generator`](https://github.com/Cocoon-AI/architecture-diagram-generator) | Cocoon AI | MIT | 7.3k | 1 个 skill |
| [`oil-oil/vibe-hub-skill`](https://github.com/oil-oil/vibe-hub-skill) | oil-oil | MIT | 191 | 1 个 skill |
| [`coleam00/excalidraw-diagram-skill`](https://github.com/coleam00/excalidraw-diagram-skill) | coleam00 | **未声明许可证** | 4.8k | 1 个 skill |

### ⚠️ 许可状态待确认的一项

`coleam00/excalidraw-diagram-skill` 仓库内**没有 LICENSE 文件**，上游也未声明许可证 —— 依默认著作权规则属「保留所有权利」。本仓库**只登记其用途与链接、不复制其任何内容**；若你要在自己的项目中复用它，请先向上游作者确认授权。

## 关于 `DESIGN.md` 的再分发

- 来源仓库：[`VoltAgent/awesome-design-md`](https://github.com/VoltAgent/awesome-design-md)（MIT，116.9k★）
- 该仓库是 **73+ 品牌 `DESIGN.md` 的合集**（本身不是 skill 包）。`01-web-ui/awesome-design-md/SKILL.md` 由本仓库作者编写，用于把该合集作为 skill 使用；`design-md/<brand>/DESIGN.md` 为上游戏内容原样复制（74 个品牌目录，未含上游的品牌级 `README.md` 存根）。
- 上游已声明：这些文件是对公开站点 CSS 的**「inspired interpretation」**（其 frontmatter 标 `version: alpha`），**非官方品牌规范**，上游不主张对任何站点视觉识别的所有权。

## 自建 skill 的既有发布渠道

`hahadong-push-github`、`c-drive-cleanup`、`feynman-tutor-skill`、`mermaid-doc-renderer` 等同时发布在作者自己的 GitHub 账号下，并按 skillhub 约定的 frontmatter 字段提供。本仓库中的副本**保持文件原样（未改写任何 `SKILL.md`）**，唯一例外见下方。

### 本仓库对自建内容做过的改动（仅 1 处）

| 文件 | 改动 | 原因 |
|---|---|---|
| `05-dev-tooling/hahadong-push-github/scripts/push_to_github.sh` | 把兜底 python 解释器的硬编码绝对路径（`C:/Users/<用户名>/...`）改为基于 `$USERPROFILE` / `$HOME` 的环境变量探测；找不到时给出明确报错并退出 | 去除个人信息，同时保持原意与可用性 |

另：`05-dev-tooling/c-drive-cleanup/` 已剔除 `_skillhub_meta.json`（含本机绝对路径与 skillhub namespace），`_meta.json` 只保留 `slug` / `version` / `publishedAt`。

### 已知注意事项（**未**改动上游内容，仅提示）

这两个脚本是为 **WorkBuddy** 环境写的，默认目录指向 `~/.workbuddy/`：

| 文件 | 表现 | 在 CodeBuddy 下怎么办 |
|---|---|---|
| `06-learning/feynman-tutor-skill/install.ps1` | 安装目标写死为 `$env:USERPROFILE\.workbuddy\skills` | 改用 `~/.codebuddy/skills/`，或手动复制目录 |
| `05-dev-tooling/hahadong-push-github/scripts/push_to_github.sh` | 找不到 `python3` / `python` 时，兜底去 `~/.workbuddy/binaries/python/...` 找解释器 | 把 python 加进 `PATH`，或按报错提示设置 |

`s/vibehub` 等其他 skill 不涉及该问题。

## 商标

各 skill 名称、上游仓库名与其中提及的产品名归各自权利人所有，此处仅作指称之用。
