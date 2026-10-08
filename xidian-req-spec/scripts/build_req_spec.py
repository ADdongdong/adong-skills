# -*- coding: utf-8 -*-
"""
按《开源证券工作底稿科技管理系统v4.0升级》需求规格说明书规范生成 docx。

版本 v1.1（2026-10-08）—— 相对 v1.0 补齐三件"用户明确要求、但原脚本靠人肉补"的事：
① 目录（TOC 域）自动更新；② 每张表显式全边框；③ 逐条列用真实项目符号。
另修两处模板遗留：菜单目录表与修改历史表里的**上一份文档的行**、目录域里的**旧条目缓存**。
（这三条同时写进了 SKILL.md 与 references/03、04。）

版本 v1.2（2026-10-08）—— **插图**：`figure()` / `('fig', {...})` 块，图注用「列出段落1」样式、
图片居中并按正文区**宽 15cm / 高 20.5cm** 双向封顶等比缩放（纵向流程图按高度反算宽度，
否则一张图跨两三页）；`req(...)` 的 `界面原型图` 也支持直接传图片路径。
图源建议先用 skill `mermaid转图片` 把 Markdown 里的 ```mermaid 块渲染成 PNG
（`render_mermaid.py <md> --out <图目录> --format png --scale 3`）。

用法：
    from build_req_spec import build
    build(SPEC, r'D:\\out\\XX需求规格说明书V1.0.docx')

SPEC 结构见文件末尾 EXAMPLE。核心特点：
- 以 assets/需求规格说明书_模板.docx 为底，完整继承原文档样式与多级标题自动编号
  （heading 1..6 = styleId 2..7，编号 1. / 1.1. / 1.1.1. / 1.1.1.1. 自动生成，无需手写序号）
- 需求点用 ("req", {...}) 一次性生成「用户场景 / 权限说明 / 功能描述 / 补充说明」四段式
- **目录（TOC 域）自动更新**：清掉模板带来的旧缓存条目 + 置 settings 的 updateFields，
  在 Word/WPS 中打开即按当前正文重排，**不需要手动 F9**（见 _clear_toc_cache）
- **每一张表都带全边框**：显式写 tblBorders（模板的菜单目录表本身是无边框的，
  只套 Table Grid 样式压不住，见 _force_borders）
- **逐条列用真实项目符号**（numbering 定义，不手打"●"）；用户场景保持叙述段落（见 bullets / bullet）
"""
import copy, os, re, shutil, sys, tempfile
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

try:                                   # Windows 控制台默认 GBK：日志里有中文/符号会直接抛异常
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, '..', 'assets', '需求规格说明书_模板.docx')

W = qn('w:p'); T = qn('w:tbl')
# 模板中的 styleId 映射
SID = {'Normal': '1', 'h1': '2', 'h2': '3', 'h3': '4', 'h4': '5', 'h5': '6', 'h6': '7'}
# 需求点四段式的小节名（h5）
SEC_USER = '用户场景'
SEC_PERM = '权限说明'
SEC_FUNC = '功能描述'
SEC_EXTRA = '补充说明'
# 功能描述内部固定要素（按此顺序出现，缺失则跳过）
FUNC_KEYS = ['数据来源', '状态划分', '二级页面', '操作说明', '界面原型图', '字段说明', '字段逻辑']
# 「名称 / 类型 / 规则/说明」明细表标准表头
DETAIL_HEADER = ['名称', '类型', '规则/说明']
# 【菜单目录】表标准表头
MENU_HEADER = ['一级菜单', '二级菜单', '三级菜单']

# ---- 插图（v1.2）----
IMG_CAPTION_SID = '25'      # 「列出段落1」样式（styleId 25）—— 主文档的图注就用它
MAX_IMG_W_CM = 15.0         # 正文区宽度（A4 纵向减左右页边距）
MAX_IMG_H_CM = 20.5         # 单页可用高度余量（A4 29.7cm − 上下页边距 − 图注）


def _image_px(path):
    """读图片像素尺寸；读不到返回 None（python-docx 自带图片头解析，无需 Pillow）。"""
    try:
        from docx.image.image import Image as _DocxImage
        im = _DocxImage.from_file(str(path))
        w = float(getattr(im, 'px_width', None) or im.width)
        h = float(getattr(im, 'px_height', None) or im.height)
        return (w, h) if w > 0 and h > 0 else None
    except Exception:
        return None


def _fit_cm(path):
    """按正文区尺寸等比缩放，返回 `(宽cm, 高cm)`；算不出比例时只给宽度、由 Word 等比缩放。

    **纵向流程图必须按高度封顶**（实测：`flowchart TB` 长链路的图宽高比能到 1:1.8，
    按 15cm 宽铺开就是 27cm 高 —— 一张图横跨两三页，读者得翻页对照）。所以：
    先按最大宽度算高度，超过最大高度就**改按高度反算宽度**。
    """
    px = _image_px(path)
    if not px:
        return MAX_IMG_W_CM, None
    ratio = px[1] / px[0]
    w, h = MAX_IMG_W_CM, MAX_IMG_W_CM * ratio
    if h > MAX_IMG_H_CM:
        h = MAX_IMG_H_CM
        w = h / ratio
    return round(w, 2), round(h, 2)


