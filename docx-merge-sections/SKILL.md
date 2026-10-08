---
name: docx-merge-sections
description: 合并两个 Word(.docx) 文档，支持按章节区间【交错插入】而不仅是首尾拼接。处理损坏的图片关系、自动编号(numId)冲突、图片/样式重映射。当用户要把两份需求规格说明书/报告/制度文档合并成一份，或要把某文档的若干章节插入另一文档的指定位置时使用。关键词：合并word、合并docx、文档合并、章节合并、docx 损坏、KeyError docx、python-docx 打不开。
agent_created: true
---

# 合并 Word 文档（按章节交错插入）

## 何时用
- 把两份 docx 合并成一份，且需要**保留主干文档的章节结构**，把另一份的某些章节插到指定位置
- 文档因图片关系损坏（`../NULL`、悬空 rId）导致 python-docx 抛异常打不开

## 核心工具链
```
pip install python-docx docxcompose lxml
```
用 **docxcompose 的 `Composer.insert(index, doc)`**，不要手写 XML 深拷贝。

`insert` 的语义（源码要点）：
- `index` 就是 **body child 索引**（不是段落索引）
- 内部 `for element in doc.element.body:` → `body.insert(index, element); index += 1`
- **会自动跳过源文档的 `sectPr`**
- 自动处理：`add_images`、`add_numberings`（numId 重映射）、`add_styles`、`renumber_bookmarks`、`renumber_docpr_ids`

> ⚠️ **最关键的坑**：因为 `index += 1`，**连续 insert 到同一个 index 时，后插的排在前面**。
> 所以：多个块要插到同一锚点时，必须按**期望顺序的逆序**插入。
> 全局插入顺序必须**从后往前**（先插索引大的），否则前面的锚点会被打乱。

## 标准流程

### 阶段 0：勘察（只读，先别动手）
用 `zipfile + lxml` 直接解析 XML 拿真实结构。**不要依赖 python-docx 打开**（源文件可能已损坏）：

```python
import zipfile
from lxml import etree
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
z = zipfile.ZipFile(path)
root = etree.fromstring(z.read('word/document.xml'))
kids = list(root.find(W+'body'))
# 输出每个 child 的：索引 / pStyle styleId / 文字 / 图片数 / 表格行数
```

**必须确认 styleId → 标题层级的映射**（每个文档都可能不同，没有统一规律）：
```python
st = etree.fromstring(z.read('word/styles.xml'))
for s in st.findall(W+'style'):
    print(s.get(W+'styleId'), '->', s.find(W+'name').get(W+'val'))
```
实测常见映射：`'3'→heading 1, '4'→heading 2, '2'→heading 3, '5'→heading 4, '6'→heading 5`
（注意 `'2'` 是 H3 不是 H2！）

**两份文档 styleId 映射一致时，迁移无需样式重映射** —— 这会大幅简化工作。

再统计两边的段落/表格/图片数、numId 数量、media 文件数，作为验收基线。

### 阶段 1：修复损坏文档（如有）
脚本：`scripts/repair_broken_docx.py`

**两个必须避开的坑（都造成过整篇误删）**：

1. **禁止跨元素正则删除 drawing**
   ```python
   # ❌ 灾难：非贪婪 .*? 会从第一个 <w:drawing> 一路吞到目标 rId
   re.sub(r'<w:drawing>.*?rId54.*?</w:drawing>', '', xml, flags=re.S)
   ```
   正确做法：lxml **遍历每个 `w:drawing`**，只在它自己的 `a:blip/@r:embed` 命中失效 rId 时才删它本身：
   ```python
   for drawing in list(root.iter(f'{{{W}}}drawing')):
       hit = any(blip.get(f'{{{R}}}embed') in bad_rids
                 for blip in drawing.iter(f'{{{A}}}blip'))
       if hit:
           parent = drawing.getparent()
           parent.remove(drawing)
   ```

