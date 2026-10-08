// 按 Unsplash 图片 ID 下载真实照片到工作目录，并自动记录来源（provenance）。
//
// 用法：
//   node scripts/fetch_photo.cjs <工作目录> <id1> [id2] [id3] ...
//   node scripts/fetch_photo.cjs <工作目录> --sheet          # 仅重新拼候选总览图
//
// 产出：
//   <工作目录>/assets/cand1.jpg, cand2.jpg, ...   下载的候选照片
//   <工作目录>/assets/SOURCES.md                  来源记录（guizang 规范要求）
//
// 怎么拿 ID（由 AI 执行，脚本不做搜索）：
//   1. 从推文核心类比提炼视觉关键词（英文效果最好，如 bookmark-book / traffic-light）
//   2. WebFetch https://unsplash.com/s/photos/<关键词>
//   3. 从返回里挑「不带 Unsplash+ 标记」的免费图，取其 download 链接中的 ID
//      形如 https://unsplash.com/photos/bYy9hndOx0k/download → ID = bYy9hndOx0k
//
// 为什么不直接 curl 搜索页：unsplash.com 搜索页有反爬（401/307），
// 但 /photos/<id>/download 端点可达，会 302 到 images.unsplash.com CDN（实测 200）。

const fs = require('fs');
const path = require('path');
const https = require('https');

const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36';

function download(url, dest, depth = 0) {
  return new Promise((resolve, reject) => {
    if (depth > 6) return reject(new Error('重定向次数过多'));
    https.get(url, { headers: { 'User-Agent': UA } }, res => {
      // 跟随重定向
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        res.resume();
        return download(res.headers.location, dest, depth + 1).then(resolve, reject);
      }
      if (res.statusCode !== 200) {
        res.resume();
        return reject(new Error(`HTTP ${res.statusCode}`));
      }
      const chunks = [];
      res.on('data', c => chunks.push(c));
      res.on('end', () => {
        const buf = Buffer.concat(chunks);
        fs.writeFileSync(dest, buf);
        resolve({ bytes: buf.length, finalUrl: url });
      });
      res.on('error', reject);
    }).on('error', reject);
  });
}

(async () => {
  const dir = path.resolve(process.argv[2] || '.');
  const ids = process.argv.slice(3).filter(a => !a.startsWith('--'));
  if (!ids.length) {
    console.error('用法：node scripts/fetch_photo.cjs <工作目录> <unsplash_id> [id2] ...');
    process.exit(1);
  }

  const assetsDir = path.join(dir, 'assets');
  fs.mkdirSync(assetsDir, { recursive: true });

  const records = [];
  for (let i = 0; i < ids.length; i++) {
    const id = ids[i];
    const out = path.join(assetsDir, `cand${i + 1}.jpg`);
    const url = `https://unsplash.com/photos/${id}/download?force=true`;
    process.stdout.write(`[取图] ${id} ... `);
    try {
      const { bytes, finalUrl } = await download(url, out);
      console.log(`✅ cand${i + 1}.jpg (${Math.round(bytes / 1024)}KB)`);
      // 从 CDN 最终 URL 里解析作者（?dl=<author>-<id>-unsplash.jpg）
      const m = /dl=([a-z0-9-]+)-[A-Za-z0-9_-]+-unsplash/i.exec(finalUrl);
      records.push({
        file: `cand${i + 1}.jpg`,
        id,
        author: m ? m[1].replace(/-/g, ' ') : 'unknown',
        page: `https://unsplash.com/photos/${id}`,
      });
    } catch (e) {
      console.log(`❌ ${e.message}`);
    }
  }

  if (!records.length) { console.error('没有下载成功任何图片'); process.exit(1); }

  // 写来源记录（guizang 规范：始终保留 provenance）
  const srcPath = path.join(assetsDir, 'SOURCES.md');
  const lines = [
    '# 图片来源',
    '',
    `取图时间：${new Date().toISOString().slice(0, 19).replace('T', ' ')}`,
    '来源站点：Unsplash（免费图库，Unsplash License）',
    '',
    ...records.map(r => `- \`${r.file}\` ← ${r.page} · Photo by ${r.author}`),
    '',
    '> ⚠️ 版权未经逐张核实。Unsplash License 允许商用与修改，但建议在正文或图角标注来源。',
  ];
  fs.writeFileSync(srcPath, lines.join('\n'), 'utf-8');
  console.log(`[取图] 来源已记录 -> assets/SOURCES.md`);
  console.log(`[取图] 完成 ${records.length} 张。下一步：挑一张改到 cover.html 的 --art，再跑 render_cover.cjs`);
})().catch(e => { console.error('取图失败：', e.message); process.exit(1); });
