# -*- coding: utf-8 -*-
"""
只读勘察 docx 结构：body child 索引 / 标题层级 / 表格 / 图片 / numId / styleId 映射。
不依赖 python-docx，源文件损坏也能用。

用法:
    python analyze_structure.py <a.docx> [<b.docx> ...] [--headings-only]
"""
import io
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from lxml import etree

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
A_NS = 'http://schemas.openxmlformats.org/drawingml/2006/main'


def style_map(z):
    """styleId -> 样式名；返回 (全部映射, heading 的 styleId->层级)"""
    try:
        st = etree.fromstring(z.read('word/styles.xml'))
    except KeyError:
        return {}, {}
    full, heads = {}, {}
    for s in st.findall(f'{{{W}}}style'):
        sid = s.get(f'{{{W}}}styleId')
        nm = s.find(f'{{{W}}}name')
        n = nm.get(f'{{{W}}}val') if nm is not None else ''
        full[sid] = n
        if n.startswith('heading'):
            heads[sid] = 'H' + n.split()[-1]
        elif n == 'Title':
            heads[sid] = 'TITLE'
    return full, heads


def analyze(path, headings_only=False):
    print('=' * 78)
    print(path)
    with zipfile.ZipFile(path) as z:
        full, heads = style_map(z)
        root = etree.fromstring(z.read('word/document.xml'))
        body = root.find(f'{{{W}}}body')
        kids = list(body)

        tbls = len(body.findall(f'{{{W}}}tbl'))
        imgs = len(list(root.iter(f'{{{A_NS}}}blip')))
        words = len(''.join(t.text or '' for t in root.iter(f'{{{W}}}t')))
        numpr = len(list(root.iter(f'{{{W}}}numPr')))

        print(f'body children={len(kids)}  表格={tbls}  图片={imgs}  字数={words}  自动编号={numpr}')
        print('末尾元素:', etree.QName(kids[-1]).localname, '(应为 sectPr)')
        print('heading styleId 映射:', heads)

        try:
            nu = etree.fromstring(z.read('word/numbering.xml'))
            nids = [x.get(f'{{{W}}}numId') for x in nu.findall(f'{{{W}}}num')]
            print(f'numbering: abstractNum={len(nu.findall(f"{{{W}}}abstractNum"))} '
                  f'num={len(nids)}')
        except KeyError:
            print('numbering: 无')
        print(f'media 文件: {len([n for n in z.namelist() if n.startswith("word/media/")])}')

        if headings_only:
            return

        print('--- 索引 / 层级 / 文字 / 图片数 ---')
        M = dict(heads)
        for i, el in enumerate(kids):
            q = etree.QName(el).localname
            if q == 'p':
                pPr = el.find(f'{{{W}}}pPr')
                sid = None
                if pPr is not None:
                    ps = pPr.find(f'{{{W}}}pStyle')
                    sid = ps.get(f'{{{W}}}val') if ps is not None else None
                txt = ''.join(t.text or '' for t in el.iter(f'{{{W}}}t')).strip()
                n_im = len(list(el.iter(f'{{{A_NS}}}blip')))
                if sid in M:
                    print(f'  [{i}] {M[sid]:5s} img={n_im} {txt[:60]}')
                elif n_im:
                    print(f'  [{i}] {"":5s} img={n_im} {txt[:60]}')
            elif q == 'tbl':
                rows = el.findall(f'{{{W}}}tr')
                hdr = ''.join(x.text or '' for x in rows[0].iter(f'{{{W}}}t'))[:60] if rows else ''
                print(f'  [{i}] TBL    rows={len(rows)} :: {hdr}')


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    only = '--headings-only' in sys.argv
    for p in args:
        analyze(p, only)