# tblPr 子元素的 schema 顺序。**顺序错，Word 打开会报"文档已损坏"** ——
# python-docx 1.2 的 CT_TblPr 只暴露了 tblStyle / tblLayout / jc / bidiVisual 的 get_or_add_*，
# tblW / tblBorders 这些得自己按这个顺序插。
TBLPR_SEQ = (
    'w:tblStyle', 'w:tblpPr', 'w:tblOverlap', 'w:bidiVisual', 'w:tblStyleRowBandSize',
    'w:tblStyleColBandSize', 'w:tblW', 'w:jc', 'w:tblCellSpacing', 'w:tblInd',
    'w:tblBorders', 'w:shd', 'w:tblLayout', 'w:tblCellMar', 'w:tblLook',
    'w:tblCaption', 'w:tblDescription', 'w:tblPrChange',
)


def _tbl_pr_set(tblPr, tag, **attrs):
    """在 tblPr 里放一个 `<tag>`：**先删旧的，再按 schema 顺序插**（返回新元素）。"""
    for el in tblPr.findall(qn(tag)):
        tblPr.remove(el)
    e = OxmlElement(tag)
    for k, v in attrs.items():
        e.set(qn(k), v)
    tail = {qn(t) for t in TBLPR_SEQ[TBLPR_SEQ.index(tag) + 1:]}
    for child in tblPr:
        if child.tag in tail:
            child.addprevious(e)
            return e
    tblPr.append(e)
    return e


def _para_of(el):
    """往上找所属段落（域的 run 常被包在 `w:hyperlink` 里）。"""
    p = el.getparent()
    while p is not None and p.tag != W:
        p = p.getparent()
    return p


# 条目开头的**手写序号**：`1、` `2.` `3）` `(4)` `（5）`
LIST_NO_RE = re.compile(r'^\s*(?:\d+\s*[、.．)）]|[(（]\s*\d+\s*[)）])\s*')


def _strip_list_no(text):
    """去掉条目前的**手写序号**。

    与项目符号同时出现会变成两层标记（"● 1、列表排序规则…"），所以**加圆点的场合**顺手去掉。
    `p()` 写的普通段落不动 —— 那里保留手写序号是对的（主文档正文就是 `1、…` 的写法）。
    若某条序号**被正文引用**（如"见第 4 点"），就别用 bullets，改用 `p()` 逐条写。
    """
    return LIST_NO_RE.sub('', str(text))
    p = el.getparent()
    while p is not None and p.tag != W:
        p = p.getparent()
    return p


def _field_runs(body):
    """把正文里**与域有关**的 run 按文档顺序摊平：`[(run, 'begin'|'separate'|'end'|'instr', 文本), …]`。

    处理目录/域必须按这个顺序做配对：段落结构（域跨段、子域嵌套）靠它才能算清。
    """
    seq = []
    for r in body.iter(qn('w:r')):
        fc = r.find(qn('w:fldChar'))
        if fc is not None:
            seq.append((r, fc.get(qn('w:fldCharType')), ''))
            continue
        it = r.find(qn('w:instrText'))
        if it is not None:
            seq.append((r, 'instr', (it.text or '').strip()))
    return seq


# ---- 与主文档一致的直接排版参数（实测自 v4.0.5 document.xml）----
BODY_FONT = '宋体'      # 正文/表格：ascii/hAnsi/eastAsia/cs 均为宋体
BODY_SZ_HALF = 24       # 12pt（w:sz 单位为半磅）
LINE = 1.5              # = w:spacing w:line="360" w:lineRule="auto"
FIRST_LINE_TWIPS = 420  # 用户场景段落首行缩进（2 字符）


def _sty(doc, key):
    sid = SID[key] if key in SID else key
    for s in doc.styles:
        if s.style_id == sid:
            return s
    raise KeyError('style %s not found' % sid)


def fmt_run(run, size_half=BODY_SZ_HALF, bold=None, color=None,
            latin=BODY_FONT, ea=BODY_FONT, hint='eastAsia'):
    """按主文档写法设置字符格式：rFonts(ascii/hAnsi/eastAsia/cs/hint) + sz。
    标题只需 hint=eastAsia（字体字号由 heading 样式决定），传 size_half=None 即可。"""
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts')
        rpr.insert(0, rf)                     # rFonts 必须是 rPr 的首个子元素
    if latin:
        rf.set(qn('w:ascii'), latin); rf.set(qn('w:hAnsi'), latin); rf.set(qn('w:cs'), latin)
    if ea:
        rf.set(qn('w:eastAsia'), ea)
    if hint:
        rf.set(qn('w:hint'), hint)
    if size_half is not None:
        run.font.size = Pt(size_half / 2.0)
    if bold is not None:
        run.font.bold = bold
    if color is not None:
        run.font.color.rgb = color
    return run


