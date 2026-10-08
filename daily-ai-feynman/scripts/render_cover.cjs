// 用 Playwright 把封面 HTML 按节点 id 截图为 PNG（公众号 21:9 + 1:1 封面对）。
// 用法：
//   node scripts/render_cover.cjs <工作目录>
// 约定：<工作目录>/cover.html 内需含以下 id 的 section：
//   #wechat-21x9   -> 输出 <工作目录>/cover.png          （2100x900，用于草稿封面）
//   #wechat-1x1    -> 输出 <工作目录>/cover_square.png   （1080x1080）
//   #wechat-pair   -> 输出 <工作目录>/cover_preview.png  （可选，仅供人眼比对，不上传）
//
// 配图：模板用 CSS 变量 --art 指向 guizang 背景素材。
//   渲染前自动把 {{配图绝对路径}} 替换为 file:// 绝对路径。
//   默认素材：guizang-social-card-skill/assets/screenshot-backgrounds/style-b/ikb-dot-gradient.webp
//   切换素材：改 cover.html 里的 {{配图绝对路径}} 占位符指向其他 .webp 即可
const fs = require('fs');
const path = require('path');

// playwright 装在托管 node workspace，不在本 skill 的 node_modules，逐个候选路径解析。
const PW_CANDIDATES = [
  'playwright',
  'C:/Users/10355/.workbuddy/binaries/node/workspace/node_modules/playwright',
  path.join(process.env.APPDATA || '', 'npm/node_modules/playwright'),
];
let chromium = null;
for (const c of PW_CANDIDATES) {
  try { ({ chromium } = require(c)); break; } catch { /* 试下一个 */ }
}
if (!chromium) {
  console.error('找不到 playwright。请先安装：\n' +
    '  cd C:/Users/10355/.workbuddy/binaries/node/workspace && npm i playwright\n' +
    '  node node_modules/playwright/cli.js install chromium');
  process.exit(1);
}

// guizang 素材根目录（相对于本 skill 安装位置）
const SKILL_ROOT = path.resolve(__dirname, '..');
const GZ_ASSETS = path.join(
  SKILL_ROOT.replace(/daily-ai-feynman$/, 'guizang-social-card-skill'),
  'assets', 'screenshot-backgrounds'
);
// 默认素材
const DEFAULT_ART = path.join(GZ_ASSETS, 'style-b', 'ikb-dot-gradient.webp');

const dir = path.resolve(process.argv[2] || '.');
const htmlPath = path.join(dir, 'cover.html');
if (!fs.existsSync(htmlPath)) {
  console.error('找不到封面 HTML：', htmlPath);
  process.exit(1);
}

// [选择器, 输出文件名, 是否必需]
const TARGETS = [
  ['#wechat-21x9', 'cover.png', true],
  ['#wechat-1x1', 'cover_square.png', true],
  ['#wechat-pair', 'cover_preview.png', false],
];

(async () => {
  // 预处理：解析配图占位符 → 注入 file:// 绝对路径
  let html = fs.readFileSync(htmlPath, 'utf-8');
  const artPlaceholder = '{{配图绝对路径}}';
  if (html.includes(artPlaceholder)) {
    // 优先级：1) 同目录已有明确指定（非 art.png 的自定义文件）→ 用它
    //         2) 默认 guizang 素材 ikb-dot-gradient
    //         3) 兼容旧流程：同目录的 art.png / art.webp
    let artFile = null;
    // 检查是否有非默认的自定义配图（排除 art.png/art.webp 这些自动生成的）
    const customExts = ['png', 'jpg', 'jpeg', 'webp'];
    const autoNames = new Set(['art.png', 'art.jpg', 'art.jpeg', 'art.webp']);
    for (const ext of customExts) {
      const candidate = path.join(dir, `art.${ext}`);
      if (fs.existsSync(candidate) && !autoNames.has(`art.${ext}`)) {
        artFile = candidate; break;
      }
    }
    if (!artFile) {
      // 用默认 guizang 素材
      artFile = DEFAULT_ART;
    }
    if (!fs.existsSync(artFile)) {
      console.error(`⚠️ 配图文件不存在：${artFile}\n   请在 cover.html 中指定有效路径或放置 art.png`);
      process.exit(1);
    }
    const fileUrl = 'file:///' + artFile.replace(/\\/g, '/');
    html = html.replaceAll(artPlaceholder, fileUrl);
    console.log(`[封面] 配图：${path.basename(artFile)} (${Math.round(fs.statSync(artFile).size/1024)}KB)`);
    // 写回临时文件供 Playwright 加载（不覆盖原文件）
    fs.writeFileSync(path.join(dir, '_cover_render.html'), html, 'utf-8');
  }

  const loadPath = fs.existsSync(path.join(dir, '_cover_render.html'))
    ? path.join(dir, '_cover_render.html') : htmlPath;

  const browser = await chromium.launch();
  const page = await browser.newPage({ deviceScaleFactor: 1 });
  await page.goto('file:///' + loadPath.replace(/\\/g, '/'), { waitUntil: 'load' });
  // 等字体与图片就绪（含 WebGL/canvas 背景的绘制时间）
  await page.evaluate(() => document.fonts && document.fonts.ready);
  await page.waitForTimeout(900);

  let ok = 0;
  for (const [sel, out, required] of TARGETS) {
    const el = await page.$(sel);
    if (!el) {
      if (required) console.error(`  ⚠️ 缺少节点 ${sel}，跳过 ${out}`);
      continue;
    }
    const outPath = path.join(dir, out);
    await el.screenshot({ path: outPath });
    const box = await el.boundingBox();
    console.log(`  ✅ ${out}  ${Math.round(box.width)}x${Math.round(box.height)}`);
    ok++;
  }
  await browser.close();

  // 清理临时文件（直接 unlink，不经过 trash）
  const tmp = path.join(dir, '_cover_render.html');
  try { if (fs.existsSync(tmp)) fs.unlinkSync(tmp); } catch {}

  if (!ok) { console.error('没有渲染出任何封面，检查 cover.html 里的 section id'); process.exit(1); }
  console.log(`[封面] 完成 ${ok} 张 -> ${dir}`);
})().catch(e => { console.error('渲染失败：', e.message); process.exit(1); });
