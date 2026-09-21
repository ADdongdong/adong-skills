# garden-skills — 本类分片

> **合集总览**：5 个 skill，跨 5 个分类 · 上游 <https://github.com/ConardLi/garden-skills> · MIT · 12.6k★
> **本目录收录 1 个**：内容编辑与产出
> **其他分类**：[01-web-ui(1)](../01-web-ui/garden-skills.md) · [02-visuals(1)](../02-visuals/garden-skills.md) · [04-presentation(1)](../04-presentation/garden-skills.md) · [06-learning(1)](../06-learning/garden-skills.md)
> **上游路径根**：`skills/<name>/`（上游以 Claude 插件形式分发，另见 `.claude-plugin/`）
> **安装**：把上游 `skills/<name>/` 复制到 `~/.codebuddy/skills/<name>/`。
> 本机 `~/.codebuddy/skills/` 下这 5 个**均未安装**。

## 内容编辑与产出

| Skill | 用途与触发场景 |
|---|---|
| `beautiful-article` | 把用户给的素材（网页 URL / PDF / DOCX / Markdown / 纯文本 / 截图 / 粘贴材料）编辑设计成一篇**可离线打开与分享的单文件 HTML 网页文章**。基于 reacticle 组件协议 —— 不手写裸 HTML/CSS，而用语义组件 + 受主题约束的自由层；按 `source → 规划 → 双确认 → 生成 → 终审 → 修复` 的小型 harness 流程推进，**默认 100% 信息保留的长文**。触发：把 URL/PDF/DOCX/文章做成网页文章、长文、briefing、解释文、视觉文章、教程、审阅复盘、方案分析。**只生成文章**，不生成后台、表单、dashboard、产品原型或通用 Web App。 |

## 与 03-content-pipeline 内其他项的边界

本分类主体是 baoyu 的「搬运流水线」（抓取 → 整形 → 分发）。`beautiful-article` 是其中**唯一做"深度再创作"**的一项：

| 你想要 | 用 |
|---|---|
| 把一份外部材料**改写排版成一篇成品文章** | `beautiful-article`（本项） |
| 把已有 markdown **补格式**或**转成带样式的 HTML** | [`baoyu-format-markdown`](baoyu-skills.md)、[`baoyu-markdown-to-html`](baoyu-skills.md) |
| 把网页 / 视频 / 帖子**抓成 markdown 素材** | [`baoyu-url-to-markdown`](baoyu-skills.md)、[`baoyu-youtube-transcript`](baoyu-skills.md) |
| 把成品**发到平台** | [`baoyu-post-to-wechat`](baoyu-skills.md)、[`baoyu-post-to-weibo`](baoyu-skills.md)、[`baoyu-post-to-x`](baoyu-skills.md) |

## 同合集其他分类

| 分类 | Skill | 一句话 |
|---|---|---|
| [01-web-ui](../01-web-ui/garden-skills.md) | `web-design-engineer` | 构建/重设计浏览器渲染的视觉制品 |
| [02-visuals](../02-visuals/garden-skills.md) | `gpt-image-2` | 面向 GPT Image 2 的图像生成/编辑 |
| [04-presentation](../04-presentation/garden-skills.md) | `web-video-presentation` | 文章/口播稿转点击式 16:9 网页演示 |
| [06-learning](../06-learning/garden-skills.md) | `kb-retriever` | 本地知识库目录的分层检索与问答 |
