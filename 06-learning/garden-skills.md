# garden-skills — 本类分片

> **合集总览**：5 个 skill，跨 5 个分类 · 上游 <https://github.com/ConardLi/garden-skills> · MIT · 12.6k★
> **本目录收录 1 个**：知识检索
> **其他分类**：[01-web-ui(1)](../01-web-ui/garden-skills.md) · [02-visuals(1)](../02-visuals/garden-skills.md) · [03-content-pipeline(1)](../03-content-pipeline/garden-skills.md) · [04-presentation(1)](../04-presentation/garden-skills.md)
> **上游路径根**：`skills/<name>/`（上游以 Claude 插件形式分发，另见 `.claude-plugin/`）
> **安装**：把上游 `skills/<name>/` 复制到 `~/.codebuddy/skills/<name>/`。
> 本机 `~/.codebuddy/skills/` 下这 5 个**均未安装**。

## 知识检索

| Skill | 用途与触发场景 |
|---|---|
| `kb-retriever` | 面向**本地知识库目录**的检索与问答助手。核心流程：(1) 分层索引导航 → (2) **遇到 PDF / Excel 时必须先读 `references/` 学习处理方法** → (3) 处理完文件再检索。按文件类型组合使用 `grep`、`Read`、`pdfplumber`、`pandas` 做渐进式检索，避免整文件加载。触发：用户问题涉及"从知识库目录回答问题 / 检索信息 / 查资料"。 |

## 为什么它归 06-learning

它服务的场景是**从自己的资料里找答案**，与 06 的另一项 `vibe-hub-skill`（把别人的话翻译成准确术语）同属「理解与获得信息」，而不是 03-content-pipeline 那种「把内容搬去发布」。

## 同合集其他分类

| 分类 | Skill | 一句话 |
|---|---|---|
| [01-web-ui](../01-web-ui/garden-skills.md) | `web-design-engineer` | 构建/重设计浏览器渲染的视觉制品 |
| [02-visuals](../02-visuals/garden-skills.md) | `gpt-image-2` | 面向 GPT Image 2 的图像生成/编辑 |
| [03-content-pipeline](../03-content-pipeline/garden-skills.md) | `beautiful-article` | 素材转单文件 HTML 网页文章 |
| [04-presentation](../04-presentation/garden-skills.md) | `web-video-presentation` | 文章/口播稿转点击式 16:9 网页演示 |
