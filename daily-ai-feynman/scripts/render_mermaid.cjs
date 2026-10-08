// 用 Playwright 跑本地 mermaid 把 .mmd（Mermaid 声明式代码）渲染为高清 PNG。
//
// 渲染管线：Playwright 加载 mermaid.min.js → 浏览器内渲染矢量 SVG →
//           el.screenshot() 以高倍率（默认 deviceScaleFactor=4）截取位图。
//
// 为什么不用 @resvg/resvg-js 栅格化？
//   Mermaid 的 SVG 含复杂 CSS 类样式 + 中文 <text>/<tspan>，
//   resvg（WASM）对这类 SVG 的字体/CSS 支持不完整，会丢失文字。
//   浏览器截图虽然不是"纯矢量栅格化"，但 DSF=4 下 1200px 宽的输出
//   在手机/PC/放大查看时都足够锐利，且零兼容风险。
//
// 用法：
//   node scripts/render_mermaid.cjs <目录> [deviceScaleFactor，默认4]
// 递归渲染该目录下所有 *.mmd -> 同名 *.png（与 render_svg.cjs 同约定）。
// 主题配色对齐 daily-ai-feynman 的「清新蓝 #1c5fd9」。
const fs = require('fs');
const path = require('path');
const os = require('os');

// ---- playwright（装在托管 node workspace）----
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
    '  cd C:/Users/10355/.workbuddy/binaries/node/workspace && npm i playwright');
  process.exit(1);
}

const SKILL_ROOT = path.resolve(__dirname, '..');
const MERMAID_JS = path.join(SKILL_ROOT, 'assets', 'mermaid', 'mermaid.min.js');
if (!fs.existsSync(MERMAID_JS)) {
  console.error('找不到本地 mermaid 库：', MERMAID_JS, '\n请先下载 mermaid.min.js 到 assets/mermaid/');
  process.exit(1);
}
const MERMAID_URL = 'file:///' + MERMAID_JS.replace(/\\/g, '/');

const DSF = Number(process.argv[3]) || 4;

// 清新蓝主题（对齐 guizang Swiss #1c5fd9）
const THEME_VARS = {
  fontFamily: 'Microsoft YaHei, PingFang SC, sans-serif',
  background: '#ffffff',
  primaryColor: '#eaf1ff',
  primaryTextColor: '#1a2b4a',
  primaryBorderColor: '#1c5fd9',
  lineColor: '#1c5fd9',
  secondaryColor: '#f3f6fc',
  tertiaryColor: '#ffffff',
  clusterBkg: '#f3f6fc',
  clusterBorder: '#c9d8ff',
  edgeLabelBackground: '#ffffff',
  fontSize: '16px',
};

function buildHtml(code) {
  const tv = Object.entries(THEME_VARS)
    .map(([k, v]) => `${k}: '${v}'`).join(',\n    ');
  return `<!doctype html><html><head><meta charset="utf-8">
<style>
  html,body{margin:0;padding:0;background:#ffffff;}
  .wrap{display:inline-block;padding:24px;}
  .mermaid{font-family:'Microsoft YaHei',sans-serif;}
</style>
<script src="${MERMAID_URL}"></script>
</head><body>
<div class="wrap"><div class="mermaid">${code}</div></div>
<script>
  mermaid.initialize({ startOnLoad:false, theme:'base', securityLevel:'loose',
    themeVariables:{ ${tv} } });
  mermaid.run({ querySelector:'.mermaid' });
</script>
</body></html>`;
}

function walk(d) {
  let out = [];
  for (const e of fs.readdirSync(d, { withFileTypes: true })) {
    const p = path.join(d, e.name);
    if (e.isDirectory()) out = out.concat(walk(p));
    else if (e.name.toLowerCase().endsWith('.mmd')) out.push(p);
  }
  return out;
}

const dir = path.resolve(process.argv[2] || '.');
if (!fs.existsSync(dir)) { console.error('目录不存在：', dir); process.exit(1); }
const files = walk(dir).sort();
if (files.length === 0) { console.error('目录下没有 .mmd 文件'); process.exit(1); }

(async () => {
  const browser = await chromium.launch();
  let ok = 0;
  for (const f of files) {
    const code = fs.readFileSync(f, 'utf-8').trim();
    if (!code) { console.error('  ⚠️ 空文件，跳过：', f); continue; }
    const html = buildHtml(code);
    const tmp = path.join(os.tmpdir(), `mmd_${Date.now()}_${Math.random().toString(36).slice(2)}.html`);
    fs.writeFileSync(tmp, html, 'utf-8');
    const page = await browser.newPage({ deviceScaleFactor: DSF });
    await page.goto('file:///' + tmp.replace(/\\/g, '/'), { waitUntil: 'load' });
    try {
      await page.waitForSelector('.mermaid svg', { timeout: 15000 });
    } catch {
      console.error('  ⚠️ Mermaid 渲染超时/失败：', f);
      await page.close(); try { fs.unlinkSync(tmp); } catch {} continue;
    }
    // 等字体与布局稳定
    await page.evaluate(() => document.fonts && document.fonts.ready);
    await page.waitForTimeout(400);
    const el = await page.$('.wrap > .mermaid');
    const outPng = f.replace(/\.mmd$/i, '.png');
    await el.screenshot({ path: outPng });
    const box = await el.boundingBox();
    console.log(`  ✅ ${path.basename(outPng)}  ${Math.round((box?.width||0)*DSF)}x${Math.round((box?.height||0)*DSF)}  (DSF=${DSF})`);
    await page.close();
    try { fs.unlinkSync(tmp); } catch { /* 系统 temp，无害 */ }
    ok++;
  }
  await browser.close();
  if (!ok) { console.error('没有渲染出任何图'); process.exit(1); }
  console.log(`[Mermaid] 完成 ${ok} 张 -> ${dir}`);
})().catch(e => { console.error('渲染失败：', e.message); process.exit(1); });
