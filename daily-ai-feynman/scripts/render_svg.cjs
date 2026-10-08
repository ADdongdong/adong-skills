// 用 @resvg/resvg-js（纯 WASM）把 SVG 渲染为 2x 高清 PNG，不走浏览器。
// 用法：
//   NODE_PATH=C:/Users/10355/.workbuddy/binaries/node/workspace/node_modules node render_svg.cjs <目录>
// 会渲染该目录下所有 *.svg -> 同名 *.png（中文已绑定系统字体，不乱码）。
const fs = require('fs');
const path = require('path');

// 自动兜底：@resvg/resvg-js 装在托管 node workspace 里，不在本 skill 的 node_modules。
// 无需再手动设 NODE_PATH，这里逐个候选路径解析。
const RESVG_CANDIDATES = [
  '@resvg/resvg-js',
  'C:/Users/10355/.workbuddy/binaries/node/workspace/node_modules/@resvg/resvg-js',
  path.join(process.env.APPDATA || '', 'npm/node_modules/@resvg/resvg-js'),
];
let Resvg = null;
for (const c of RESVG_CANDIDATES) {
  try { ({ Resvg } = require(c)); break; } catch { /* 继续尝试下一个 */ }
}
if (!Resvg) {
  console.error('找不到 @resvg/resvg-js。请先安装：\n' +
    '  cd C:/Users/10355/.workbuddy/binaries/node/workspace && npm i @resvg/resvg-js');
  process.exit(1);
}

const dir = process.argv[2] || '.';
if (!fs.existsSync(dir)) {
  console.error('目录不存在：', dir);
  process.exit(1);
}

// 显式加载系统中文字体，确保中文不乱码
const fontCandidates = [
  'C:/Windows/Fonts/msyh.ttc',
  'C:/Windows/Fonts/msyhbd.ttc',
  'C:/Windows/Fonts/simhei.ttf',
  'C:/Windows/Fonts/simkai.ttf',
  'C:/Windows/Fonts/STKAITI.TTF',
];
const fontFiles = fontCandidates.filter(f => fs.existsSync(f));
console.log('loaded fonts:', fontFiles);

function walk(d, base) {
  let out = [];
  for (const e of fs.readdirSync(d, { withFileTypes: true })) {
    const p = path.join(d, e.name);
    const rel = path.join(base, e.name);
    if (e.isDirectory()) out = out.concat(walk(p, rel));
    else if (e.name.toLowerCase().endsWith('.svg')) out.push(rel);
  }
  return out;
}
const files = walk(dir, '').filter(f => f.toLowerCase().endsWith('.svg')).sort();
if (files.length === 0) {
  console.error('目录下没有 .svg 文件');
  process.exit(1);
}

for (const f of files) {
  const svg = fs.readFileSync(path.join(dir, f), 'utf-8');
  const resvg = new Resvg(svg, {
    fitTo: { mode: 'zoom', value: 2 },
    font: { fontFiles, loadSystemFonts: true, defaultFontFamily: 'Microsoft YaHei' },
    background: '#ffffff',
  });
  const png = resvg.render();
  const out = path.join(dir, f.replace(/\.svg$/i, '.png'));
  fs.writeFileSync(out, png.asPng());
  console.log('rendered', out, png.width + 'x' + png.height);
}
