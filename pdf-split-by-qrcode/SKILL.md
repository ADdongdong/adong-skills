---
name: pdf-split-by-qrcode
description: 按页面上的二维码/条形码将一个大 PDF 切分成多个小 PDF，每个文件以条码内容命名。用于函证打包文件、批量扫描件、快递面单、试卷合订本等"一个条码对应一份文档"的场景。触发词：按二维码切分PDF、按条码拆分PDF、拆分函证打包文件、PDF按二维码命名、split pdf by qrcode、 barcode split。
agent_created: true
---

# 按二维码切分 PDF

## 适用场景

一个 PDF 里连续排列了 N 份文档，**每份文档首页（通常右上角）有一个二维码/条形码作为分隔标记**，
需要按标记切开，并用条码内容给每个子文件命名。

典型：银行函证控制表打包文件（每份询证函首页右上角带 `LC2026xxxxxx` 二维码）。

## 快速开始

```bash
"<PYTHON>" scripts/split_pdf_by_qrcode.py "<输入.pdf>" ["<输出目录>"]
```

- 不传输出目录时，默认在**源文件同级目录**建 `<源文件名>_拆分/`。
- 输出同时生成 `_拆分清单.json`（源路径 / 每份文件的页码区间 / 页数 / 条码值）。

## 环境依赖

| 包 | 用途 | 安装 |
|---|---|---|
| PyMuPDF (`fitz`) | 渲染页面、切分与保存 PDF | `pip install PyMuPDF` |
| opencv-python (`cv2`) | 灰度转换 + 二维码兜底识别 | `pip install opencv-python` |
| numpy / Pillow | 图像数组转换 | `pip install numpy Pillow` |
| pyzbar | 条码识别主引擎 | `pip install pyzbar` |

> **Windows 注意**：pyzbar 需要 zbar 的 DLL。若报 `Unable to find zbar shared library`，
> 装 `pyzbar[scripts]`（`pip install pyzbar[scripts]`）或用 conda 环境。
> 用户本机 `C:/ProgramData/Anaconda3/envs/pytorch/python.exe` 已全量可用（含 fitz 1.26.5、pyzbar、cv2、PIL）。

## 工作流

1. **先探查**：打开 PDF 确认页数与页面尺寸。
   ```python
   import fitz; d = fitz.open(path); print(d.page_count, d[0].rect)
   ```
2. **扫描每页条码**（先裁条码区域，快且准；识别不到再全页兜底）。
3. **交叉校验**：pyzbar 与 OpenCV `QRCodeDetector` 双引擎各跑一遍，
   两次结果一致才进入切分。条码编号通常连续，检查是否缺号（缺号 = 有漏检页）。
4. **内容校验**（重要）：抽取每页首行文本，确认标记页确实是新文档首页
   （如函证场景标记页开头为「银行询证函（格式一）」，末页为「以下由被询证银行填列」）。
5. **切分**：以每个标记页为起点，下一个标记页（或文末）为终点，用 `insert_pdf` 切片保存。
6. **闭环校验**：逐个打开输出文件，重新识别首页条码，与文件名比对，要求 100% 一致。

## 关键实现要点

- **渲染缩放 `ZOOM=3`**：A4 页约 1786×2526 px，右上角二维码约 74×76 px，识别稳定。
  若条码更小或更密，调到 4~5；追求速度可降到 2（先小样本验证）。
- **裁剪区域 `CROP = (0.55, 0.0, 1.0, 0.25)`**：右上角 45% 宽 × 顶部 25% 高。
  条码若在别的位置，按实际改这四个比例（x0, y0, x1, y1）。
- **只认 QRCODE**：函证页同时存在 CODE128（如 `yhhz08060001`），
  必须用 `c.type == 'QRCODE'` 过滤，否则会把条码错当分隔标记。
- **同名保护**：条码重复时自动追加 `_01` `_02` 序号，避免覆盖。
- **文件名净化**：`re.sub(r'[\\/:*?"<>|\r\n\t]', '_', s)`，条码含特殊字符也不会写盘失败。
- **保存参数**：`save(garbage=4, deflate=True)` 压缩去冗余，单份约 90 KB。
- **忽略噪声**：zbar 会打印 `WARNING: zbar\decoder\databar.c ... Assertion "seg->finder >= 0" failed.`，
  这是 DataBar 解码器的已知无害告警，用 `grep -v WARNING` 过滤即可。

## 实测数据（银行控制表2608标记函证打包文件）

- 输入 107 页 A4，输出 15 份，编号 `LC2026006765` ~ `LC2026006779` 连续无缺。
- 分段：前 2 份各 8 页，其余 13 份各 7 页（8+8+7×13 = 107）。
- 注意：**编号顺序与物理页序不完全一致**（…768 → 770 → 769 → 771…），
  说明打包顺序不等于编号顺序，切分后不要假设文件按名称排序就等于原顺序。

## 排查清单

| 现象 | 原因 | 处理 |
|---|---|---|
| 一页都没识别到 | 条码是矢量绘制且渲染太淡 | 提高 `ZOOM` 到 4~5 |
| 识别到的是 CODE128 而非二维码 | 未过滤 `c.type` | 加 `if c.type == 'QRCODE'` |
| 切分份数少于预期 | 某页条码模糊漏检 | 双引擎交叉校验 + 检查编号连续性 |
| 某份页数明显异常（如 1 页或 30 页） | 中间页误识别出条码 | 抽内容文本核对边界 |
| zbar DLL 报错 | 缺 zbar 动态库 | `pip install pyzbar[scripts]` |