def fmt_para(p, line=LINE, first_line=None, left=None, before=None, after=None):
    """按主文档写法设置段落格式：spacing(line=360,lineRule=auto)、ind、before/after。"""
    pf = p.paragraph_format
    if line is not None:
        pf.line_spacing = line                # → w:spacing line=360 lineRule=auto
    if first_line is not None:
        pf.first_line_indent = Pt(first_line / 20.0)   # twips → pt
    if left is not None:
        pf.left_indent = Pt(left / 20.0)
    if before is not None:
        pf.space_before = Pt(before / 20.0)
    if after is not None:
        pf.space_after = Pt(after / 20.0)
    return p


def _set_cell(cell, text, bold=False):
    """写入单元格，段落与字符格式对齐主文档表格：
    spacing(before=0, after=0, line=360) + 宋体 12pt。"""
    p = cell.paragraphs[0]
    for r in list(p.runs):                     # 清掉占位空 run，避免首个 run 无字体属性
        r._element.getparent().remove(r._element)
    fmt_para(p, before=0, after=0)
    fmt_run(p.add_run(str(text)), bold=bold)


def _force_borders(t):
    """给表格写**显式全边框**（`tblBorders`，六个方向 single）。

    **为什么不只靠 `tblStyle = 'Table Grid'`**（v1.1 修）：
    · 模板里那张**菜单目录表本来是无边框的** —— 它的 `tblBorders` 六向全是 `val="none"`，
      而**直接格式比样式更"具体"**，光套 `Table Grid` 样式压不住它，必须把 `none` 换掉；
    · 文档里混着"样式给的框线"与"直接格式给的框线"，一旦某张表被复制粘贴过就说不清了。

    所以统一在收尾时给**每一张**表都写死边框：`single` + `sz=4`（0.5pt，与主文档表格一致；
    `sz=6` 会明显偏粗）+ `color=auto`（跟随文字色）。
    """
    b = _tbl_pr_set(t._tbl.tblPr, 'w:tblBorders')
    for tag in ('w:top', 'w:left', 'w:bottom', 'w:right', 'w:insideH', 'w:insideV'):
        e = OxmlElement(tag)
        e.set(qn('w:val'), 'single'); e.set(qn('w:sz'), '4')
        e.set(qn('w:space'), '0'); e.set(qn('w:color'), 'auto')
        b.append(e)


def _fix_table(t, widths):
    """统一表格版式：固定列宽 + 表宽 100% + 全边框。"""
    t.autofit = False
    tblPr = t._tbl.tblPr
    _tbl_pr_set(tblPr, 'w:tblW', **{'w:type': 'pct', 'w:w': '5000'})
    _tbl_pr_set(tblPr, 'w:tblLayout', **{'w:type': 'fixed'})
    grid = t._tbl.find(qn('w:tblGrid'))
    if grid is not None:
        for gc in list(grid):
            grid.remove(gc)
        for wd in widths:
            gc = OxmlElement('w:gridCol'); gc.set(qn('w:w'), str(int(wd * 567))); grid.append(gc)
    _force_borders(t)


