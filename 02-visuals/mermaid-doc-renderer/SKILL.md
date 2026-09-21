---
name: mermaid-doc-renderer
description: >
  Mermaid 图渲染 + Markdown 转 Word 文档的一体化工具。
  用 headless Chromium + 本地 mermaid.min.js（完全离线）把 Mermaid 声明式代码渲染为
  高清 PNG / 矢量 SVG / WebP / PDF / JPG，再把含 Mermaid 代码块的 Markdown 文档
  转成无 Markdown 语法的 Word（.docx，图用 PNG 嵌入）。
  当用户需要"把 md 里的 mermaid 图导出成图片"、"md 生成 Word/需求文档"、
  "mermaid 转 png/svg"、"文档里的图要清晰、不要 markdown 痕迹"时触发。
agent_created: true
version: 1.2.0
display_name: "Mermaid图表转图片和Word"
display_name_en: "Mermaid Render & Doc Generator"
description_zh: "图表成文：把 Mermaid 图渲染成高清 PNG/SVG/PDF，并把含图的 Markdown 一键转成排版干净的 Word 文档。完全离线，跨机器可移植。"
description_en: "Render Mermaid diagrams to PNG/SVG/WebP/PDF and convert Markdown with Mermaid blocks to clean Word (.docx) documents, fully offline and portable."
visibility: "public"
---

# Mermaid图表转图片和Word（mermaid-doc-renderer）

把「Mermaid 代码 → 高清图片/矢量」和「Markdown（含 Mermaid 图）→ 干净的 Word 文档」
串成一条可复用的离线流水线。所有渲染完全离线（本地 mermaid.min.js + headless Chromium），
不依赖任何在线图床。

**设计原则：零硬编码路径** —— 脚本自动探测本机环境（Playwright 浏览器缓存、系统 Chrome/Edge），
在任何机器上开箱即用；探测失败时给出明确的可操作提示（如何安装/如何手动指定）。

## 适用场景

- 用户提供一份 Markdown，希望把里面的 ```mermaid 代码块导出成图片（PNG/SVG/WebP/PDF/JPG）
- 用户提供 Markdown，希望生成 Word 文档（.docx），且「不要出现 markdown 语法、图要 PNG 格式」
- 用户在写需求规格说明书、设计文档、技术方案时，文档里的架构图/流程图需要高质量渲染

## 前置依赖

- **Python 3**，需安装 `Pillow`、`python-docx`：
  `pip install Pillow python-docx`
- **headless Chromium / Chrome / Edge**（任一即可，脚本按以下顺序自动探测）
  1. Playwright 缓存目录中的 `chromium_headless_shell-*` / `chromium-*`
     （Windows 在 `%LOCALAPPDATA%\ms-playwright`，macOS/Linux 在 `~/.cache/ms-playwright`）
  2. 系统 Chrome 或 Edge（Windows Program Files / macOS /Applications / Linux PATH）
  - 推荐用 Playwright 版 headless shell：`pip install playwright && playwright install chromium`
  - ⚠️ 如系统 Chrome 正在运行且不支持独立 headless 实例，优先用 Playwright 的 headless_shell.exe
- **mermaid.min.js v10+**（本 skill 自带 `assets/mermaid.min.js`，离线加载，无需下载）

所有路径均可用环境变量（`MERMAID_JS`、`HEADLESS_SHELL`）或命令行参数（`--mermaid-js`、`--shell`）
覆盖，没有任何写死的用户目录。

## 工作流程

### 一、渲染 Mermaid → 图片/矢量（`scripts/render_mermaid.py`）

```bash
# 提取 md 中所有 mermaid 块 → PNG（2x 高清，自动裁剪白边）
python scripts/render_mermaid.py <md路径> --out <输出目录> --format png --scale 2

# → 矢量 SVG（保留原始矢量，适合嵌入网页/后续编辑）
python scripts/render_mermaid.py <md路径> --out <输出目录> --format svg

