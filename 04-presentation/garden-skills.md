# garden-skills — 本类分片

> **合集总览**：5 个 skill，跨 5 个分类 · 上游 <https://github.com/ConardLi/garden-skills> · MIT · 12.6k★
> **本目录收录 1 个**：网页视频演示
> **其他分类**：[01-web-ui(1)](../01-web-ui/garden-skills.md) · [02-visuals(1)](../02-visuals/garden-skills.md) · [03-content-pipeline(1)](../03-content-pipeline/garden-skills.md) · [06-learning(1)](../06-learning/garden-skills.md)
> **上游路径根**：`skills/<name>/`（上游以 Claude 插件形式分发，另见 `.claude-plugin/`）
> **安装**：把上游 `skills/<name>/` 复制到 `~/.codebuddy/skills/<name>/`。
> 本机 `~/.codebuddy/skills/` 下这 5 个**均未安装**。

## 网页视频演示

| Skill | 用途与触发场景 |
|---|---|
| `web-video-presentation` | 把一篇文章或口播稿做成**"看起来像视频"的点击驱动 16:9 网页演示**，可选合成口播音频。流程：原始文章 → **一次产出**口播稿 + outline 开发计划 → 用户**一次对齐** 5 件事（稿子 / outline / 主题 / 素材 / 开发模式）→ 网页开发（逐章 / 顺序 / 并行）→ 可选音频合成（与供应商无关：内置 MiniMax `mmx-cli` 与 OpenAI TTS，可换 ElevenLabs / edge-tts / Azure / 自带 TTS）。**outline 只规划节奏与信息密度，不规划动画** —— 动画在章节开发时按 PRINCIPLES + ANTI-AI 法则即时设计。每次点击推进口播稿的一个节拍，每一步独占整屏，进度条平时隐藏、悬浮才出现。触发：用网页做视频（动态 PPT 但不像 PPT）、把口播稿 / 文章变成可交互解说、为 B站 / YouTube / 视频号录屏教程、做有电影感的产品或 talk demo。 |

## 与 04-presentation 内另一项的边界

| 想要 | 用 |
|---|---|
| **点击推进的网页演示**，可叠音频、可录屏 | `web-video-presentation`（本项） |
| **图片形式的幻灯片**，先把风格大纲敲定再逐页出图 | [`baoyu-slide-deck`](baoyu-skills.md) |

## 同合集其他分类

| 分类 | Skill | 一句话 |
|---|---|---|
| [01-web-ui](../01-web-ui/garden-skills.md) | `web-design-engineer` | 构建/重设计浏览器渲染的视觉制品 |
| [02-visuals](../02-visuals/garden-skills.md) | `gpt-image-2` | 面向 GPT Image 2 的图像生成/编辑 |
| [03-content-pipeline](../03-content-pipeline/garden-skills.md) | `beautiful-article` | 素材转单文件 HTML 网页文章 |
| [06-learning](../06-learning/garden-skills.md) | `kb-retriever` | 本地知识库目录的分层检索与问答 |