class Builder:
    def __init__(self, template=TEMPLATE):
        self._tmp = os.path.join(tempfile.gettempdir(), '_req_spec_tmp_%d.docx' % os.getpid())
        shutil.copy2(template, self._tmp)
        self.doc = Document(self._tmp)
        self._clear_skeleton()
        self._clear_toc_cache()          # 目录：清掉模板带来的旧条目
        self._auto_update_fields()       # 目录：打开文档即自动重排（不必手动 F9）
        self._bullet_numid_value = None  # 项目符号的 numId 缓存（见 _bullet_numid）

    # ---------- 基础 ----------
    def _clear_skeleton(self):
        """删除模板中「菜单目录」表之后的所有骨架内容（保留封面/修改历史/编写说明/目录域/菜单目录）。"""
        body = self.doc.element.body
        children = list(body)
        menu_idx = None
        for i, el in enumerate(children):
            if el.tag != T:
                continue
            head = ''.join(t.text or '' for t in el.iter(qn('w:t')))[:12]
            if head.startswith('一级菜单'):
                menu_idx = i
        if menu_idx is None:
            return
        for i, el in enumerate(children):
            if i > menu_idx and el.tag in (W, T):
                body.remove(el)
        # 空白标题段会占掉一个自动编号（如出现孤立的"2."）。
        # 注意：模板尾部这类段落常同时承载分节符（pPr/sectPr），直接删除会破坏页面设置，
        # 因此只摘掉它的标题样式与编号，保留段落本身。
        for p in body.findall(W):
            ppr = p.find(qn('w:pPr'))
            if ppr is None:
                continue
            st = ppr.find(qn('w:pStyle'))
            sid = st.get(qn('w:val')) if st is not None else None
            if sid not in SID.values():
                continue
            if ''.join(t.text or '' for t in p.iter(qn('w:t'))).strip():
                continue
            ppr.remove(st)
            for np in ppr.findall(qn('w:numPr')):
                ppr.remove(np)

    # ---------- 目录（TOC 域） ----------
    def _clear_toc_cache(self, levels=None):
        """**目录：清掉模板带过来的旧缓存结果，并把域标成"待更新"。**

        模板 `assets/需求规格说明书_模板.docx` 的目录域里存着**另一份文档的条目**
        （"1. 引言 / 1.1 编写目的 …"）。不清掉的话，凡是不自动更新域的阅读器（在线预览、
        部分 WPS）打开就会显示这些**与本文档毫不相干**的条目 —— 比"空目录"更容易让人
        以为文档写错了。清空后只剩「域起止 + `TOC \\o "1-3" \\h \\u` 指令」，
        由 `_auto_update_fields()` 让 Word/WPS 打开时按当前正文重排。

        实现要点（直接改 XML 的坑）：
        · 目录缓存**跨多个段落**，每条一目；且**首条与域起点同段、末段与域终点同段** ——
          所以要分三处清：独占的整段删掉、起点段删 `separate` 之后的、终点段删 `end` 之前的；
        · 域的配平用**深度计数**（`begin` +1 / `end` -1 回到 0 即本域），别用"往后找第一个 end"，
          因为域里嵌着 HYPERLINK / PAGEREF 这些子域，第一个 end 是子域的。
        """
        seq = _field_runs(self.doc.element.body)
        begin = sep = None
        for i, (r, kind, val) in enumerate(seq):
            if kind == 'instr' and val.upper().startswith('TOC'):
                if levels:
                    self._set_toc_switch(r, levels)
                for j in range(i - 1, -1, -1):
                    if seq[j][1] == 'begin':
                        begin = j
                        break
                for j in range(i + 1, len(seq)):
                    if seq[j][1] == 'separate':
                        sep = j
                        break
                break
        if begin is None or sep is None:
            return
        depth, end = 0, None
        for j in range(begin, len(seq)):
            if seq[j][1] == 'begin':
                depth += 1
            elif seq[j][1] == 'end':
                depth -= 1
                if depth == 0:
                    end = j
                    break
        if end is None or end <= sep:
            return
        sep_run, end_run = seq[sep][0], seq[end][0]
        p_sep, p_end = _para_of(sep_run), _para_of(end_run)
        # ① 域内独占的整段（一条目一段）整段删掉
        node = p_sep.getnext()
        while node is not None and node is not p_end:
            nxt = node.getnext()
            if node.tag in (W, T):
                node.getparent().remove(node)
            node = nxt
        # ② 起点段：separate 之后的（首条缓存）删掉
        node = sep_run.getnext()
        while node is not None:
            nxt = node.getnext()
            p_sep.remove(node)
            node = nxt
        # ③ 终点段：end 之前的（末条缓存）删掉，**保留 end 与段落样式**
        if p_end is not p_sep:
            for node in list(p_end):
                if node is end_run:
                    break
                if node.tag == qn('w:pPr'):
                    continue
                p_end.remove(node)
        seq[begin][0].find(qn('w:fldChar')).set(qn('w:dirty'), 'true')

    def _set_toc_switch(self, instr_run, levels):
        """改目录的收录层级：`\\o "1-3"` → `\\o "1-4"` 等（默认沿用主文档的 1-3）。"""
        it = instr_run.find(qn('w:instrText'))
        it.text = re.sub(r'\\o\s+"[^"]*"', '\\o "%s"' % levels, it.text)
        return it.text

    def toc_levels(self, levels):
        """对外：指定目录收录到几级标题（如 `'1-4'` 让 H4 功能点也进目录）。"""
        for r, kind, val in _field_runs(self.doc.element.body):
            if kind == 'instr' and val.upper().startswith('TOC'):
                self._set_toc_switch(r, levels)
                return True
        return False

    def _auto_update_fields(self):
        """settings.xml 里置 `w:updateFields=true` —— 打开文档时自动更新域（含目录）。

        **位置坑**：`w:updateFields` 在 CT_Settings 的元素顺序里夹在
        `w:savePreviewPicture … alwaysMergeEmptyNamespace` 与
        `w:hdrShapeDefaults / w:footnotePr / w:endnotePr / w:compat` 之间，
        **不能随手 append 到 settings 末尾** —— 顺序错 Word 会报"文档已损坏"。
        这里拿顺序上紧跟其后、且必然存在的 `w:compat` 当锚点，插到它前面。
        """
        settings = self.doc.settings.element
        for el in settings.findall(qn('w:updateFields')):
            el.set(qn('w:val'), 'true')
            return
        e = OxmlElement('w:updateFields')
        e.set(qn('w:val'), 'true')
        anchor = None
        for tag in ('w:compat', 'w:docVars', 'w:rsids', 'w:mathPr', 'w:themeFontLang',
                    'w:clrSchemeMapping', 'w:shapeDefaults', 'w:decimalSymbol', 'w:listSeparator'):
            anchor = settings.find(qn(tag))
            if anchor is not None:
                break
        if anchor is not None:
            anchor.addprevious(e)
        else:
            settings.append(e)

    # ---------- 项目符号 ----------
    def _bullet_numid(self):
        """取项目符号用的 `numId`（缓存一次）。见 `_find_or_make_bullet`。"""
        if self._bullet_numid_value is None:
            self._bullet_numid_value = self._find_or_make_bullet() or ''
        return self._bullet_numid_value or None

    def _find_or_make_bullet(self):
        """**优先复用模板里现成的 bullet 定义** —— 缩进（`left=420 hanging=420`）与圆点样式
        跟主文档完全一致，不用自己造。

        模板里有好几种项目符号（`\\uf06c` 实心圆 / `\\uf0d8` 方块 / `\\uf0b2` 方点），
        **优先挑实心圆** —— 中文商务文档的项目符号惯例就是实心圆，方块更像"子级标记"。
        模板里连 bullet 定义都没有时**克隆**一份（新的 abstractNumId / numId，不动原有定义）；
        连可克隆的源都没有则返回 `None`（调用处退回普通段落）。
        """
        numbering = self.doc.part.numbering_part.element
        circles, others, src, src_circle = set(), set(), None, None
        for an in numbering.findall(qn('w:abstractNum')):
            lvl0 = None
            for lvl in an.findall(qn('w:lvl')):
                if (lvl.get(qn('w:ilvl')) or '0') == '0':
                    lvl0 = lvl
            if lvl0 is None:
                continue
            fmt = lvl0.find(qn('w:numFmt'))
            if fmt is None or fmt.get(qn('w:val')) != 'bullet':
                continue
            aid = an.get(qn('w:abstractNumId'))
            lt = lvl0.find(qn('w:lvlText'))
            is_circle = lt is not None and (lt.get(qn('w:val')) or '') == '\uf06c'
            (circles if is_circle else others).add(aid)
            if src is None:
                src = an
            if is_circle and src_circle is None:
                src_circle = an
        for want in (circles, others):
            if not want:
                continue
            for num in numbering.findall(qn('w:num')):
                ref = num.find(qn('w:abstractNumId'))
                if ref is not None and ref.get(qn('w:val')) in want:
                    return num.get(qn('w:numId'))
        if src_circle is not None:
            src = src_circle
        if src is None:
            return None
        new_an = copy.deepcopy(src)
        for tag in ('w:nsid', 'w:tmpl'):      # 文档级标识，跟着复制会撞车
            for el in new_an.findall(qn(tag)):
                new_an.remove(el)
        aid = str(max(int(x.get(qn('w:abstractNumId'))) for x in numbering.findall(qn('w:abstractNum'))) + 1)
        new_an.set(qn('w:abstractNumId'), aid)
        first_num = numbering.find(qn('w:num'))
        if first_num is not None:
            first_num.addprevious(new_an)     # abstractNum 必须排在所有 w:num 之前
        else:
            numbering.append(new_an)
        nid = str(max(int(x.get(qn('w:numId'))) for x in numbering.findall(qn('w:num'))) + 1)
        new_num = OxmlElement('w:num')
        new_num.set(qn('w:numId'), nid)
        ref = OxmlElement('w:abstractNumId')
        ref.set(qn('w:val'), aid)
        new_num.append(ref)
        numbering.append(new_num)
        return nid

    def bullet(self, text):
        """一条**项目符号**（真实编号列表，不是手打的"●"）：圆点样式与缩进由模板的
        bullet 定义提供（左 420 悬挂 420）。

        用在**逐条并列**的内容上：权限说明 / 补充说明 / 数据来源 / 状态划分 / 字段逻辑。
        **用户场景不加** —— 它是叙述性段落，加了圆点会读成清单，反而不像"场景"。

        条目**开头的手写序号（`1、`）会被去掉** —— 不然会叠成"● 1、…"两层标记（见 `_strip_list_no`）。
        """
        p = self._add(_strip_list_no(text), 'Normal')
        nid = self._bullet_numid()
        if nid is None:
            return p
        ppr = p._p.get_or_add_pPr()
        numpr = ppr.get_or_add_numPr()        # 按 schema 顺序插（必须在 w:spacing / w:ind 之前）
        ilvl = OxmlElement('w:ilvl'); ilvl.set(qn('w:val'), '0')
        numid = OxmlElement('w:numId'); numid.set(qn('w:val'), nid)
        numpr.append(ilvl); numpr.append(numid)
        return p

    def _add(self, text, style_key, first_line=None, line=LINE):
        p = self.doc.add_paragraph(text, style=_sty(self.doc, style_key))
        fmt_para(p, line=line, first_line=first_line)
        if style_key in ('Normal',):
            for r in p.runs:
                fmt_run(r)
        else:                                  # heading：只加 hint=eastAsia
            for r in p.runs:
                fmt_run(r, size_half=None, latin=None, ea=None)
        return p

    # ---------- 块 ----------
    def h(self, level, text):
        return self._add(text, 'h%d' % level)

    def p(self, text=''):
        """普通段落（无缩进），与主文档正文一致：宋体 12pt + 1.5 倍行距。"""
        return self._add(text, 'Normal')

    def p_indent(self, text=''):
        """首行缩进 2 字符的正文段落（主文档「用户场景」正文即此格式）。"""
        return self._add(text, 'Normal', first_line=FIRST_LINE_TWIPS)

    def cover(self, 系统名=None, 版本=None, 公司=None, 日期=None):
        """就地改写封面与修改历史（可选）。"""
        body = self.doc.element.body
        paras = [el for el in body if el.tag == W]
        def set_at(idx, val):
            if val is None or idx >= len(paras):
                return
            el = paras[idx]
            for t in el.iter(qn('w:t')):
                t.text = ''
            ts = list(el.iter(qn('w:t')))
            if ts:
                ts[0].text = val
        # 模板封面：7=系统名 8=版本 17=公司 18=日期（下标基于模板固定版式）
        set_at(7, 系统名); set_at(8, 版本); set_at(17, 公司); set_at(18, 日期)

    def history(self, rows):
        """文档修改历史表：[[版本号,修改日期,编写人,评审人,批准人,修改内容], ...]

        与 `menu_table` 同理：**保留表头行、清掉其余行再追加**（模板表里带着上一版的记录，
        直接追加会变成"旧记录 + 新记录"）。
        """
        t = self.doc.tables[0]
        for tr in t._tbl.findall(qn('w:tr'))[1:]:
            t._tbl.remove(tr)
        for r in rows:
            cells = t.add_row().cells
            for i, v in enumerate(r[:len(cells)]):
                _set_cell(cells[i], v)
        _fix_table(t, [1.8, 2.4, 1.8, 1.8, 1.8, 5.4])

    def menu_table(self, rows):
        """菜单目录表：[[一级菜单,二级菜单,三级菜单], ...]（可含表头行）

        **模板里那张表带着底稿系统的整套菜单（52 行）**，而这里是"追加"语义 ——
        不先清掉就会得到「底稿菜单 + 本系统菜单」两份。所以：**保留表头行、清掉其余行，再追加**
        （传进来的表头行与模板表头重复，跳过）。

        注意在 **XML 层**删行（`w:tr`）：python-docx 的 `table.rows` 视图与 XML 不完全同步，
        有合并单元格时容易看漏。
        """
        t = self.doc.tables[1]
        for tr in t._tbl.findall(qn('w:tr'))[1:]:
            t._tbl.remove(tr)
        for r in rows:
            if list(r)[:3] == MENU_HEADER:
                continue
            cells = t.add_row().cells
            for i, v in enumerate(r[:len(cells)]):
                _set_cell(cells[i], v)
        _fix_table(t, [3.0, 5.0, 7.0])

    def table(self, rows, widths=None):
        rows = list(rows)
        ncol = len(rows[0])
        t = self.doc.add_table(rows=0, cols=ncol)
        t.style = 'Table Grid'
        for r in rows:
            cells = t.add_row().cells
            for i, v in enumerate(r[:ncol]):
                _set_cell(cells[i], v)
        _fix_table(t, widths or ([15.0 / ncol] * ncol))
        return t

    def kv(self, label, value):
        """「标签：内容」单行 —— 权限说明 / 功能描述内部要素的标准句式。"""
        return self.p('%s：%s' % (label, value) if value else '%s：' % label)

    def bullets(self, items, indent=False, bullet=True):
        """逐条列。

        `bullet=True`（默认）→ **真实项目符号**（用 numbering 定义，圆点与悬挂缩进交给 Word 排）；
        `bullet=False` → 普通段落（`indent=True` 时首行缩进 2 字符）。
        **用户场景用 `bullet=False`**：它是叙述性段落，加圆点会被读成清单，反而不像"场景"。

        **只有一条时不加圆点**（`len(items) == 1` → 普通段落）：单条内容写成一句话更自然，
        「● 无」「● 不涉及」这类只有一个圆点跟着两个字的排版也会显得怪。
        """
        items = list(items)
        use_bullet = bullet and len(items) > 1
        for it in items:
            if use_bullet:
                self.bullet(it)
            else:
                (self.p_indent if indent else self.p)(it)

    def figure(self, 图片, 图注=None, 宽度=None, 说明=None):
        """**插一张图**（v1.2）：**图注在图片上方**（「列出段落1」样式、冒号结尾）+ 图片居中。

        参数与 `req()` 一样用中文键：`('fig', dict(图注='…', 图片=r'…'))`。

        规范见 `references/03-样式与编号规范.md` 第六节。三条尺寸约定：
        · 宽上限 **15cm**（A4 纵向正文区）；
        · 高上限 **20.5cm** —— 纵向流程图超过就**改按高度反算宽度**（否则一张图跨两三页）；
        · 图注里**不写"图 4.5-1"这类编号**：标题编号是样式自动生成的，手写图号一旦插删章节就对不上。
          用「回函管理业务数据分工：」这种**描述性图注**（主文档即如此）。

        `图片` 不存在时插入灰色占位文字并打印警告，**不让整篇文档生成失败**。
        """
        if 图注:
            cap = str(图注).strip()
            if not cap.endswith(('：', ':')):
                cap += '：'
            p = self.doc.add_paragraph(cap, style=_sty(self.doc, IMG_CAPTION_SID))
            fmt_para(p, line=LINE)
            for r in p.runs:
                fmt_run(r)
        p = self.doc.add_paragraph()
        fmt_para(p, line=LINE)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if not 图片 or not os.path.isfile(str(图片)):
            r = p.add_run('[图表未找到：%s]' % (图片,))
            fmt_run(r, color=RGBColor(0x99, 0x99, 0x99))
            print('⚠ 图片不存在，已插入占位：', 图片)
            return p
        w_cm, h_cm = _fit_cm(图片) if 宽度 is None else (float(宽度), None)
        run = p.add_run()
        run.add_picture(str(图片), width=Cm(w_cm), height=(Cm(h_cm) if h_cm else None))
        if 说明:
            np_ = self.doc.add_paragraph(str(说明), style=_sty(self.doc, 'Normal'))
            fmt_para(np_, line=LINE)
            for r in np_.runs:
                fmt_run(r)
        return p

    # ---------- 需求点 ----------
    def req(self, title, 用户场景=None, 权限说明=None, 功能描述=None, 补充说明=None, level=4):
        """
        生成一个完整需求点：
            h{level}   功能点名称（默认 level=4；当【菜单目录】的一级菜单本身即功能点时用 level=3）
              h{level+1} 用户场景      → **叙述段落**（首行缩进 2 字符，不加项目符号）
              h{level+1} 权限说明      → 逐条列（**项目符号**；菜单权限/功能权限/列表数据权限/使用人员）
              h{level+1} 功能描述      → {'数据来源':[], '状态划分':[], '二级页面':表, '操作说明':表,
                                         '界面原型图':str, '字段逻辑':表/[], '字段说明':表}
                                        （多条目 → 项目符号；二维列表 → 表格）
              h{level+1} 补充说明      → 逐条列（**项目符号**，默认「无」）
        """
        sec = level + 1
        self.h(level, title)
        if 用户场景 is not None:
            self.h(sec, SEC_USER)
            # 主文档中「用户场景」正文为首行缩进 2 字符，其余小节不缩进。
            # **这里不加项目符号**：用户场景是叙述段落，加圆点就变成清单了。
            self.bullets(用户场景 if isinstance(用户场景, (list, tuple)) else [用户场景],
                         indent=True, bullet=False)
        if 权限说明 is not None:
            self.h(sec, SEC_PERM)
            self.bullets(权限说明 if isinstance(权限说明, (list, tuple)) else [权限说明])
        if 功能描述 is not None:
            self.h(sec, SEC_FUNC)
            for key in FUNC_KEYS:
                if key not in 功能描述:
                    continue
                val = 功能描述[key]
                if key in ('数据来源', '状态划分'):
                    if isinstance(val, (list, tuple)) and val and isinstance(val[0], (list, tuple)):
                        self.p('%s：' % key)
                        self.table(val)            # 二维 → 状态/来源表格
                        continue
                    items = list(val) if isinstance(val, (list, tuple)) else [val]
                    if len(items) == 1:            # 单项 → 与原文一致，标签与内容同行
                        self.p('%s：%s' % (key, items[0]))
                    else:
                        self.p('%s：' % key)
                        self.bullets(items)
                elif key in ('操作说明', '二级页面', '字段说明'):
                    self.p('%s：' % key)
                    if val:
                        self.table(val)
                elif key == '界面原型图':
                    # 传图片路径（或 {'图片':…, '图注':…}）→ **直接插图**；否则仍按文字写（"无" / 待补）
                    if isinstance(val, dict):
                        fig = dict(val)
                        self.figure(fig.pop('图片', None), 图注=fig.pop('图注', None) or '界面原型图', **fig)
                    elif val and os.path.isfile(str(val)):
                        self.figure(val, 图注='界面原型图')
                    else:
                        self.p('界面原型图：' + (val or '（此处插入页面截图）'))
                elif key == '字段逻辑':
                    if isinstance(val, (list, tuple)) and val and isinstance(val[0], (list, tuple)):
                        self.p('字段逻辑：')
                        self.table(val)            # 二维 → 表格
                    else:
                        items = list(val) if isinstance(val, (list, tuple)) else [val]
                        self.p('字段逻辑：%s' % (items[0] if len(items) == 1 else ''))
                        if len(items) > 1:
                            self.bullets(items)
        if 补充说明 is not None:
            self.h(sec, SEC_EXTRA)
            self.bullets(补充说明 if isinstance(补充说明, (list, tuple)) else [补充说明])

    # ---------- 输出 ----------
    def save(self, path):
        os.makedirs(os.path.dirname(os.path.abspath(path)) or '.', exist_ok=True)
        self.doc.save(path)
        try:
            os.remove(self._tmp)
        except OSError:
            pass
        return path


