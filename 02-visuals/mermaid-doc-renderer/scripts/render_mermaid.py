# -*- coding: utf-8 -*-
"""Mermaid → 图片/矢量 通用渲染器（mermaid-doc-renderer skill）

支持输出格式：png / svg / webp / jpg / pdf
支持分辨率：--scale 倍率，或 --width 目标像素宽度

渲染管线（完全离线，验证可靠）：
  1. headless Chromium 加载 HTML（内嵌本地 mermaid.min.js），
     mermaid 渲染完成后在 document.title 写入状态标记：
       MMD_READY = 成功    MMD_ERROR:<消息> = mermaid 语法错误
  2. 第一遍 --dump-dom 读回 DOM：校验渲染状态；SVG 格式直接提取 <svg> 矢量源码
  3. 位图格式（PNG/WebP/JPG/PDF）：第二遍 --screenshot 截取高清位图（DSF 缩放），
     PIL 快速裁剪白边，再按需转格式

健壮性设计：
  - 渲染失败（语法错误/空白图）会明确报错并跳过该块，不再静默输出坏图
  - 临时 HTML 写入系统临时目录（tempfile），互不冲突，用后即删
  - 白边裁剪用 PIL ImageChops.getbbox()，大图也是毫秒级

为什么不用 cairosvg 转 SVG？
  mermaid 生成的 SVG 含复杂 CSS/foreignObject，cairosvg 解析常报 mismatched tag，
  且中文字体支持差。截图方式（DSF>=2）零兼容风险，足够高清。

用法：
  python render_mermaid.py <md_path> --out <dir> --format png --scale 2
  python render_mermaid.py <md_path> --out <dir> --format svg
  python render_mermaid.py <md_path> --out <dir> --format png --width 1200
  # 单条 mermaid 字符串（不读 md）
  python render_mermaid.py --code "graph LR; A-->B" --out <dir> --format svg
  # 自定义 mermaid.js / Chromium 路径
  python render_mermaid.py <md> --out <dir> --mermaid-js <path> --shell <path>

依赖：
  - Python：Pillow（无 cairosvg 需求）
  - headless Chromium（自动探测 Playwright 的 chromium_headless_shell 或系统 Chrome）
  - mermaid.min.js v10+（离线，本 skill 自带 assets/mermaid.min.js）
"""
import os, sys, re, subprocess, argparse, glob, json, tempfile, shutil

# ====== 自动探测环境常量 ======
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def find_mermaid_js():
    """优先 skill 自带的离线库；找不到时给出可操作的提示"""
    bundled = os.path.join(SKILL_DIR, 'assets', 'mermaid.min.js')
    if os.path.exists(bundled):
        return bundled
    return None


def find_headless_shell():
    """跨平台探测 headless 浏览器：
    1) Playwright 安装的 chromium_headless_shell（任意版本号）
    2) Playwright 的 chromium 完整版 chrome
    3) 系统已装的 Chrome / Edge
    """
    home = os.path.expanduser('~')
    local = os.environ.get('LOCALAPPDATA') or os.path.join(home, 'AppData', 'Local')
    candidates = []

    pw_dirs = [os.path.join(local, 'ms-playwright'),
               os.path.join(home, '.cache', 'ms-playwright')]
    for root in pw_dirs:
        if not os.path.isdir(root):
            continue
        for sub in sorted(glob.glob(os.path.join(root, 'chromium*')), reverse=True):
            for exe in (('chrome-win', 'headless_shell.exe'),
                        ('chrome-win', 'chrome.exe'),
                        ('chrome-win64', 'headless_shell.exe'),
                        ('chrome-win64', 'chrome.exe'),
                        ('chrome-linux', 'headless_shell'),
                        ('chrome-linux', 'chrome'),
                        ('chrome-mac', 'Chromium.app', 'Contents', 'MacOS', 'Chromium')):
                p = os.path.join(sub, *exe)
                if os.path.exists(p):
                    candidates.append(p)

    import platform
    if platform.system() == 'Windows':
        pf = os.environ.get('ProgramFiles', r'C:\Program Files')
        pf86 = os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)')
        for base in (pf, pf86):
            for rel in (r'Google\Chrome\Application\chrome.exe',
                        r'Microsoft\Edge\Application\msedge.exe'):
                candidates.append(os.path.join(base, rel))
    elif platform.system() == 'Darwin':
        candidates += ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome']
    else:
        candidates += ['/usr/bin/google-chrome', '/usr/bin/chromium-browser',
                       '/usr/bin/chromium']

    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None


