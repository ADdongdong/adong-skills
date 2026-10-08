# -*- coding: utf-8 -*-
"""把**过高的图**拆成上下两张，好塞进 A4 正文区（v1.2 附带的工具）。

用法：
    python split_image_for_docx.py <图.png> [--out <目录>] [--ratio 2.2] [--near 0.5]

## 为什么需要它

Word 正文区宽 15cm、单页可用高约 24.6cm。规范里给图定的上限是"宽 ≤15cm 且高 ≤20.5cm，
取更严的一个"—— 于是**宽高比差于 1:2.2 的图**会被按高度反算宽度，铺出来又窄又矮：

| 图宽高比 | 按规范铺出来的尺寸 | 16px 的图源字号变成 |
|---|---|---|
| 1:2.35（实测的纵向流程图） | 8.7cm × 20.5cm | **≈4.7pt —— 读不出** |
| 拆成上下两张（每张 1:1.18） | 15cm × 17.6cm | **≈8.2pt —— 可读** |

所以：**比 1:2.2 更瘦长的图，进 Word 前先拆**。裁切线选**最靠近中部的整行空白**
（不切进方框里），拆完两张都会再裁掉各自的白边。

对应规范：`references/03-样式与编号规范.md` 第 6.2 节。
"""
import argparse
import os
import sys

from PIL import Image, ImageChops

try:                                   # Windows 控制台默认 GBK，中文/符号会直接抛
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

BORDER_RATIO = 0.25    # 一行里非白像素超过宽度的这个比例 → 认为是某个方框的横边框
GAP_INK_MAX = 10       # 一行里非白像素少于此值 → 认为是"基本空白"
GAP_RUN_MIN = 4        # 连续多少行基本空白才算一条可切的空白带
BORDER_AVOID = 8       # 离横边框这么近的行不作为切线（怕切到框线）


def ink_profile(img):
    """每行的非白像素个数（用直方图统计，比逐像素快得多）。"""
    g = img.convert('L')
    w, h = g.size
    prof = []
    for y in range(h):
        hist = g.crop((0, y, w, y + 1)).histogram()
        prof.append(w - sum(hist[250:]))
    return prof, w, h


def pick_cut(prof, w, h, near=0.5, mermaid=True):
    """选**最靠近 `near` 位置**的可切空白带中心；找不到返回 None。

    **为什么不能用"整行纯白"当判据**：纵向流程图里每一行都可能有**竖线箭头**穿过
    （一条 1~2px 的线），一行的非白像素只有 2 个也算不上"纯白" → 整张图找不出一条
    「全白行」，判据直接失效。改用**每行的墨量轮廓**：
    · **横边框行**（墨量 > 宽度×25%）是方框的上下边 —— 切线要**避开**它们；
    · 在**基本空白**（墨量 ≤10）且**离横边框 ≥8px** 的行里找连续带，取最近目标位置的那条。
    切线可能正好穿过一根竖向箭头（拆图后表现为上下各留一小截箭头），这是可接受的。
    """
    target = h * near
    border = [i for i, v in enumerate(prof) if v >= BORDER_RATIO * w]
    runs, start = [], None
    for y in range(h):
        ok = prof[y] <= GAP_INK_MAX and all(abs(y - b) >= BORDER_AVOID for b in border)
        if ok and start is None:
            start = y
        elif not ok and start is not None:
            if y - start >= GAP_RUN_MIN:
                runs.append((start, y))
            start = None
    if start is not None and h - start >= GAP_RUN_MIN:
        runs.append((start, h))
    if not runs:
        return None
    best = min(runs, key=lambda r: abs((r[0] + r[1]) / 2 - target))
    return (best[0] + best[1]) // 2


def trim(img):
    """裁掉四周白边（与 mermaid skill 同一套做法：ImageChops 差值 + getbbox）。"""
    rgb = img.convert('RGB')
    bg = Image.new('RGB', rgb.size, (255, 255, 255))
    box = ImageChops.difference(rgb, bg).getbbox()
    return rgb.crop(box) if box else rgb


def split(path, out_dir=None, ratio=2.2, near=0.5):
    img = Image.open(path).convert('RGB')
    w, h = img.size
    print('  原图 %dx%d  宽高比 1:%.2f' % (w, h, h / w))
    if h / w <= ratio:
        print('  未超过 1:%.2f，不需要拆' % ratio)
        return []
    prof, pw, ph = ink_profile(img)
    cut = pick_cut(prof, pw, ph, near)
    if cut is None or cut < h * 0.15 or cut > h * 0.85:
        print('  [!] 找不到合适的空白带（图太密），未拆；建议改图源（缩小字号/拉宽）或手工切')
        return []
    base = os.path.splitext(os.path.basename(path))[0]
    out_dir = out_dir or os.path.dirname(os.path.abspath(path))
    res = []
    for tag, box in (('top', (0, 0, w, cut)), ('bottom', (0, cut, w, h))):
        part = trim(img.crop(box))
        p = os.path.join(out_dir, '%s_%s.png' % (base, tag))
        part.save(p)
        res.append((p, part.size))
    for p, size in res:
        print('  -> %s  %dx%d  宽高比 1:%.2f' % (os.path.basename(p), size[0], size[1], size[1] / size[0]))
    print('  切线 y=%d（原图高 %d，%.0f%% 处）' % (cut, h, 100.0 * cut / h))
    return res


def main():
    ap = argparse.ArgumentParser(description='把过高的图拆成上下两张（按页高适配 Word 正文区）')
    ap.add_argument('image')
    ap.add_argument('--out', default=None, help='输出目录（默认与输入同目录）')
    ap.add_argument('--ratio', type=float, default=2.2, help='宽高比超过 1:N 才拆（默认 2.2）')
    ap.add_argument('--near', type=float, default=0.5, help='在图的百分之几处切（默认 0.5）')
    a = ap.parse_args()
    print('拆图:', a.image)
    res = split(a.image, a.out, a.ratio, a.near)
    print('DONE' + ('' if res else '（未拆）'))
    return 0 if res else 0


if __name__ == '__main__':
    sys.exit(main())