def build(spec, path):
    b = Builder(spec.get('模板', TEMPLATE))
    cov = spec.get('封面')
    if cov:
        b.cover(**cov)
    if spec.get('文档修改历史'):
        b.history(spec['文档修改历史'])
    if spec.get('菜单目录'):
        b.menu_table(spec['菜单目录'])
    if spec.get('目录层级'):            # 可选：'1-4' 让 H4 功能点也进目录（默认沿用主文档的 1-3）
        b.toc_levels(spec['目录层级'])
    for blk in spec.get('body', []):
        kind = blk[0]
        if kind in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            b.h(int(kind[1]), blk[1])
        elif kind == 'p':
            b.p(blk[1])
        elif kind == 'bullets':         # 段落级逐条列（真实项目符号）
            b.bullets(blk[1])
        elif kind == 'fig':             # 插图：('fig', dict(图注=…, 图片=…, 宽度=…))
            b.figure(**blk[1])
        elif kind == 'table':
            b.table(blk[1], blk[2] if len(blk) > 2 else None)
        elif kind == 'req':
            b.req(**blk[1])
        else:
            raise ValueError('unknown block: %r' % (kind,))
    return b.save(path)


DETAIL = lambda rows: [DETAIL_HEADER] + rows

EXAMPLE = dict(
    封面=dict(系统名='工作底稿科技管理系统', 版本='需求说明书v4.1', 公司='西安西点信息技术有限公司', 日期='2026年9月'),
    文档修改历史=[['V1.0', '2026-09-16', '×××', '', '', '初稿']],
    # 目录层级='1-4',   # 可选：让 H4 功能点也进目录（默认沿用主文档的 1-3）
    菜单目录=[MENU_HEADER, ['首页', '', ''], ['项目管理', '我的项目', '']],
    body=[
        ('h1', '底稿系统标准产品需求'),
        ('h2', 'WEB端需求'),
        ('h3', '首页'),
        ('req', dict(
            title='首页－底稿待办',
            # 用户场景 = 叙述段落（不加项目符号）
            用户场景=['为当前登录用户提供底稿待办处理，并可通过待办详情查看并处理项目的底稿任务待办。'],
            # 权限说明 / 补充说明 = 逐条列 → 自动加项目符号
            权限说明=['菜单权限：登录用户均有首页权限', '功能权限：不涉及',
                      '列表数据权限：所有需要当前登录用户处理的底稿目录', '使用人员：系统管理员'],
            功能描述={
                '数据来源': ['底稿详情页所有需处理的底稿目录'],
                '状态划分': ['无'],
                '操作说明': DETAIL([['提交', '按钮', '勾选需要提交的底稿目录，点击提交按钮可进行提交操作'],
                                    ['更多操作', '下拉选择', '可进行底稿目录索引、附件引用等操作']]),
                '界面原型图': '（此处插入页面截图）',
                '字段逻辑': ['不涉及'],
            },
            补充说明=['无'],
        )),
        # —— 「本章节暂未收录的需求」这类段落级清单，用 bullets 块（真实项目符号）——
        ('h3', '本章节暂未收录的需求'),
        ('p', '以下内容本次未收录，后续版本补充：'),
        ('bullets', ['助手端 / 手机端 / 客户端需求（本期仅 WEB 端）',
                     '各功能点的界面原型图（原型见原型工程）']),
        # —— 插图：图片路径不存在时会插灰色占位并打警告，不会让整篇文档生成失败 ——
        # ('h3', '业务流程'),
        # ('p', '回函管理的业务链路：……。下面三张图分别是……。'),
        # ('fig', dict(图注='回函管理业务数据分工（AI 读取 / 人工定性 / 系统推导）',
        #              图片=r'D:/proj/docs/figures/mermaid_0.png')),
        # 也可以只给宽度（此时不再按高度封顶，自己确认不会跨页）：('fig', dict(图片=…, 宽度=12))

        # —— 定制化需求：**只有项目确有定制内容时才写**；没有就整章不写（含引言 / 需求总览），
        #     不要留空标题（空标题还会白占一个自动编号）。确有定制内容时照下面写：
        # ('h1', '定制化需求'),
        # ('h2', '定制化需求引言'),
        # ('h3', '编写目的'),
        # ('p', '本章节描述……'),
        # ('h3', '项目背景'),
        # ('p', '……'),
        # ('h2', '需求总览'),
        # ('table', [['条目', '需求名称', '新系统主要落点'], ['1.0', '××对接增加字段', '系统对接说明']]),
        # ('h2', '功能需求'),
        # ('req', dict(title='××', 用户场景=[...], 权限说明=[...], 功能描述={...},
        #              补充说明=['定制需求梳理清单原始条目（第 4 部分）'], level=3)),
    ],
)

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'out', '示例输出.docx')
    print('saved ->', build(EXAMPLE, out))
