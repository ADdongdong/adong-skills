# -*- coding: utf-8 -*-
"""
修复 docx 中失效/悬空的图片关系（如 rId54 -> ../NULL），使 python-docx 可正常打开。

用法:
    python repair_broken_docx.py <input.docx> <output.docx> [--expect-body N] [--expect-tbl N]

安全原则（血泪教训）：
  1. 严禁跨元素正则删 drawing —— 非贪婪 .*? 会从第一个 <w:drawing> 一路吞到目标 rId
  2. rels 的 Target 相对 word/ 目录解析 —— 漏加前缀会把所有图片误判为悬空
"""
import io
import sys
import zipfile
import posixpath
import argparse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from lxml import etree

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
A_NS = 'http://schemas.openxmlformats.org/drawingml/2006/main'
V_NS = 'urn:schemas-microsoft-com:vml'


def find_bad_rids(z: zipfile.ZipFile):
    """找出失效的内部关系 id"""
    rels = etree.fromstring(z.read('word/_rels/document.xml.rels'))
    parts = set(z.namelist())
    bad = set()
    for rel in rels:
        rid = rel.get('Id')
        target = rel.get('Target') or ''
        if 'NULL' in target.upper():
            bad.add(rid)
            print(f'  [失效关系] {rid} -> {target}')
        elif rel.get('TargetMode') != 'External':
            # rels 位于 word/_rels/，Target 相对 word/ 解析
            norm = (target.lstrip('/') if target.startswith('/')
                    else posixpath.normpath(posixpath.join('word', target)))
            if norm and norm not in parts:
                bad.add(rid)
                print(f'  [悬空关系] {rid} -> {target} (部件不存在)')
    return bad


def drawing_hits_bad(drawing, bad_rids):
    """判断单个 drawing 是否引用了失效 rId"""
    for blip in drawing.iter(f'{{{A_NS}}}blip'):
        for attr in (f'{{{R}}}embed', f'{{{R}}}link'):
            if blip.get(attr) in bad_rids:
                return True
    for im in drawing.iter(f'{{{V_NS}}}imagedata'):
        for attr in (f'{{{R}}}id', f'{{{R}}}href'):
            if im.get(attr) in bad_rids:
                return True
    for ole in drawing.iter(f'{{{W}}}OLEObject'):
        if ole.get(f'{{{R}}}id') in bad_rids:
            return True
    return False


def repair(src, dst):
    with zipfile.ZipFile(src) as z:
        bad_rids = find_bad_rids(z)
        if not bad_rids:
            print('  未发现失效关系，仅复制')

        root = etree.fromstring(z.read('word/document.xml'))
        removed_d = removed_p = 0

        # 精确删除：逐个 drawing 判断，只删命中的那一个
        for drawing in list(root.iter(f'{{{W}}}drawing')):
            if not drawing_hits_bad(drawing, bad_rids):
                continue
            removed_d += 1
            parent = drawing.getparent()
            # 向上找承载它的 w:p
            holder = drawing
            while holder is not None and etree.QName(holder).localname not in ('p', 'tc'):
                holder = holder.getparent()
            if parent is not None:
                parent.remove(drawing)
            if holder is not None and etree.QName(holder).localname == 'p':
                has_run = holder.find(f'{{{W}}}r') is not None
                has_text = ''.join(t.text or '' for t in holder.iter(f'{{{W}}}t')).strip()
                if not has_run and not has_text and holder.getparent() is not None:
                    holder.getparent().remove(holder)
                    removed_p += 1

        print(f'  删除失效 drawing: {removed_d} 个，连带空段落: {removed_p} 个')

        new_doc = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)

        rels = etree.fromstring(z.read('word/_rels/document.xml.rels'))
        for rel in list(rels):
            if rel.get('Id') in bad_rids:
                rels.remove(rel)
        new_rels = etree.tostring(rels, xml_declaration=True, encoding='UTF-8', standalone=True)

        with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as out:
            for item in z.infolist():
                data = z.read(item.filename)
                if item.filename == 'word/document.xml':
                    data = new_doc
                elif item.filename == 'word/_rels/document.xml.rels':
                    data = new_rels
                out.writestr(item, data)


def verify(path, expect_body=None, expect_tbl=None):
    ok = True
    with zipfile.ZipFile(path) as z:
        root = etree.fromstring(z.read('word/document.xml'))
        body = root.find(f'{{{W}}}body')
        n = len(list(body))
        tbls = len(body.findall(f'{{{W}}}tbl'))
        imgs = len(list(root.iter(f'{{{A_NS}}}blip')))
        words = len(''.join(t.text or '' for t in root.iter(f'{{{W}}}t')))
    print(f'  body children = {n}   表格 = {tbls}   图片引用 = {imgs}   字数 = {words}')
    if expect_body is not None and n != expect_body:
        print(f'  ❌ body children 期望 {expect_body}'); ok = False
    if expect_tbl is not None and tbls != expect_tbl:
        print(f'  ❌ 表格数期望 {expect_tbl}'); ok = False
    try:
        from docx import Document
        d = Document(path)
        print(f'  ✅ python-docx 可打开，段落数 {len(d.paragraphs)}')
    except Exception as e:
        print(f'  ❌ python-docx 打开失败: {e}'); ok = False
    return ok


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('dst')
    ap.add_argument('--expect-body', type=int, default=None)
    ap.add_argument('--expect-tbl', type=int, default=None)
    a = ap.parse_args()
    print('=== 修复 ===')
    repair(a.src, a.dst)
    print('=== 校验 ===')
    sys.exit(0 if verify(a.dst, a.expect_body, a.expect_tbl) else 1)
