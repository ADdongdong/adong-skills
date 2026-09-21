# garden-skills — 本类分片

> **合集总览**：5 个 skill，跨 5 个分类 · 上游 <https://github.com/ConardLi/garden-skills> · MIT · 12.6k★
> **本目录收录 1 个**：生成式图像
> **其他分类**：[01-web-ui(1)](../01-web-ui/garden-skills.md) · [03-content-pipeline(1)](../03-content-pipeline/garden-skills.md) · [04-presentation(1)](../04-presentation/garden-skills.md) · [06-learning(1)](../06-learning/garden-skills.md)
> **上游路径根**：`skills/<name>/`（上游以 Claude 插件形式分发，另见 `.claude-plugin/`）
> **安装**：把上游 `skills/<name>/` 复制到 `~/.codebuddy/skills/<name>/`。
> 本机 `~/.codebuddy/skills/` 下这 5 个**均未安装**。

## B2 生成式图像

| Skill | 用途与触发场景 |
|---|---|
| `gpt-image-2` | 面向 **GPT Image 2** 的图像生成 / 编辑，含 18 大类、80+ 结构化模板（海报 / UI / 产品图 / 信息图 / 学术图 / 技术架构图 / 漫画 / 头像 / 流程板 / 电影分镜 / IP 周边 / 编辑工作流等）。三种工作模式：**(A) Garden 本地模式** —— 走 OpenAI 兼容接口直接出图并落盘；**(B) Host-Native 模式** —— 把本 skill 当提示词工程指引，把渲染好的 prompt 交给宿主 agent 自带的图像工具出图；**(C) Advisor 模式** —— 宿主没有任何图像工具时，退化为高质量 prompt 顾问。 |

## 与 02-visuals 内其他生成项的边界

同为"AI 出图"，选择依据是**后端与模板体系**：

| 想要 | 用 |
|---|---|
| 指定 GPT Image 2 + 结构化模板（含 Advisor 降级模式） | `gpt-image-2` |
| 多后端自由切换（Azure / Google / DashScope / GLM / MiniMax / 即梦 / Seedream / Replicate …）、按 prompt 文件批量出图 | [`baoyu-image-gen`](baoyu-skills.md) |
| 中文文章正文配图（特定"小黑/手绘"风格） | [`ian-xiaohei-illustrations`](ian-xiaohei-illustrations.md) |

## 同合集其他分类

| 分类 | Skill | 一句话 |
|---|---|---|
| [01-web-ui](../01-web-ui/garden-skills.md) | `web-design-engineer` | 构建/重设计浏览器渲染的视觉制品 |
| [03-content-pipeline](../03-content-pipeline/garden-skills.md) | `beautiful-article` | 素材转单文件 HTML 网页文章 |
| [04-presentation](../04-presentation/garden-skills.md) | `web-video-presentation` | 文章/口播稿转点击式 16:9 网页演示 |
| [06-learning](../06-learning/garden-skills.md) | `kb-retriever` | 本地知识库目录的分层检索与问答 |
