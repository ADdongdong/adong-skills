/**
 * render_local.cjs - 本地 Markdown → 微信公众号 HTML 渲染器
 *
 * 为什么需要它：远端排版服务（feishu2weixin）依赖账号下的主题 ID，
 * 主题失效/服务不可用时整条推送链就断了。本模块把排版搬回本地，
 * 零外部依赖，输出全内联样式（微信会过滤 <style>/class，必须内联）。
 *
 * 排版硬规则（与 references/style_guide.md 一致）：
 *   - 零背景色：任何元素都不写 background，纯白底
 *   - 不重复标题：调用方已剥掉开头 H1
 *   - 不用引用块竖条：对话行走普通段落
 *   - 主色 #1c5fd9 承担结构与人物，砖红 #c86442 承担正文加粗强调
 *
 * 用法：
 *   const { renderMarkdown } = require('./render_local.cjs');
 *   const html = renderMarkdown(md);
 */

'use strict';

// ── 设计令牌 ───────────────────────────────────────────────────────────────
const T = {
  ink: '#111418',        // 标题/加粗
  body: '#33373d',       // 正文
  muted: '#9aa4b2',      // 图注/辅助
  blue: '#1c5fd9',       // 主色：结构、人物名
  brick: '#c86442',      // 强调：正文加粗
  line: '#e8ecf2',       // 分割线/边框
  cellLine: '#dfe4ec',   // 表格边框
};

const S = {
  p: `font-size:16px;line-height:1.9;color:${T.body};margin:0 0 20px;letter-spacing:0.4px;text-align:justify`,
  h1: `font-size:23px;font-weight:800;color:${T.ink};margin:0 0 22px;line-height:1.4`,
  h2: `font-size:20px;font-weight:800;color:${T.ink};margin:38px 0 16px;line-height:1.45;letter-spacing:0.3px`,
  h3: `font-size:17px;font-weight:700;color:${T.blue};margin:28px 0 12px;line-height:1.5`,
  strong: `font-weight:700;color:${T.brick}`,
  code: `font-family:Consolas,Monaco,"Courier New",monospace;font-size:14.5px;color:${T.blue};padding:1px 4px;border:1px solid ${T.line};border-radius:3px`,
  link: `color:${T.blue};text-decoration:none;border-bottom:1px solid ${T.line}`,
  hr: `border:none;border-top:1px solid ${T.line};margin:34px 0`,
  ul: `margin:0 0 22px;padding-left:20px;list-style-type:disc`,
  ol: `margin:0 0 22px;padding-left:20px;list-style-type:decimal`,
  li: `font-size:16px;line-height:1.9;color:${T.body};margin:0 0 10px;letter-spacing:0.3px`,
  figWrap: `margin:6px 0 26px;text-align:center`,
  img: `max-width:100%;width:100%;display:block;border-radius:6px;margin:0 auto`,
  cap: `display:block;font-size:13px;color:${T.muted};text-align:center;margin-top:10px;line-height:1.6`,
  table: `width:100%;max-width:100%;table-layout:fixed;border-collapse:collapse;margin:6px 0 26px;font-size:13.5px;line-height:1.6`,
  th: `border:1px solid ${T.cellLine};padding:8px 6px;text-align:left;font-weight:700;color:${T.ink};vertical-align:top;box-sizing:border-box;word-break:break-word;overflow-wrap:break-word`,
  td: `border:1px solid ${T.cellLine};padding:8px 6px;text-align:left;color:${T.body};vertical-align:top;box-sizing:border-box;word-break:break-word;overflow-wrap:break-word`,
};

// ── 内联解析 ───────────────────────────────────────────────────────────────
/**
 * 处理行内语法：**加粗** / `代码` / [链接](url)
 * 已有 HTML 标签（如 <span style=...>）必须原样保留，不能被转义或误匹配。
 * 做法：先把标签与行内代码抽成占位符，处理完再回填。
 */
