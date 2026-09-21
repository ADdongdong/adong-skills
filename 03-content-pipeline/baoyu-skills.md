# baoyu-skills — 本类分片

> **合集总览**：21 个 skill，跨 3 个分类 · 上游 <https://github.com/JimLiu/baoyu-skills> · MIT · 26.0k★
> **本目录收录 12 个**：内容抓取、排版转换、翻译、发布与摘要
> **其他分类**：[02-visuals(8)](../02-visuals/baoyu-skills.md) · [04-presentation(1)](../04-presentation/baoyu-skills.md)
> **上游路径根**：`skills/<name>/`（上游以 Claude 插件形式分发，另见 `.claude-plugin/`）
> **安装**：把上游 `skills/<name>/` 复制到 `~/.codebuddy/skills/<name>/`。
> 本机 `~/.codebuddy/skills/` 下这 21 个**均未安装**。
> ⚠️ 带 `danger-` 前缀的两个走**逆向工程 API**，上游明确要求先取得用户同意再用。

这一组的共同形态是「**把内容从一个地方搬到另一个地方**」：抓进来 → 整形 → 发出去。按数据流向分成三小段排列。

## 1) 抓取：把外部内容变成 markdown / 素材

| Skill | 用途与触发场景 |
|---|---|
| `baoyu-url-to-markdown` | 抓任意 URL 并转成 markdown，走 baoyu-fetch CLI（Chrome CDP + 站点适配器）。内置适配器覆盖 **X/Twitter、YouTube 字幕、Hacker News 帖子**，通用页面走 Defuddle；遇到登录 / 验证码有交互等待模式。触发：想把某个网页存成 markdown。 |
| `baoyu-youtube-transcript` | 按 URL 或视频 ID 下载 **YouTube 字幕 / 转录**与**封面图**，支持多语言、翻译、章节、说话人识别，并缓存原始数据以便快速重新排版。触发：取 YouTube 字幕、下载字幕、YouTube 封面 / 视频封面。 |
| `baoyu-danger-x-to-markdown` | 把 **X（Twitter）推文与文章**转成带 YAML front matter 的 markdown，走逆向 API。触发：提到"X 转 markdown""保存推文"，或直接给出 x.com / twitter.com 链接要求转换。 |
| `baoyu-danger-gemini-web` | 走逆向的 **Gemini Web API** 出图与出文，支持参考图视觉输入与多轮对话。触发：其他 skill 需要图像生成后端时；或用户要求"用 Gemini 生成图片 / 文本"、需要具备视觉能力的生成。 |
| `baoyu-electron-extract` | 从任意已安装的 Electron 应用（`.asar` 包）提取资源与 JavaScript —— 有 `.js.map` 时还原原始源码，否则用 Prettier 格式化压缩代码。跳过 `node_modules`，支持 macOS 与 Windows。触发：提取 Electron 应用、反编译 Electron、看某个桌面应用源码、检查 `app.asar`。 |

## 2) 整形：排版与格式转换

| Skill | 用途与触发场景 |
|---|---|
| `baoyu-format-markdown` | 给纯文本或 markdown 补齐 frontmatter、标题、摘要、分级标题、加粗、列表与代码块。输出到 `{filename}-formatted.md`。触发：排版 markdown、美化文章、补格式、改文章版面。 |
| `baoyu-markdown-to-html` | markdown 转**带样式的 HTML**（微信兼容主题），支持代码高亮、数学公式、**Mermaid（经 headless Chrome 渲染成 PNG）**、PlantUML、脚注、提示块、信息图，并可把外链自动转为文末引用。触发：md 转 html、要带样式的 HTML 输出、微信外链转底部引用。 |
| `baoyu-translate` | 翻译，三种模式（快翻 / 常规 / 精翻），支持自定义术语表。触发：翻译、精翻、改成中文 / 英文、本地化、校对译文，或提供一个 URL / 文件并带翻译意图。 |

## 3) 分发：发到平台 / 做成摘要

| Skill | 用途与触发场景 |
|---|---|
| `baoyu-post-to-wechat` | 发布到**微信公众号**（API 或 Chrome CDP）：支持文章（HTML / markdown / 纯文本输入）与**贴图**（多图）。markdown 文章默认把普通外链转成文末引用，以适配公众号。触发：发布公众号、微信贴图 / 图文 / 文章。 |
| `baoyu-post-to-weibo` | 发布到**微博**：支持带文字 / 图片 / 视频的普通微博，以及用 markdown 输入的**头条文章**（走 Chrome CDP）。触发：发微博、发布微博、写微博、微博头条文章。 |
| `baoyu-post-to-x` | 发布到 **X（Twitter）**：支持带图 / 视频的普通推文与 **X Articles 长文**（markdown）。在 Codex 中若用户明确要求 Chrome 插件 / @chrome 就用扩展工作流，否则优先用 Chrome Computer Use，只有被允许时才回退到真实 Chrome CDP 脚本。触发：post to X、tweet、发推、分享到 X。 |
| `baoyu-wechat-summary` | 用本地 `wx-cli`（<https://github.com/jackwener/wx-cli>）把**微信群聊精华**总结成结构化摘要，默认出常规版、"毒舌版"需显式开启。跨次运行维护：每群历史（`history.json` + `history-digests.jsonl`）、每用户画像、每群事实记忆（`memory.md`），内置隐私护栏。触发：总结群聊、群聊精华、群聊摘要。 |

## 与 04-presentation 分片的边界

`baoyu-slide-deck`（"做幻灯片"）与本文件的 `baoyu-markdown-to-html`（"md 转 html"）都以内容为输入，区别在**交付形态**：前者出的是**幻灯片图片**、归 04-presentation；后者出的是**可直接粘贴的 HTML**、归本分类。
