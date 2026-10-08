/**
 * push_with_local_images.cjs — 增版推送：支持本地路径图片自动上传到微信 CDN
 *
 * 基于 publish.cjs，增加：渲染后的 HTML 中 <img src="本地路径">
 * 也会被读取文件并上传到微信 /media/uploadimg，替换为 CDN URL。
 *
 * 用法：
 *   node push_with_local_images.cjs --file <带图片的MD> [--title ..] [--author ..] [--cover ..]
 */
'use strict';
const fs   = require('fs');
const path = require('path');

// ── 读取 .env ──────────────────────────────────────────────────────────────
const envPath = path.join(__dirname, '..', '.env');
if (fs.existsSync(envPath)) {
  fs.readFileSync(envPath, 'utf-8').split('\n').forEach(line => {
    const m = line.match(/^\s*([^#=\s][^=]*?)\s*=\s*(.*?)\s*$/);
    if (m) process.env[m[1]] = m[2];
  });
}

// ── 常量 ───────────────────────────────────────────────────────────────────
const FALLBACK_COVER = 'https://zaowu-pic.maolai.cc/uploads/1774501229309-Image_55.jpg';
const WECHAT_API     = 'https://api.weixin.qq.com/cgi-bin';
const CACHE_PATH     = path.join(process.env.TMP || process.env.TEMP || '/tmp', '.md_wechat_cache.json');

// ── 解析命令行参数 ─────────────────────────────────────────────────────────
function parseArgs(argv) {
  const args = { confirmed: true }; // 本脚本默认已确认
  for (let i = 0; i < argv.length; i++) {
    if      (argv[i] === '--file')      args.file      = argv[++i];
    else if (argv[i] === '--title')     args.title     = argv[++i];
    else if (argv[i] === '--author')    args.author    = argv[++i];
    else if (argv[i] === '--cover')     args.cover     = argv[++i];
    else if (argv[i] === '--confirmed') args.confirmed = true;
  }
  return args;
}

// ── 输出辅助 ───────────────────────────────────────────────────────────────
function exitOk(data) { console.log(JSON.stringify(data, null, 2)); process.exit(0); }
function exitErr(error, message) { console.error(JSON.stringify({ success:false, error, message }, null,2)); process.exit(1); }

// ── 缓存操作 ───────────────────────────────────────────────────────────────
function loadCache() { try { return JSON.parse(fs.readFileSync(CACHE_PATH,'utf-8')); } catch { return { covers:{}, bodyImages:{} }; } }
function saveCache(cache) { fs.writeFileSync(CACHE_PATH, JSON.stringify(cache,null,2),'utf-8'); }

// ── MD 文件解析 ────────────────────────────────────────────────────────────
function extractTitle(md) { const m=md.match(/^#\s+(.+)$/m); return m?m[1].trim():null; }
function extractFirstImage(md) {
  const stripped = md.replace(/```[\s\S]*?```/g,'').replace(/`[^`\n]+`/g,'');
  const m = stripped.match(/!\[.*?\]\(((?:https?:\/\/|\.{0,2}\/)[^)\s]+)\)/);
  return m ? m[1] : null;
}
function guessMime(filename) {
  const ext=path.extname(filename).toLowerCase();
  const map={'.jpg':'image/jpeg','.jpeg':'image/jpeg','.png':'image/png','.gif':'image/gif','.webp':'image/webp'};
  return map[ext]||'image/jpeg';
}

// ── 封面上传（支持URL + 本地路径）────────────────────────────────────────
async function uploadCoverImage(imageSource, mdDir, token) {
  const cache=loadCache(); if(cache.covers[imageSource]){console.error(`[封面] 缓存命中：${imageSource}`);return cache.covers[imageSource];}
  console.error(`[封面] 正在上传封面图：${imageSource}`);
  let buffer,filename; const isUrl=/^https?:\/\//i.test(imageSource);
  if(isUrl){const r=await fetch(imageSource);if(!r.ok)exitErr('cover_download_failed',`下载失败HTTP${r.status}：${imageSource}`);
    buffer=Buffer.from(await r.arrayBuffer());filename=path.basename(new URL(imageSource).pathname)||'cover.jpg';}
  else{const lp=path.isAbsolute(imageSource)?imageSource:path.join(mdDir,imageSource);
    if(!fs.existsSync(lp))exitErr('cover_not_found',`文件不存在：${lp}`);
    buffer=fs.readFileSync(lp);filename=path.basename(lp);}
  const mime=guessMime(filename);const form=new FormData();form.append('media',new Blob([buffer],{type:mime}),filename);
  const upRes=await fetch(`${WECHAT_API}/material/add_material?access_token=${token}&type=image`,{method:'POST',body:form});
  const upData=await upRes.json();
  if(upData.errcode&&upData.errcode!==0){const msg=upData.errmsg||JSON.stringify(upData);
    if(upData.errcode===40164){const ip=(msg.match(/invalid ip\s+([\d.]+)/i)||[])[1]||'（见错误信息）';
      exitErr('40164',`IP不在白名单。微信看到的实际IP：${ip}\n请加入公众号后台→基础配置→API IP白名单后重试。\n原始错误：${msg}`);}
    exitErr(`wechat_${upData.errcode}`,`封面上传失败：${msg}`);}
  if(!upData.media_id)exitErr('upload_no_media_id',`异常返回：${JSON.stringify(upData)}`);
  cache.covers[imageSource]=upData.media_id;saveCache(cache);
  console.error('[封面] ✅ 上传成功');return upData.media_id;
}

// ── 正文图片上传（核心增强：同时处理 URL + 本地路径）──────────────────────
async function uploadBodyImage(source, mdDir, token) {
  const cache=loadCache();if(!cache.bodyImages)cache.bodyImages={};
  if(cache.bodyImages[source])return cache.bodyImages[source];
  console.error(`  [图片] 正在上传：${source.substring(0,80)}...`);
  try{
    let buffer,contentType;
    const isUrl=/^https?:\/\//i.test(source);
    if(isUrl){
      const res=await fetch(source);if(!res.ok){console.error(`  [图片] ⚠️ 下载失败(HTTP${res.status})，跳过`);return null;}
      buffer=Buffer.from(await res.arrayBuffer());contentType=res.headers.get('content-type')||'image/jpeg';
    }else{
      const lp=path.isAbsolute(source)?source:path.join(mdDir,source);
      if(!fs.existsSync(lp)){console.error(`  [图片] ⚠️ 文件不存在(${lp})，跳过`);return null;}
      buffer=fs.readFileSync(lp);contentType=guessMime(lp);
    }
    const ext=contentType.includes('png')?'.png':contentType.includes('gif')?'.gif':'.jpg';
    const form=new FormData();form.append('media',new Blob([buffer],{type:contentType}),`body_img${ext}`);
    const upRes=await fetch(`${WECHAT_API}/media/uploadimg?access_token=${token}`,{method:'POST',body:form});
    const upData=await upRes.json();
    if(!upData.url){console.error(`  [图片] ⚠️ 上传失败：${JSON.stringify(upData)}，跳过`);return null;}
    cache.bodyImages[source]=upData.url;saveCache(cache);
    console.error(`  [图片] ✅ 已上传 → ${upData.url.substring(0,60)}...`);
    return upData.url;
  }catch(e){console.error(`  [图片] ⚠️ 异常(${e.message})，跳过`);return null;}
}

/** 找出所有图片（URL + 本地相对路径）并上传到微信CDN */
async function uploadAndReplaceAllImages(html, mdDir, token) {
  const weixinDomains=['mmbiz.qpic.cn','mmbiz.qlogo.cn','res.wx.qq.com'];
  // 匹配所有 src="..." 属性值（包括相对路径）
  const srcRegex=/\bsrc="([^"]+)"/g;
  const sources=new Set();let m;
  while((m=srcRegex.exec(html))!==null){
    if(!weixinDomains.some(d=>m[1].includes(d)))sources.add(m[1]);
  }
  if(sources.size===0){console.error('[图片] 无需上传的图片');return html;}
  console.error(`[图片] 发现 ${sources.size} 张图片（含本地路径），开始上传到微信服务器...`);
  const urlMap={};
  for(const url of sources){const wurl=await uploadBodyImage(url,mdDir,token);if(wurl)urlMap[url]=wurl;}
  let result=html;
  for(const[orig,repl]of Object.entries(urlMap)){
    const escaped=orig.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
    result=result.replace(new RegExp(escaped,'g'),repl);
  }
  console.error(`[图片] ✅ 共替换 ${Object.keys(urlMap).length} 张图片URL`);
  return result;
}

// ── 微信 API ───────────────────────────────────────────────────────────────
async function getAccessToken(appId,appSecret){
  const res=await fetch(`${WECHAT_API}/token?grant_type=client_credential&appid=${appId}&secret=${appSecret}`);
  const data=await res.json();
  if(data.errcode&&data.errcode!==0){
    if(data.errcode===40164){const ip=((data.errmsg||'').match(/invalid ip\s+([\d.]+)/i)||[])[1]||'（见错误信息）';
      exitErr('40164',`IP不在白名单。微信实际IP：${ip}\n请加入白名单后重试。\n原始错误：${data.errmsg}`);}
    exitErr(`wechat_token_${data.errcode}`,`获取token失败：${data.errmsg}（${data.errcode}）`);}
  if(!data.access_token)exitErr('token_empty',`异常返回：${JSON.stringify(data)}`);
  return data.access_token;
}

async function pushDraft(token,title,author,htmlContent,thumbMediaId){
  const article={title,content:htmlContent,thumb_media_id:thumbMediaId,show_cover_pic:1,need_open_comment:0};
  if(author)article.author=author;
  const res=await fetch(`${WECHAT_API}/draft/add?access_token=${token}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({articles:[article]})});
  const data=await res.json();
  if(data.errcode&&data.errcode!==0){const msg=data.errmsg||JSON.stringify(data);
    if(data.errcode===40164){const ip=(msg.match(/invalid ip\s+([\d.]+)/i)||[])[1]||'（见错误信息）';
      exitErr('40164',`IP不在白名单。微信实际IP：${ip}\n请加白名单。\n原始错误：${msg}`);}
    exitErr(`wechat_draft_${data.errcode}`,`推送草稿失败：${msg}（${data.errcode}）`);}
  return data.media_id;
}

// ── 主流程 ─────────────────────────────────────────────────────────────────
async function main(){
  const args=parseArgs(process.argv.slice(2));
  if(!args.file)exitErr('missing_arg','缺少--file参数');
  if(!fs.existsSync(args.file))exitErr('file_not_found',`MD文件不存在：${args.file}`);

  const account=process.env.ACCOUNT;const themeId=process.env.THEME_ID;
  const apiBase=(process.env.API_URL||'https://feishu2weixin.maolai.cc').replace(/\/$/,'');
  const appId=process.env.WECHAT_APP_ID;const appSecret=process.env.WECHAT_APP_SECRET;
  const defaultCover=process.env.WECHAT_DEFAULT_COVER||FALLBACK_COVER;
  const defaultAuthor=process.env.AUTHOR_NAME||'';

  const missingEnv=[!account&&'ACCOUNT',!themeId&&'THEME_ID',!appId&&'WECHAT_APP_ID',!appSecret&&'WECHAT_APP_SECRET'].filter(Boolean);
  if(missingEnv.length)exitErr('missing_env','缺少环境变量：\n'+missingEnv.map(v=>`  - ${v}`).join('\n'));

  // 步骤1：渲染
  console.error('[渲染] 正在调用渲染API...');
  let html;try{
    const res=await fetch(`${apiBase}/api/skill`,{method:'POST',headers:{'Content-Type':'application/json','X-Account':account,'X-Theme-Id':themeId},body:JSON.stringify({action:'render',markdown:fs.readFileSync(args.file,'utf-8')})});
    if(!res.ok)exitErr('api_http_error',`渲染API返回HTTP${res.status}`);
    const data=await res.json();if(!data.success)exitErr('api_error',`渲染错误：${data.error||JSON.stringify(data)}`);
    html=data.html||'';if(!html)exitErr('empty_html','渲染返回空内容');
  }catch(e){if(e.code==='missing_env'||e.code==='api_http_error')throw e;exitErr('render_failed',`渲染失败：${e.message}`);}
  console.error('[渲染] ✅ 完成');

  // 步骤2：标题、作者、封面
  const mdContent=fs.readFileSync(args.file,'utf-8');const mdDir=path.dirname(path.resolve(args.file));
  const title=args.title||extractTitle(mdContent)||path.basename(args.file,path.extname(args.file));
  const author=args.author||defaultAuthor;
  console.error(`[草稿] 标题：${title}`);

  let coverSource;if(args.cover)coverSource=args.cover;
  else{const mdImg=extractFirstImage(mdContent);if(mdImg)coverSource=mdImg;else coverSource=defaultCover;}

  // 步骤3：微信API + 图片上传（含本地路径！）
  console.error('[微信] 正在获取access_token...');
  const token=await getAccessToken(appId,appSecret);console.error('[微信] ✅ token获取成功');
  const thumbMediaId=await uploadCoverImage(coverSource,mdDir,token);

  // 核心：上传所有图片（URL + 本地路径）到微信CDN
  const processedHtml=await uploadAndReplaceAllImages(html,mdDir,token);

  // 步骤4：推送
  console.error('[草稿] 正在推送到微信草稿箱...');
  const draftMediaId=await pushDraft(token,title,author,processedHtml,thumbMediaId);
  console.error('[草稿] ✅ 推送成功');
  exitOk({success:true,media_id:draftMediaId,title,message:'草稿已推送成功，请前往公众号后台→草稿箱查看'});
}
main().catch(e=>exitErr('unexpected',e.message));