2. **rels 的 Target 是相对 `word/` 目录解析的**（rels 位于 `word/_rels/`）
   ```python
   # ❌ 错误：media/image1.png 不在包内 → 全部图片被误判为悬空
   norm = target.lstrip('/')
   # ✅ 正确
   import posixpath
   norm = (target.lstrip('/') if target.startswith('/')
           else posixpath.normpath(posixpath.join('word', target)))
   ```

**修完必须断言**：body children 数、表格数、字数 与修复前一致（字数偏差 >5% 即中止）。

### 阶段 2：把源文档拆成块
按索引区间裁剪，**保留 sectPr**，其余逆序删除，另存为 chunk docx：
```python
from docx import Document
def make_chunk(src, out, start, end):
    doc = Document(src)
    body = doc.element.body
    children = list(body)          # 先取快照，索引才对应原文档
    for i in range(len(children)-1, -1, -1):
        el = children[i]
        if el.tag.endswith('}sectPr'):
            continue               # 保留 sectPr
        if not (start <= i <= end):
            body.remove(el)
    doc.save(out)
```

**层级对齐**：如果两文档层级惯例不同（如源文档 H2 下直接挂 H4，主干文档是 H2→H3→H4），直接改 XML 的 `w:pStyle/@w:val`：
```python
def restyle(doc, from_id, to_id):
    for p in doc.paragraphs:
        pPr = p._p.find(qn('w:pPr'))
        if pPr is None: continue
        ps = pPr.find(qn('w:pStyle'))
        if ps is not None and ps.get(qn('w:val')) == from_id:
            ps.set(qn('w:val'), to_id)
```
比 `p.style = doc.styles['Heading 3']` 更可靠。

### 阶段 3：组装（严格从后往前）
```python
from docx import Document
from docxcompose.composer import Composer

master = Document(B_repaired)
composer = Composer(master)
for path, idx in PLAN:            # PLAN 已按 index 从大到小排好
    composer.insert(idx, Document(path))
master.save(OUT)
```
- 追到文末用 `idx = len(master.element.body) - 1`（sectPr 必须是 body 的最后一个元素）
- 每插一个块打印 `before -> after`，核对增量是否等于该块的元素数（sectPr 不带入）

### 阶段 4：后处理
改标题文字要**保留格式**：只改首个 run，清空其余 run（直接赋值 `p.text` 会丢格式）：
```python
def set_para_text(p, text):
    runs = p.runs
    if not runs:
        p.add_run(text); return
    runs[0].text = text
    for r in runs[1:]:
        r.text = ''
```

### 阶段 5：验收（脚本化断言）
必查项：
1. body children 数 == 主干原数 + 各块元素数之和（sectPr 不计）
2. 表格数、图片数与基线一致
3. 正文字数不低于主干原字数
4. **末尾元素必须是 `sectPr`**
5. 图片引用零失效：遍历 `a:blip/@r:embed` → rels → 部件是否存在
6. numId 全部有定义（文档引用的 numId ⊆ numbering.xml 定义的；`numId=0` 表示"无编号"，合法）
7. `[Content_Types].xml` 未声明部件数 == 0
8. python-docx 能重新打开，且能遍历全部表格单元格
9. 打印章节快照（H1/H2/H3 全量）人工核对有无错位、孤立子节

## 内容取舍的决策建议
合并前先用**关键词词频交叉验证**判断两份文档的关系，这决定了合并策略：
- 互补（A 讲 X、B 讲 Y）→ 保留主干骨架，另一份独有章节整块插入
- 重叠（同名章节）→ 逐一判定"超集/子集/同名异义"，**只有内容实质相同才去重**；名字像但业务不同（如「常规文件报送」vs「常规报送记录」）必须都保留并改名区分
- 新旧版本 → 以新版为准，回补旧版独有子节

不要擅自改动主干文档的既有章节编号（可能有意或已知的遗留瑕疵），除非用户明确要求。

## 验收后的收尾提醒
- 目录（TOC）是域码，合并后需用户在 Word 中手动「更新域」
- 修订记录表新增版本行时，「编写人/评审人」通常留空让用户补