function inline(text) {
  const stash = [];
  const keep = (s) => `\u0000${stash.push(s) - 1}\u0000`;

  // 1) 已存在的 HTML 标签整体保护
  let out = text.replace(/<\/?[a-zA-Z][^>]*>/g, (m) => keep(m));

  // 2) 行内代码保护（避免内部 ** 被解析）
  out = out.replace(/`([^`\n]+)`/g, (m, code) => keep(`<code style="${S.code}">${esc(code)}</code>`));

  // 3) 链接
  out = out.replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g,
    (m, label, url) => `<a href="${url}" style="${S.link}">${label}</a>`);

  // 4) 加粗
  out = out.replace(/\*\*([^*\n]+)\*\*/g, (m, t) => `<strong style="${S.strong}">${t}</strong>`);

  // 5) 回填占位符
  out = out.replace(/\u0000(\d+)\u0000/g, (m, i) => stash[Number(i)]);
  return out;
}

function esc(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// ── 块级解析 ───────────────────────────────────────────────────────────────
const HTML_BLOCK = /^\s*<(section|div|table|figure|blockquote|p|h[1-6]|ul|ol|li|img|br|hr|span)\b/i;

function isTableRow(line) { return /^\s*\|.*\|\s*$/.test(line); }
function isTableSep(line) { return /^\s*\|[\s:|-]+\|\s*$/.test(line); }

function renderTable(rows) {
  const cells = (line) => line.trim().replace(/^\||\|$/g, '').split('|').map(c => c.trim());
  const head = cells(rows[0]);
  const bodyRows = rows.slice(1).filter(r => !isTableSep(r)).map(cells);

  const th = head.map(c => `<th style="${S.th}">${inline(c)}</th>`).join('');
  const tb = bodyRows.map(r => {
    const tds = r.map(c => `<td style="${S.td}">${inline(c)}</td>`).join('');
    return `<tr>${tds}</tr>`;
  }).join('');

  return `<table style="${S.table}"><thead><tr>${th}</tr></thead><tbody>${tb}</tbody></table>`;
}

function renderList(items, ordered) {
  const tag = ordered ? 'ol' : 'ul';
  const style = ordered ? S.ol : S.ul;
  const lis = items.map(it => `<li style="${S.li}">${inline(it)}</li>`).join('');
  return `<${tag} style="${style}">${lis}</${tag}>`;
}

/**
 * 主渲染函数
 * @param {string} md Markdown 源码（开头 H1 已由调用方剥离）
 * @returns {string} 微信可用的 HTML 片段（全内联样式）
 */
function renderMarkdown(md) {
  const lines = String(md).replace(/\r\n?/g, '\n').split('\n');
  const out = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // 空行
    if (!line.trim()) { i++; continue; }

    // 代码块（公众号里少见，保留为等宽段落）
    if (/^\s*```/.test(line)) {
      i++;
      const buf = [];
      while (i < lines.length && !/^\s*```/.test(lines[i])) buf.push(lines[i++]);
      i++;
      out.push(`<p style="font-size:14.5px;line-height:1.8;color:${T.body};margin:0 0 20px;padding:12px 14px;border:1px solid ${T.line};border-radius:6px;font-family:Consolas,Monaco,monospace;white-space:pre-wrap">${esc(buf.join('\n'))}</p>`);
      continue;
    }

    // 已存在的 HTML 块：原样输出（正文里的 PART 章节标题就是这种）
    if (HTML_BLOCK.test(line)) { out.push(line.trim()); i++; continue; }

    // 水平线
    if (/^\s*(---+|\*\*\*+|___+)\s*$/.test(line)) { out.push(`<hr style="${S.hr}">`); i++; continue; }

    // 标题
    const h = line.match(/^(#{1,6})\s+(.+)$/);
    if (h) {
      const level = h[1].length;
      const text = inline(h[2].trim());
      if (level === 1) out.push(`<h1 style="${S.h1}">${text}</h1>`);
      else if (level === 2) out.push(`<h2 style="${S.h2}">${text}</h2>`);
      else out.push(`<h3 style="${S.h3}">${text}</h3>`);
      i++; continue;
    }

    // 图片（整行）：带图注
    const img = line.match(/^\s*!\[([^\]]*)\]\(([^)\s]+)\)\s*$/);
    if (img) {
      const alt = img[1].trim();
      const src = img[2].trim();
      const cap = alt ? `<span style="${S.cap}">${inline(alt)}</span>` : '';
      out.push(`<p style="${S.figWrap}"><img src="${src}" style="${S.img}">${cap}</p>`);
      i++; continue;
    }

    // 表格
    if (isTableRow(line)) {
      const rows = [];
      while (i < lines.length && isTableRow(lines[i])) rows.push(lines[i++]);
      if (rows.length >= 2) { out.push(renderTable(rows)); continue; }
    }

    // 列表
    if (/^\s*[-*+]\s+/.test(line) || /^\s*\d+\.\s+/.test(line)) {
      const ordered = /^\s*\d+\.\s+/.test(line);
      const items = [];
      while (i < lines.length) {
        const l = lines[i];
        const m = l.match(/^\s*(?:[-*+]|\d+\.)\s+(.+)$/);
        if (!m) break;
        items.push(m[1].trim());
        i++;
      }
      out.push(renderList(items, ordered));
      continue;
    }

    // 普通段落：连续非空行合并
    const buf = [line.trim()];
    i++;
    while (i < lines.length) {
      const l = lines[i];
      if (!l.trim()) break;
      if (/^\s*(#{1,6}\s|!\[|---+$|\*\*\*+$)/.test(l)) break;
      if (isTableRow(l) || /^\s*[-*+]\s+/.test(l) || /^\s*\d+\.\s+/.test(l)) break;
      if (HTML_BLOCK.test(l)) break;
      buf.push(l.trim());
      i++;
    }
    out.push(`<p style="${S.p}">${inline(buf.join(' '))}</p>`);
  }

  return out.join('\n');
}

module.exports = { renderMarkdown };

// 直接执行时：node render_local.cjs <input.md> [output.html]
if (require.main === module) {
  const fs = require('fs');
  const [, , inFile, outFile] = process.argv;
  if (!inFile) { console.error('用法: node render_local.cjs <input.md> [output.html]'); process.exit(1); }
  const md = fs.readFileSync(inFile, 'utf-8').replace(/^\uFEFF?\s*#\s+.+?(?:\r?\n)+/, '');
  const html = renderMarkdown(md);
  if (outFile) { fs.writeFileSync(outFile, html, 'utf-8'); console.error(`✅ 已写入 ${outFile}（${html.length} 字符）`); }
  else console.log(html);
}