MERMAID_JS = os.environ.get('MERMAID_JS') or find_mermaid_js()
SHELL = os.environ.get('HEADLESS_SHELL') or find_headless_shell()
DEFAULT_OUT = os.path.join(os.getcwd(), 'render_out')


def extract_mermaid_blocks(md_text):
    blocks = []
    lines = md_text.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith('```mermaid'):
            buf = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                buf.append(lines[i])
                i += 1
            blocks.append('\n'.join(buf))
            i += 1
        else:
            i += 1
    return blocks


def make_html(mermaid_code, mermaid_js_path):
    """生成渲染页：成功写 title=MMD_READY，失败写 title=MMD_ERROR 并把错误显示在页面里"""
    mermaid_js_url = 'file:///' + mermaid_js_path.replace('\\', '/')
    code_json = json.dumps(mermaid_code)
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<script src="{mermaid_js_url}"></script>
<style>
  html,body {{ margin:0; padding:0; background:#fff; }}
  .mermaid {{ padding:16px; font-size:16px; }}
</style>
</head><body>
<div class="mermaid" id="mm"></div>
<script>
  var code = {code_json};
  document.getElementById('mm').textContent = code;
    try {{
    mermaid.initialize({{ startOnLoad:false, theme:'default', securityLevel:'loose',
                          suppressErrorRendering:true }});
    mermaid.run({{ querySelector:'#mm' }}).then(function(){{
      document.title = 'MMD_READY';
    }}).catch(function(e){{
      document.title = 'MMD_ERROR';
      document.getElementById('mm').textContent = String(e && e.message || e);
      document.getElementById('mm').style.color = '#c00';
    }});
  }} catch(e) {{
    document.title = 'MMD_ERROR';
    document.getElementById('mm').textContent = String(e && e.message || e);
  }}
</script>
</body></html>"""


def run_chromium(html_path, extra_args):
    cmd = [SHELL,
           '--headless', '--disable-gpu', '--no-sandbox',
           '--hide-scrollbars', '--force-device-scale-factor=1',
           '--window-size=1800,1400', '--virtual-time-budget=10000',
           ] + extra_args + ['file:///' + html_path.replace('\\', '/')]
    return subprocess.run(cmd, capture_output=True, timeout=90)


def check_status_and_svg(dom):
    """从 DOM 的 <title> 实际运行时值判断渲染状态（注意：dump-dom 会包含
    内联 script 源码，裸搜 'MMD_READY' 会误命中 JS 字面量，必须用 <title> 标签）"""
    m_title = re.search(r'<title[^>]*>([^<]*)</title>', dom)
    title = (m_title.group(1) if m_title else '').strip()
    if title == 'MMD_READY':
        # 兜底：旧版 mermaid 不支持 suppressErrorRendering，会把错误画成横幅图
        if re.search(r'[Ss]yntax\s+error', dom):
            status, err = 'error', 'mermaid 语法/运行错误: Syntax error（渲染出错误横幅图）'
        else:
            status, err = 'ok', ''
    elif title == 'MMD_ERROR':
        m = re.search(r'<div class="mermaid"[^>]*>([\s\S]*?)</div>', dom)
        err = html_unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip()[:200] if m else '未知错误'
        status, err = 'error', f'mermaid 语法/运行错误: {err}'
    else:
        status, err = 'timeout', '渲染超时或未产生结果（可尝试增大 --virtual-time-budget）'
    svg = None
    if status == 'ok':
        start = dom.find('<svg')
        end = dom.rfind('</svg>') if start != -1 else -1
        if start != -1 and end != -1:
            svg = dom[start:end + len('</svg>')]
    return status, err, svg


def html_unescape(s):
    for a, b in (('&lt;', '<'), ('&gt;', '>'), ('&amp;', '&'), ('&quot;', '"'), ('&#39;', "'")):
        s = s.replace(a, b)
    return s


def trim_whitespace(path):
    """快速裁掉四周白边：ImageChops 差值 + getbbox（毫秒级，替代逐像素扫描）"""
    from PIL import Image, ImageChops
    img = Image.open(path).convert('RGB')
    bg = Image.new('RGB', img.size, (255, 255, 255))
    diff = ImageChops.difference(img, bg).convert('L')
    # 容忍接近白的抗锯齿像素（亮度差 <=8 视为背景）
    diff = diff.point(lambda x: 0 if x <= 8 else x)
    bbox = diff.getbbox()
    if bbox and (bbox[2] - bbox[0] > 4) and (bbox[3] - bbox[1] > 4):
        img.crop(bbox).save(path)
        return Image.open(path).size
    return img.size


def is_blank_png(path):
    """内容几乎全白 → 判定渲染失败兜底检查"""
    from PIL import Image, ImageChops
    img = Image.open(path).convert('L')
    bg = Image.new('L', img.size, 255)
    return ImageChops.difference(img, bg).getbbox() is None


def convert_png_to(out_path, fmt, width=None):
    """从 PNG 转换 webp/jpg/pdf（PIL 支持）"""
    from PIL import Image
    img = Image.open(out_path)
    if width:
        h = int(img.height * width / img.width)
        img = img.resize((width, h), Image.LANCZOS)
    base = os.path.splitext(out_path)[0]
    target = base + '.' + fmt
    if fmt in ('webp', 'jpg', 'jpeg'):
        img.save(target, format='WEBP' if fmt == 'webp' else 'JPEG')
    elif fmt == 'pdf':
        img.convert('RGB').save(target, format='PDF')
    return target


def render_one(mermaid_code, idx, out_dir, fmt='png', scale=2, width=None, trim=True,
               virtual_time_budget=10000):
    os.makedirs(out_dir, exist_ok=True)

    # ---- 临时 HTML：系统临时目录、唯一文件名、用后即删（避免并行冲突和残留）----
    tmp_dir = tempfile.mkdtemp(prefix='mmdr_')
    html_path = os.path.join(tmp_dir, 'render.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(make_html(mermaid_code, MERMAID_JS))

    def _cleanup():
        shutil.rmtree(tmp_dir, ignore_errors=True)

    try:
        global VIRTUAL_TIME_BUDGET
        budget_ms = virtual_time_budget or VIRTUAL_TIME_BUDGET

        # ---- 第一遍：dump-dom 校验渲染状态（SVG 在此一并提取）----
        try:
            r = run_chromium(html_path, [
                f'--virtual-time-budget={budget_ms}', '--dump-dom'])
            dom = r.stdout.decode('utf-8', errors='replace')
        except Exception as e:
            print(f'  [{idx}] 渲染失败: {e}')
            return None
        status, err, svg = check_status_and_svg(dom)
        if status == 'error':
            print(f'  [{idx}] {err}')
            return None
        if status == 'timeout':
            print(f'  [{idx}] {err}')
            return None

        name_base = f'mermaid_{idx}'

        if fmt == 'svg':
            if not svg:
                print(f'  [{idx}] DOM 中未找到 SVG 矢量源码')
                return None
            final = os.path.join(out_dir, name_base + '.svg')
            with open(final, 'w', encoding='utf-8') as f:
                f.write(svg)
            print(f'  [{idx}] -> {name_base}.svg size=vector')
            return final

        # ---- 第二遍：高清位图截图（DSF 缩放，放大窗口确保图不被截断）----
        png_path = os.path.join(tmp_dir, name_base + '.png')
        try:
            run_chromium(html_path, [
                f'--virtual-time-budget={budget_ms}',
                f'--force-device-scale-factor={scale}',
                f'--screenshot={png_path}'])
        except Exception as e:
            print(f'  [{idx}] 截图失败: {e}')
            return None
        if not os.path.exists(png_path) or os.path.getsize(png_path) == 0:
            print(f'  [{idx}] 截图未产出文件')
            return None
        if trim:
            size = trim_whitespace(png_path)
            if size[0] <= 6 or size[1] <= 6:
                print(f'  [{idx}] 渲染内容为空（疑似语法问题被 mermaid 兜底绘制为空白）')
                return None

        ext = {'jpeg': 'jpg'}.get(fmt, fmt)
        target = png_path
        if fmt != 'png':
            target = convert_png_to(png_path, fmt, width=None)
        final = os.path.join(out_dir, name_base + '.' + ext)
        shutil.move(target, final)

        from PIL import Image
        try:
            sz = Image.open(final).size
        except Exception:
            sz = 'ok'
        if width:
            from PIL import Image as I2
            img = I2.open(final)
            h = int(img.height * width / img.width)
            img = img.resize((width, h), I2.LANCZOS)
            img.save(final)
            sz = (width, h)
        print(f'  [{idx}] -> {os.path.basename(final)} size={sz}')
        return final
    finally:
        _cleanup()


VIRTUAL_TIME_BUDGET = 10000


def main():
    ap = argparse.ArgumentParser(description='Mermaid → 图片/矢量 渲染器')
    ap.add_argument('md_path', nargs='?', help='markdown 文件路径（含 mermaid 块）')
    ap.add_argument('--code', help='直接渲染这段 mermaid 源码（优先级最高）')
    ap.add_argument('--out', default=DEFAULT_OUT, help='输出目录')
    ap.add_argument('--format', default='png', choices=['png', 'svg', 'webp', 'pdf', 'jpg'],
                    help='输出格式')
    ap.add_argument('--scale', type=float, default=2, help='分辨率倍率（默认2）')
    ap.add_argument('--width', type=int, default=None, help='目标像素宽度（指定后 scale 失效）')
    ap.add_argument('--no-trim', action='store_true', help='不裁剪白边')
    ap.add_argument('--virtual-time-budget', type=int, default=None,
                    help='headless 渲染等待毫秒数（默认10000，复杂图可增大）')
    ap.add_argument('--mermaid-js', default=None, help='自定义 mermaid.min.js 路径')
    ap.add_argument('--shell', default=None, help='自定义 headless Chromium 路径')
    args = ap.parse_args()

    global MERMAID_JS, SHELL, VIRTUAL_TIME_BUDGET
    if args.mermaid_js:
        MERMAID_JS = args.mermaid_js
    if args.shell:
        SHELL = args.shell
    if args.virtual_time_budget:
        VIRTUAL_TIME_BUDGET = args.virtual_time_budget

    problems = []
    if not MERMAID_JS or not os.path.exists(MERMAID_JS):
        problems.append(
            f'找不到 mermaid.min.js\n'
            f'  预期位置: {SKILL_DIR}\\assets\\mermaid.min.js\n'
            f'  可从 https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js 下载放入 assets/，'
            f'或用 --mermaid-js 指定路径')
    if not SHELL or not os.path.exists(SHELL):
        problems.append(
            f'找不到 headless Chromium\n'
            f'  已依次探测: Playwright 缓存目录、系统 Chrome / Edge\n'
            f'  可执行 `pip install playwright && playwright install chromium` 后重试，'
            f'或用 --shell 指定浏览器路径')
    if problems:
        print('\n'.join(problems))
        sys.exit(1)

    out_dir = args.out

    if args.code:
        render_one(args.code, 'single', out_dir, fmt=args.format, scale=args.scale,
                   width=args.width, trim=not args.no_trim,
                   virtual_time_budget=args.virtual_time_budget)
        print('DONE')
        return

    if not args.md_path:
        print('需提供 md_path 或 --code')
        sys.exit(1)
    with open(args.md_path, encoding='utf-8') as f:
        md = f.read()
    blocks = extract_mermaid_blocks(md)
    print(f'找到 {len(blocks)} 个 mermaid 块')
    fail = 0
    for i, b in enumerate(blocks):
        print(f'== 块 {i}: {b.splitlines()[0][:40]}')
        res = render_one(b, i, out_dir, fmt=args.format, scale=args.scale,
                         width=args.width, trim=not args.no_trim,
                         virtual_time_budget=args.virtual_time_budget)
        if not res:
            fail += 1
    print('DONE', f'(失败 {fail}/{len(blocks)})' if fail else '')
    sys.exit(1 if fail else 0)


if __name__ == '__main__':
    main()
