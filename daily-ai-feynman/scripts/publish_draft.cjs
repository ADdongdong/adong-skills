/**
 * publish_draft.cjs - 渲染 Markdown 并推送至微信公众号草稿箱（增强版）
 *
 * 相比 md-to-wechat 的 publish.cjs，本脚本额外支持：
 *   - 正文本地图片（相对 / 绝对路径）自动上传微信 CDN 并替换 URL
 *   - 封面图支持本地路径（--cover 或 MD 第一张图）
 *
 * 依赖：Node.js 18+（内置 fetch / FormData / Blob），零额外 npm 依赖（除读取 .env）。
 * 配置：本 skill 目录的 .env（从 md-to-wechat 复制：ACCOUNT/THEME_ID/WECHAT_APP_ID/WECHAT_APP_SECRET/API_URL）
 *
 * 用法：
 *   首次（确认 IP 白名单）： node publish_draft.cjs --file <md>
 *   正式推送：             node publish_draft.cjs --file <md> --confirmed [--title ..] [--author ..] [--cover ..]
 */
'use strict';

const fs = require('fs');
const path = require('path');

// ── 读取 .env（本 skill 目录）──────────────────────────────────────────────
const envPath = path.join(__dirname, '..', '.env');
if (fs.existsSync(envPath)) {
  fs.readFileSync(envPath, 'utf-8').split('\n').forEach(line => {
    const m = line.match(/^\s*([^#=\s][^=]*?)\s*=\s*(.*?)\s*$/);
    if (m) process.env[m[1]] = m[2];
  });
}

// ── 常量 ───────────────────────────────────────────────────────────────────
const FALLBACK_COVER = 'https://zaowu-pic.maolai.cc/uploads/1774501229309-Image_55.jpg';
const WECHAT_API = 'https://api.weixin.qq.com/cgi-bin';
const CACHE_PATH = path.join(__dirname, '..', '.cache.json');
const WX_DOMAINS = ['mmbiz.qpic.cn', 'mmbiz.qlogo.cn', 'res.wx.qq.com'];

// ── 解析参数 ───────────────────────────────────────────────────────────────
function parseArgs(argv) {
  const args = { confirmed: false };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--file') args.file = argv[++i];
    else if (argv[i] === '--title') args.title = argv[++i];
    else if (argv[i] === '--author') args.author = argv[++i];
    else if (argv[i] === '--cover') args.cover = argv[++i];
    else if (argv[i] === '--confirmed') args.confirmed = true;
    else if (argv[i] === '--keep-bg') args.keepBg = true;       // 保留主题背景色（默认剥掉）
    else if (argv[i] === '--keep-h1') args.keepH1 = true;       // 保留正文顶部大标题（默认删掉）
  }
  return args;
}

// ── 排版净化 ───────────────────────────────────────────────────────────────
/**
 * 剥掉渲染主题带来的所有背景色（黄底/米底/色块），只留白底。
 * 处理：inline style 里的 background / background-color / background-image，
 *       以及 HTML 的 bgcolor 属性。边框、字色、左边线一律保留。
 */
function stripBackgrounds(html) {
  let n = 0;
  let out = html.replace(/style\s*=\s*(["'])([\s\S]*?)\1/gi, (m, q, css) => {
    const cleaned = css
      .split(';')
      .filter(d => {
        const prop = d.split(':')[0].trim().toLowerCase();
        const hit = prop === 'background' || prop.startsWith('background-');
        if (hit) n++;
        return !hit;
      })
      .join(';')
      .replace(/^;+|;+$/g, '');
    return `style=${q}${cleaned}${q}`;
  });
  out = out.replace(/\sbgcolor\s*=\s*(["'])[\s\S]*?\1/gi, () => { n++; return ''; });
  console.error(`[净化] 已移除 ${n} 处背景色声明`);
  return out;
}

/** 去掉 Markdown 开头的一级标题（公众号标题栏已有，正文不再重复大字） */
function stripLeadingH1(md) {
  return md.replace(/^\uFEFF?\s*#\s+.+?(?:\r?\n)+/, '');
}

function exitOk(data) { console.log(JSON.stringify(data, null, 2)); process.exit(0); }
function exitErr(error, message) {
  console.error(JSON.stringify({ success: false, error, message }, null, 2));
  process.exit(1);
}

// ── 缓存 ───────────────────────────────────────────────────────────────────
function loadCache() {
  try { return JSON.parse(fs.readFileSync(CACHE_PATH, 'utf-8')); }
  catch { return { covers: {}, bodyImages: {} }; }
}
function saveCache(cache) { fs.writeFileSync(CACHE_PATH, JSON.stringify(cache, null, 2), 'utf-8'); }

// ── MD 解析 ────────────────────────────────────────────────────────────────
function extractTitle(md) {
  const m = md.match(/^#\s+(.+)$/m);
  return m ? m[1].trim() : null;
}
function extractFirstImage(md) {
  const stripped = md.replace(/```[\s\S]*?```/g, '').replace(/`[^`\n]+`/g, '');
  const m = stripped.match(/!\[.*?\]\(((?:https?:\/\/|\.{0,2}\/|\/|\w:[\\/])[^)\s]+)\)/);
  return m ? m[1] : null;
}
function guessMime(filename) {
  const ext = path.extname(filename).toLowerCase();
  const map = { '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.gif': 'image/gif', '.webp': 'image/webp' };
  return map[ext] || 'image/jpeg';
}

// ── 图片上传（URL 或本地路径统一处理）──────────────────────────────────────
async function uploadAnyImage(src, mdDir, token, cache) {
  if (WX_DOMAINS.some(d => src.includes(d))) return src;       // 已是微信图，跳过

  let buffer, contentType, cacheKey;
  const isUrl = /^https?:\/\//i.test(src);
  if (isUrl) {
    // URL 图：URL 本身即唯一键，可先查缓存
    if (cache.bodyImages[src]) { console.error(`  [图片] 缓存命中`); return cache.bodyImages[src]; }
    cacheKey = src;
    const res = await fetch(src);
    if (!res.ok) { console.error(`  [图片] ⚠️ 下载失败 HTTP ${res.status}，跳过：${src}`); return null; }
    buffer = Buffer.from(await res.arrayBuffer());
    contentType = res.headers.get('content-type') || 'image/jpeg';
  } else {
    // 本地图：相对路径（如 images/svg_1.png）会跨文章撞车，
    // 必须用「绝对路径 + 内容哈希」做键——内容一变即重新上传。
    const localPath = path.isAbsolute(src) ? src : path.join(mdDir, src);
    if (!fs.existsSync(localPath)) { console.error(`  [图片] ⚠️ 本地图不存在，跳过：${localPath}`); return null; }
    buffer = fs.readFileSync(localPath);
    const hash = require('crypto').createHash('md5').update(buffer).digest('hex').slice(0, 12);
    cacheKey = `${path.resolve(localPath)}#${hash}`;
    if (cache.bodyImages[cacheKey]) { console.error(`  [图片] 缓存命中（内容一致）`); return cache.bodyImages[cacheKey]; }
    contentType = guessMime(localPath);
  }

  const ext = contentType.includes('png') ? '.png' : contentType.includes('gif') ? '.gif' : '.jpg';
  const form = new FormData();
  form.append('media', new Blob([buffer], { type: contentType }), `body${ext}`);
  const up = await fetch(`${WECHAT_API}/media/uploadimg?access_token=${token}`, { method: 'POST', body: form });
  const data = await up.json();
  if (!data.url) { console.error(`  [图片] ⚠️ 上传失败：${JSON.stringify(data)}`); return null; }
  cache.bodyImages[cacheKey] = data.url;
  saveCache(cache);
  console.error(`  [图片] ✅ 已上传 → ${data.url.substring(0, 60)}...`);
  return data.url;
}

/** 找出 HTML 中所有 src，统一上传并替换为微信 CDN URL（含本地路径） */
async function uploadAndReplaceBodyImages(html, mdDir, token) {
  const cache = loadCache();
  if (!cache.bodyImages) cache.bodyImages = {};
  const srcRegex = /\bsrc="([^"]+)"/g;
  const srcs = new Set();
  let m;
  while ((m = srcRegex.exec(html)) !== null) {
    if (!WX_DOMAINS.some(d => m[1].includes(d))) srcs.add(m[1]);
  }
  if (srcs.size === 0) { console.error('[图片] 正文中无需上传的外部/本地图片'); return html; }
  console.error(`[图片] 发现 ${srcs.size} 张需上传图片，开始处理...`);
  const urlMap = {};
  for (const s of srcs) {
    const r = await uploadAnyImage(s, mdDir, token, cache);
    if (r && r !== s) urlMap[s] = r;
  }
  let result = html;
  for (const [orig, rep] of Object.entries(urlMap)) {
    const esc = orig.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    result = result.replace(new RegExp(esc, 'g'), rep);
  }
  console.error(`[图片] ✅ 共替换 ${Object.keys(urlMap).length} 张`);
  return result;
}

/** 封面图上传为永久素材（支持 URL 或本地路径） */
async function uploadCoverImage(imageSource, mdDir, token) {
  const cache = loadCache();
  if (cache.covers[imageSource]) { console.error(`[封面] 缓存命中`); return cache.covers[imageSource]; }
  console.error(`[封面] 正在上传：${imageSource}`);
  let buffer, filename;
  const isUrl = /^https?:\/\//i.test(imageSource);
  if (isUrl) {
    const res = await fetch(imageSource);
    if (!res.ok) exitErr('cover_download_failed', `封面图下载失败（HTTP ${res.status}）：${imageSource}`);
    buffer = Buffer.from(await res.arrayBuffer());
    filename = path.basename(new URL(imageSource).pathname) || 'cover.jpg';
  } else {
    const localPath = path.isAbsolute(imageSource) ? imageSource : path.join(mdDir, imageSource);
    if (!fs.existsSync(localPath)) exitErr('cover_not_found', `封面图文件不存在：${localPath}`);
    buffer = fs.readFileSync(localPath);
    filename = path.basename(localPath);
  }
  const mime = guessMime(filename);
  const form = new FormData();
  form.append('media', new Blob([buffer], { type: mime }), filename);
  const upRes = await fetch(`${WECHAT_API}/material/add_material?access_token=${token}&type=image`, { method: 'POST', body: form });
  const upData = await upRes.json();
  if (upData.errcode && upData.errcode !== 0) {
    const msg = upData.errmsg || JSON.stringify(upData);
    if (upData.errcode === 40164) {
      const ip = (msg.match(/invalid ip\s+([\d.]+)/i) || [])[1] || '（见错误信息）';
      exitErr('40164', `IP 不在白名单。微信看到的实际 IP：${ip}\n请加入公众号后台 → 基础信息 → API IP 白名单后重试。`);
    }
    exitErr(`wechat_${upData.errcode}`, `封面图上传失败：${msg}`);
  }
  const mediaId = upData.media_id;
  if (!mediaId) exitErr('upload_no_media_id', `微信返回异常：${JSON.stringify(upData)}`);
  cache.covers[imageSource] = mediaId;
  saveCache(cache);
  console.error('[封面] ✅ 上传成功');
  return mediaId;
}

// ── 微信 API ───────────────────────────────────────────────────────────────
async function getAccessToken(appId, appSecret) {
  const res = await fetch(`${WECHAT_API}/token?grant_type=client_credential&appid=${appId}&secret=${appSecret}`);
  const data = await res.json();
  if (data.errcode && data.errcode !== 0) {
    if (data.errcode === 40164) {
      const ip = ((data.errmsg || '').match(/invalid ip\s+([\d.]+)/i) || [])[1] || '（见错误信息）';
      exitErr('40164', `IP 不在白名单。微信看到的实际 IP：${ip}\n请加入公众号后台 → 基础信息 → API IP 白名单后重试。`);
    }
    exitErr(`wechat_token_${data.errcode}`, `获取 access_token 失败：${data.errmsg}`);
  }
  if (!data.access_token) exitErr('token_empty', `access_token 返回异常：${JSON.stringify(data)}`);
  return data.access_token;
}

async function pushDraft(token, title, author, htmlContent, thumbMediaId) {
  const article = { title, content: htmlContent, thumb_media_id: thumbMediaId, show_cover_pic: 1, need_open_comment: 0 };
  if (author) article.author = author;
  const res = await fetch(`${WECHAT_API}/draft/add?access_token=${token}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ articles: [article] }),
  });
  const data = await res.json();
  if (data.errcode && data.errcode !== 0) {
    const msg = data.errmsg || JSON.stringify(data);
    if (data.errcode === 40164) {
      const ip = (msg.match(/invalid ip\s+([\d.]+)/i) || [])[1] || '（见错误信息）';
      exitErr('40164', `IP 不在白名单。微信看到的实际 IP：${ip}\n请加入公众号后台 → 基础信息 → API IP 白名单后重试。`);
    }
    exitErr(`wechat_draft_${data.errcode}`, `推送草稿失败：${msg}`);
  }
  return data.media_id;
}

// ── 主流程 ─────────────────────────────────────────────────────────────────
async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.file) exitErr('missing_arg', '缺少 --file 参数');
  if (!fs.existsSync(args.file)) exitErr('file_not_found', `MD 不存在：${args.file}`);

  const account = process.env.ACCOUNT;
  const themeId = process.env.THEME_ID;
  const apiBase = (process.env.API_URL || 'https://feishu2weixin.maolai.cc').replace(/\/$/, '');
  const appId = process.env.WECHAT_APP_ID;
  const appSecret = process.env.WECHAT_APP_SECRET;
  const defaultCover = process.env.WECHAT_DEFAULT_COVER || FALLBACK_COVER;
  const defaultAuthor = process.env.AUTHOR_NAME || '';

  const missingEnv = [
    !account && 'ACCOUNT', !themeId && 'THEME_ID',
    !appId && 'WECHAT_APP_ID', !appSecret && 'WECHAT_APP_SECRET',
  ].filter(Boolean);
  if (missingEnv.length) exitErr('missing_env', '缺少环境变量，请检查本 skill 目录的 .env：\n' + missingEnv.map(v => `  - ${v}`).join('\n'));

  if (!args.confirmed) {
    let publicIp = '（查询失败）';
    try { const r = await fetch('https://api4.ipify.org'); if (r.ok) publicIp = (await r.text()).trim(); } catch {}
    console.log(JSON.stringify({
      success: false, error: 'need_confirm', ip: publicIp,
      message: `请将以下 IP 加入公众号后台 → 基础信息 → API IP 白名单：${publicIp}\n确认后加 --confirmed 重新运行。`,
    }, null, 2));
    process.exit(0);
  }

  const mdContent = fs.readFileSync(args.file, 'utf-8');
  // 正文默认不重复大标题：渲染前先摘掉开头的 H1（标题仍从这里提取给草稿标题栏）
  const mdForRender = args.keepH1 ? mdContent : stripLeadingH1(mdContent);
  if (!args.keepH1 && mdForRender !== mdContent) console.error('[排版] 已移除正文顶部大标题');

  console.error('[渲染] 调用渲染 API...');
  const res = await fetch(`${apiBase}/api/skill`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Account': account, 'X-Theme-Id': themeId },
    body: JSON.stringify({ action: 'render', markdown: mdForRender }),
  });
  if (!res.ok) exitErr('api_http_error', `渲染 API HTTP ${res.status}`);
  const data = await res.json();
  if (!data.success) exitErr('api_error', `渲染失败：${data.error || JSON.stringify(data)}`);
  let html = data.html || '';
  if (!html) exitErr('empty_html', '渲染返回空内容，检查 ACCOUNT / THEME_ID');
  console.error('[渲染] ✅ 完成');

  // 剥掉主题带来的黄底/色块，纯白无背景
  if (!args.keepBg) html = stripBackgrounds(html);

  const mdDir = path.dirname(path.resolve(args.file));
  const title = args.title || extractTitle(mdContent) || path.basename(args.file, path.extname(args.file));
  const author = args.author || defaultAuthor;
  console.error(`[草稿] 标题：${title} | 作者：${author || '（未设置）'}`);

  let coverSource;
  if (args.cover) coverSource = args.cover;
  else {
    const mdImg = extractFirstImage(mdContent);
    coverSource = mdImg || defaultCover;
    console.error(`[封面] 来源：${coverSource}`);
  }

  console.error('[微信] 获取 access_token...');
  const token = await getAccessToken(appId, appSecret);
  const thumbMediaId = await uploadCoverImage(coverSource, mdDir, token);
  const processedHtml = await uploadAndReplaceBodyImages(html, mdDir, token);
  console.error('[草稿] 推送中...');
  const draftMediaId = await pushDraft(token, title, author, processedHtml, thumbMediaId);
  exitOk({ success: true, media_id: draftMediaId, title, message: '草稿已推送，请前往公众号后台 → 草稿箱查看' });
}

main().catch(e => exitErr('unexpected', e.message));
