# Mermaid图表转图片和Word（mermaid-doc-renderer）

Mermaid 图渲染 + Markdown 转 Word 文档的一体化**离线**工具链。

把 Mermaid 代码变成高清图片（PNG/SVG/PDF），再把图和 Markdown 文字变成排版干净的 Word 文档。

## 能力

| 命令 | 说明 |
|------|------|
| `render_mermaid.py` | 提取 Markdown 里的 ```mermaid 块，渲染为 PNG / SVG / WebP / PDF / JPG（完全离线，语法错误精确报错不产出坏图） |
| `gen_docx.py` | 把 Markdown 转成 Word（.docx），mermaid 图用 PNG 嵌入，支持嵌套列表/行内图片，剥离全部 markdown 语法 |

## 快速开始

```bash
pip install Pillow python-docx   # 依赖

# 1. 渲染 Mermaid → PNG（2x 高清，自动裁白边）
python scripts/render_mermaid.py 需求.md --out ./render_out --format png --scale 2

# 2. Markdown + PNG → Word
python scripts/gen_docx.py 需求.md --docx 需求.docx --png-dir ./render_out
```

输出 `render_out/mermaid_0.png`、`mermaid_1.png`…（按 md 中顺序）。

## 特性

- **零硬编码路径，开箱即用**：自动探测 Playwright 浏览器缓存 / 系统 Chrome / Edge，
  覆盖 Windows / macOS / Linux；找不到时给出明确的安装指引
- **错误检测**：mermaid 语法错误的块会打印精确 parse error 并跳过，
  不再静默产出"错误横幅图"；存在失败块时退出码为 1，便于自动化集成
- **无残留、可并行**：临时文件走系统 tempfile 目录，用后即删
- **快速裁边**：白边裁剪用 PIL ImageChops 实现，大图毫秒级完成
- **支持格式**：PNG（headless 截图 DSF 缩放）、SVG（DOM 提取矢量）、WebP/JPG/PDF（PNG 转换）

## 依赖

- Python：`Pillow` + `python-docx`
- 浏览器三选一：Playwright 的 headless shell（推荐）/ Chrome / Edge
- `assets/mermaid.min.js`（v10，离线加载，本仓库自带）

> 不使用 cairosvg 的原因：mermaid 生成的 SVG 含复杂 CSS/foreignObject，
> cairosvg 常报 `mismatched tag` 且中文字体支持差；截图方式零兼容风险。

## 许可证

MIT
