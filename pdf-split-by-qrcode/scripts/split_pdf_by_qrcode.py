# -*- coding: utf-8 -*-
"""
按右上角二维码切分 PDF：每识别到一个二维码即开启一个新文档，
每个子文件以二维码内容命名。

用法:
    python split_pdf_by_qrcode.py <输入PDF> [输出目录]

依赖: PyMuPDF(fitz) / opencv-python / numpy / pyzbar / Pillow
"""
import os
import re
import sys
import json

import fitz
import cv2
import numpy as np
from PIL import Image
from pyzbar.pyzbar import decode

# 二维码所在区域（右上角），先裁此区域识别，失败再全页兜底
CROP_X0, CROP_Y0, CROP_X1, CROP_Y1 = 0.55, 0.0, 1.0, 0.25
ZOOM = 3  # 渲染缩放，越小越快；二维码较小时调大


def render_gray(page, zoom=ZOOM):
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    arr = np.array(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
    return cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)


def detect_qr(page):
    """返回该页识别到的二维码文本列表（去重）。"""
    gray = render_gray(page)
    h, w = gray.shape
    crop = gray[int(h * CROP_Y0):int(h * CROP_Y1), int(w * CROP_X0):int(w * CROP_X1)]

    texts = []
    # 引擎1：pyzbar（先裁区域，再全页兜底）
    for img in (crop, gray):
        try:
            for c in decode(img):
                if c.type == "QRCODE":
                    t = c.data.decode("utf-8", "ignore").strip()
                    if t:
                        texts.append(t)
        except Exception:
            pass
        if texts:
            break

    # 引擎2：OpenCV（仅在 pyzbar 没结果时兜底）
    if not texts:
        det = cv2.QRCodeDetector()
        for img in (crop, gray):
            try:
                r = det.detectAndDecode(img)
                t = (r[0] if isinstance(r, tuple) else r) or ""
                if t.strip():
                    texts.append(t.strip())
                    break
            except Exception:
                pass
    # 去重保序
    seen, out = set(), []
    for t in texts:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def safe_name(s):
    """把二维码内容转成合法文件名。"""
    return re.sub(r'[\\/:*?"<>|\r\n\t]', "_", s).strip() or "unnamed"


def split(pdf_path, out_dir=None):
    pdf_path = os.path.abspath(pdf_path)
    if out_dir is None:
        out_dir = os.path.join(os.path.dirname(pdf_path),
                               os.path.splitext(os.path.basename(pdf_path))[0] + "_拆分")
    os.makedirs(out_dir, exist_ok=True)

    doc = fitz.open(pdf_path)
    total = doc.page_count

    # 1) 扫描每页二维码
    marks = []          # [(page_index, qr_text)]
    for i in range(total):
        for t in detect_qr(doc[i]):
            marks.append((i, t))
        print(f"\r扫描中 {i + 1}/{total}", end="", flush=True)
    print()

    if not marks:
        print("未识别到任何二维码，终止。")
        return []

    # 2) 按二维码分组：[start, end)
    groups = []
    for k, (p, t) in enumerate(marks):
        end = marks[k + 1][0] if k + 1 < len(marks) else total
        groups.append((p, end, t))

    # 3) 同名加序号，避免覆盖
    name_count = {}
    for _, _, t in groups:
        n = safe_name(t)
        name_count[n] = name_count.get(n, 0) + 1
    used = {}

    # 4) 输出
    results = []
    for start, end, t in groups:
        n = safe_name(t)
        if name_count[n] > 1:
            used[n] = used.get(n, 0) + 1
            fname = f"{n}_{used[n]:02d}.pdf"
        else:
            fname = f"{n}.pdf"
        out_path = os.path.join(out_dir, fname)
        new = fitz.open()
        new.insert_pdf(doc, from_page=start, to_page=end - 1)
        new.save(out_path, garbage=4, deflate=True)
        new.close()
        results.append({"file": fname, "qr": t, "pages": f"{start + 1}-{end}",
                        "page_count": end - start})
        print(f"  页码 {start + 1:>3}-{end:<3} ({end - start}页) -> {fname}")

    doc.close()

    # 索引清单
    idx = os.path.join(out_dir, "_拆分清单.json")
    with open(idx, "w", encoding="utf-8") as f:
        json.dump({"source": pdf_path, "total_pages": total, "files": results},
                  f, ensure_ascii=False, indent=2)

    print(f"\n共 {len(results)} 个文件，输出目录：{out_dir}")
    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    split(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
