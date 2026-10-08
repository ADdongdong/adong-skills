# -*- coding: utf-8 -*-
"""
按《开源证券工作底稿科技管理系统v4.0升级》需求规格说明书规范生成 docx。

用法：
    from build_req_spec import build
    build(SPEC, r'D:\\out\\XX需求规格说明书V1.0.docx')

SPEC 结构见文件末尾 EXAMPLE。核心特点：
- 以 assets/需求规格说明书_模板.docx 为底，完整继承原文档样式与多级标题自动编号
  （heading 1..6 = styleId 2..7，编号 1. / 1.1. / 1.1.1. / 1.1.1.1. 自动生成，无需手写序号）
- 需求点用 ("req", {...}) 一次性生成「用户场景 / 权限说明 / 功能描述 / 补充说明」四段式
"""
import os, shutil, sys, tempfile
from docx import Document
from docx.shared import Cm, Pt
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

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


def _fix_table(t, widths):
    t.autofit = False
    tblPr = t._tbl.tblPr
    for tag in ('w:tblW', 'w:tblLayout'):
        for el in tblPr.findall(qn(tag)):
            tblPr.remove(el)
    e = OxmlElement('w:tblW'); e.set(qn('w:type'), 'pct'); e.set(qn('w:w'), '5000'); tblPr.append(e)
    e = OxmlElement('w:tblLayout'); e.set(qn('w:type'), 'fixed'); tblPr.append(e)
    grid = t._tbl.find(qn('w:tblGrid'))
    if grid is not None:
        for gc in list(grid):
            grid.remove(gc)
        for w in widths:
            gc = OxmlElement('w:gridCol'); gc.set(qn('w:w'), str(int(w * 567))); grid.append(gc)


class Builder:
    def __init__(self, template=TEMPLATE):
        self._tmp = os.path.join(tempfile.gettempdir(), '_req_spec_tmp_%d.docx' % os.getpid())
        shutil.copy2(template, self._tmp)
        self.doc = Document(self._tmp)
        self._clear_skeleton()

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
        """文档修改历史表：[[版本号,修改日期,编写人,评审人,批准人,修改内容], ...]"""
        tbls = self.doc.tables
        t = tbls[0]
        for r in rows:
            cells = t.add_row().cells
            for i, v in enumerate(r[:len(cells)]):
                _set_cell(cells[i], v)
        _fix_table(t, [1.8, 2.4, 1.8, 1.8, 1.8, 5.4])

    def menu_table(self, rows):
        """菜单目录表：[[一级菜单,二级菜单,三级菜单], ...]（含表头行）"""
        t = self.doc.tables[1]
        for r in rows:
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

    def bullets(self, items, indent=False):
        for it in items:
            (self.p_indent if indent else self.p)(it)

    # ---------- 需求点 ----------
    def req(self, title, 用户场景=None, 权限说明=None, 功能描述=None, 补充说明=None, level=4):
        """
        生成一个完整需求点：
            h{level}   功能点名称（默认 level=4；当【菜单目录】的一级菜单本身即功能点时用 level=3）
              h{level+1} 用户场景      → 段落列表
              h{level+1} 权限说明      → 段落列表（菜单权限/功能权限/列表数据权限/使用人员）
              h{level+1} 功能描述      → {'数据来源':[], '状态划分':[], '二级页面':表, '操作说明':表,
                                         '界面原型图':str, '字段逻辑':表/[], '字段说明':表}
              h{level+1} 补充说明      → 段落列表（默认「无」）
        """
        sec = level + 1
        self.h(level, title)
        if 用户场景 is not None:
            self.h(sec, SEC_USER)
            # 主文档中「用户场景」正文为首行缩进 2 字符，其余小节不缩进
            self.bullets(用户场景 if isinstance(用户场景, (list, tuple)) else [用户场景], indent=True)
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
    for blk in spec.get('body', []):
        kind = blk[0]
        if kind in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            b.h(int(kind[1]), blk[1])
        elif kind == 'p':
            b.p(blk[1])
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
    菜单目录=[['一级菜单', '二级菜单', '三级菜单'], ['首页', '', ''], ['项目管理', '我的项目', '']],
    body=[
        ('h1', '底稿系统标准产品需求'),
        ('h2', 'WEB端需求'),
        ('h3', '首页'),
        ('req', dict(
            title='首页－底稿待办',
            用户场景=['为当前登录用户提供底稿待办处理，并可通过待办详情查看并处理项目的底稿任务待办。'],
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
        ('h1', '定制化需求'),
        ('h3', '需求总览'),
        ('table', [['条目', '需求名称', '新系统主要落点'], ['1.0', '××对接增加字段', '系统对接说明']]),
    ],
)

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'out', '示例输出.docx')
    print('saved ->', build(EXAMPLE, out))