# → 指定目标像素宽度（--scale 失效）
python scripts/render_mermaid.py <md路径> --out <输出目录> --format png --width 1200

# 单条 mermaid 字符串（不读 md）
python scripts/render_mermaid.py --code "graph LR; A-->B" --out <输出目录> --format png

# 复杂大图渲染超时时增大等待
python scripts/render_mermaid.py <md> --out <dir> --virtual-time-budget 20000
```

关键行为：
- 输出命名：`mermaid_0.png`、`mermaid_1.png`…（按 md 中出现顺序，从 0 开始）
- `--scale` 默认 2（2 倍分辨率）；`--width` 指定像素宽时 scale 失效
- `--format` 可选 `png` / `svg` / `webp` / `pdf` / `jpg`
- PNG/WebP/JPG 默认自动裁剪四周纯白边（`--no-trim` 关闭），裁剪用 PIL ImageChops，毫秒级完成
- 临时 HTML 写入系统临时目录（tempfile 隔离 + 用后即删），多实例并行互不冲突、无残留
- **错误检测（v1.1 新增）**：每块先做状态校验——mermaid 语法错误会打印精确的 parse error
  并跳过该块（不再静默产出错误横幅图/空白图）；全部跑完后退出码 = 存在失败块 ? 1 : 0，
  可用于自动化流程判断

### 二、Markdown + PNG → Word（`scripts/gen_docx.py`）

```bash
# 渲染图输出到 render_out/ 后，直接生成 docx（自动从 md 首个 H1 取标题）
python scripts/gen_docx.py <md路径> --docx <输出.docx> --png-dir <render_out目录>

# 自定义标题/副标题
python scripts/gen_docx.py <md路径> --docx <输出.docx> --png-dir <render_out目录> \
    --title "文档标题" --subtitle "副标题"
```

关键行为：
- **mermaid 代码块 → 嵌入对应 PNG**（按 `mermaid_0.png` 顺序对应 md 中的 mermaid 块）
- 某块 PNG 缺失时插入灰色占位文字 `[图表渲染失败: N]` 并继续（不会崩溃）
- **剥离所有 markdown 语法**：`**加粗**`、`` `代码` ``、`[链接](url)`（只保留显示文字）、
  表格语法、引用 `>`、列表标记
- **嵌套列表**：按缩进层级转 Word 的 List Bullet / List Bullet 2 / List Bullet 3 样式，
  有序列表嵌套自动加深缩进
- **行内图片**：`![alt](path)` 直接嵌入文档，相对路径基于 md 所在目录解析；图片缺失给灰色占位
- 引用块统一渲染为灰色缩进文字（不做任何字段名过滤）
- 标题（##/###）转为 Word 标题样式；表格转 Table Grid（深蓝表头白字）；代码块用等宽字体 + 浅灰底
- 图片按 6.3 英寸等比缩放，超高图按高度缩放

## 端到端示例（md → docx）

```bash
# 1. 渲染 md 里所有 mermaid 块 → PNG
python scripts/render_mermaid.py 需求.md --out ./render_out --format png --scale 2

# 2. 生成 Word（自动嵌入 PNG）
python scripts/gen_docx.py 需求.md --docx 需求.docx --png-dir ./render_out
```

## 常见问题

| 现象 | 处理 |
|------|------|
| 提示找不到 mermaid.min.js | 从 https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js 下载放入 `assets/`，或用 `--mermaid-js` 指定 |
| 提示找不到 headless Chromium | 执行 `pip install playwright && playwright install chromium`，或用 `--shell` 指定浏览器路径 |
| 渲染超时 | 增大 `--virtual-time-budget`（默认 10000ms），或检查 mermaid 语法 |
| 某块报「mermaid 语法/运行错误」 | 按提示的 parse error 定位修复该块源码；其余块不受影响 |
| 中文乱码 | 确认系统已装中文字体（Windows 一般自带宋体/微软雅黑） |
| docx 表格列数报错 | 检查 md 表格每行列数一致（表头列数 = 数据行列数） |
