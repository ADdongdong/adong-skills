#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
apply_heading_style.py — 把公众号文章的章节标题套用「期刊式」版式

用法：
    python3 apply_heading_style.py <post.md>            # 原地改写
    python3 apply_heading_style.py <post.md> --out x.md # 输出到新文件
    python3 apply_heading_style.py <post.md> --dry-run  # 只报告会改什么

做四件事（全部只改样式，不改文字）：
  1. `【一、标题】` → PART 编号 + 中文标题 + 蓝色短线（单行 HTML，保证渲染服务透传）
  2. `**小白**：` / `**哈哈栋**：` → 蓝色加粗 span
  3. `**第一问：…**` 后面紧跟正文 → 提成独立小节标题（蓝方块 + 17px 黑粗）
  4. 章节标题前多余的 `---` 分隔线删掉（标题自带分隔，避免重复）

注意（硬约束）：
  - publish_draft.cjs 会剥离所有 background*，所以模板**不能用背景色块**，
    只能用 color / font-size / font-weight / border / letter-spacing。
  - 标题必须是**单行** HTML；多行会被 markdown 解析器插入 <p> 而错位。
  - 脚本幂等：已转换过的章节标题（含 `margin:48px 0 22px`）不会被重复处理。
"""

import argparse
import io
import re
import sys

ACCENT = "#1c5fd9"      # 与封面/插图统一的主色
INK = "#111418"
MUTED = "#9aa4b2"

CN_NUM = {
    "一": "01", "二": "02", "三": "03", "四": "04", "五": "05",
    "六": "06", "七": "07", "八": "08", "九": "09", "十": "10",
}


def heading_block(part: str, title: str) -> str:
    """期刊式章节标题：PART 编号 + 中文标题 + 蓝色短线（单行 HTML）"""
    return (
        '<section style="margin:48px 0 22px">'
        f'<section style="font-size:12px;color:{ACCENT};font-weight:700;letter-spacing:3px">PART {part}</section>'
        f'<section style="font-size:21px;font-weight:800;color:{INK};margin-top:8px;line-height:1.45;letter-spacing:0.3px">{title}</section>'
        f'<section style="border-top:3px solid {ACCENT};width:88px;margin-top:16px"></section>'
        '</section>'
    )


def sub_heading(text: str) -> str:
    """小节标题（第一问 / 第二问 …）：蓝色方块 + 黑粗"""
    body = text.strip().rstrip("*").strip()
    return (
        f'<section style="margin:26px 0 8px;font-size:17px;font-weight:800;color:{INK};line-height:1.5">'
        f'<span style="color:{ACCENT}">■</span>　{body}</section>'
    )


def convert(md: str, verbose: bool = True) -> str:
    stats = {"headings": 0, "speakers": 0, "subheads": 0, "hr": 0}

    # 1) 章节标题【一、xxx】→ 期刊式标题
    def _h(m):
        num, title = m.group(1), m.group(2).strip()
        part = CN_NUM.get(num)
        if not part:
            return m.group(0)
        stats["headings"] += 1
        return heading_block(part, title)

    md = re.sub(r"^【([一二三四五六七八九十])、(.*?)】\s*$", _h, md, flags=re.M)

    # 2) 说话人名字 → 主色加粗（只改样式）
    for name in ("小白", "哈哈栋"):
        before = md.count(f"**{name}**：")
        md = md.replace(f"**{name}**：",
                        f'<span style="color:{ACCENT};font-weight:700">{name}</span>：')
        stats["speakers"] += before

    # 3) 「第一问：…」类小节标题：提成独立标题块
    def _sub(m):
        title, body = m.group(1).strip(), m.group(2).strip()
        stats["subheads"] += 1
        return f"{sub_heading(title)}\n\n{body}"

    md = re.sub(r"^\*\*((?:第[一二三四五六七八九十]+问|[0-9]+[、.])\s*[^*\n]{2,40}?)\*\*\s*\n(\S[^\n]*)",
                _sub, md, flags=re.M)

    # 4) 章节标题前多余的 --- 分隔线
    def _hr(m):
        stats["hr"] += 1
        return '\n<section style="margin:48px 0 22px">'

    md = re.sub(r"^---\s*\n+<section style=\"margin:48px 0 22px\">", _hr, md, flags=re.M)

    # 5) 文末「资料来源」注 → 浅灰小字
    def _src(m):
        stats["source"] = stats.get("source", 0) + 1
        return (f'<span style="font-size:13px;color:{MUTED};line-height:1.7">'
                f'资料来源：{m.group(1).strip()}</span>')

    md = re.sub(r"^\*资料来源：(.*?)\*\s*$", _src, md, flags=re.M)

    if verbose:
        print(f"[heading] 章节标题转换 {stats['headings']} 处")
        print(f"[speaker] 说话人样式转换 {stats['speakers']} 处")
        print(f"[subhead] 小节标题转换 {stats['subheads']} 处")
        print(f"[hr] 移除冗余分隔线 {stats['hr']} 处")
        print(f"[source] 资料来源小字 {stats.get('source', 0)} 处")
    return md


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--out", help="输出文件（默认原地改写）")
    ap.add_argument("--dry-run", action="store_true", help="只预览，不写文件")
    args = ap.parse_args()

    md = io.open(args.file, encoding="utf-8").read()
    out = convert(md)

    if args.dry_run:
        print("--- dry-run，未写入 ---")
        return
    target = args.out or args.file
    io.open(target, "w", encoding="utf-8").write(out)
    print(f"已写入：{target}")


if __name__ == "__main__":
    sys.exit(main())
