#!/usr/bin/env node
/**
 * verify_ports.cjs — 渲染每个移植件，截图并收集运行期错误。
 *
 * 为什么必须真的跑一遍浏览器：
 *   CSS 是机器编译出来的，语法对不代表视觉对。这个脚本能一次性抓出
 *   ① JS 报错（元素/时序写错）② 布局塌陷 ③ 明暗两套令牌失效
 *   ④ 缺失的样式（用一组探针类比对 computed style）
 *
 * 用法:
 *   node --experimental-... verify_ports.cjs [--only slug] [--scale 2]
 *
 * 依赖: playwright（从 NODE_PATH 指定的 node workspace 解析）
 */
const fs = require('fs');
const path = require('path');

const SKILL = path.resolve(__dirname, '..');
const HTML_DIR = path.join(SKILL, 'assets', 'html');
const SHOT_DIR = path.join(SKILL, '_verify');

const args = process.argv.slice(2);
const argOf = (k, d) => {
  const i = args.indexOf(k);
  return i >= 0 ? args[i + 1] : d;
};
const ONLY = argOf('--only', null);
const SCALE = Number(argOf('--scale', '2'));

function loadPlaywright() {
  // 候选顺序：显式环境变量 → Node 自带解析 → $NODE_PATH → ~ 下的 WorkBuddy 托管运行时。
  // 托管路径用 os.homedir() 推导，**不写字面量用户名**，换机器也能命中。
  const home = require('os').homedir();
  const cands = [
    process.env.PW_PATH,
    'playwright',
    process.env.NODE_PATH ? path.join(process.env.NODE_PATH, 'playwright') : null,
    path.join(home, '.workbuddy', 'binaries', 'node', 'workspace', 'node_modules', 'playwright'),
  ].filter(Boolean);
  for (const c of cands) {
    try { return require(c); } catch { /* try next */ }
  }
  throw new Error(
    '找不到 playwright。请任选一种方式：\n' +
    '  · 在本目录 npm i playwright（或全局装）\n' +
    '  · 设 PW_PATH=<playwright 所在目录>\n' +
    '  · 设 NODE_PATH=<含 playwright 的 node_modules 目录>'
  );
}

/**
 * styleAudit — 断言「生成的 CSS 规则真的生效了」。
 *
 * 为什么需要：截图只能看出明显的塌陷，看不出"某个 utility 静默丢了样式"。
 * 做法：把页面里我们生成的 `[class~="X"] { prop: value }` 规则反解出来，
 *       按元素找到匹配者，用 getComputedStyle 核对。
 *       对 var(--token) 形式的值，先从 :root 解析成实际值再比。
 *
 * 只核对少数几类"一眼看不出但很致命"的属性：颜色、阴影、圆角、display、animation。
 */
async function styleAudit(page) {
  return page.evaluate(() => {
    const WATCH = new Set([
      'background-color', 'color', 'box-shadow', 'border-radius', 'display',
      'animation-name', 'column-gap', 'row-gap', 'gap', 'opacity',
    ]);
    const rootCs = getComputedStyle(document.documentElement);
    const rootFont = parseFloat(rootCs.fontSize) || 16;
    const rules = [];

    // 只审计「基础态」规则：
    //  - 带伪类/属性变体的（:hover / :disabled / ::placeholder / [aria-*] / .dark）
    //    在静态渲染时本来就不会生效，核对它们只会产生假阳性
    //  - @media / @supports 包裹的规则同理（当前视口不一定命中）
    const walk = (rs, conditional) => {
      for (const r of Array.from(rs || [])) {
        // Chrome 里 CSSStyleRule 也带 cssRules（CSS Nesting），但是空列表。
        // 若只判断 `r.cssRules` 为真就 continue，会把真正的规则全部跳过。
        if (r.cssRules && r.cssRules.length) { walk(r.cssRules, conditional); continue; }
        if (!r.selectorText || !r.style) continue;
        if (conditional) continue;
        const sel = r.selectorText;
        const m = sel.match(/\[class~="([^"]+)"\]/);
        if (!m) continue;
        // 属性选择器之后若还有伪类/伪元素/祖先条件，跳过
        const tail = sel.slice(sel.indexOf(m[0]) + m[0].length);
        if (/[:.]/.test(tail) || sel.startsWith('.dark') || sel.includes(' ') && sel.indexOf('.dark') === 0) continue;
        if (sel.indexOf('.dark') === 0 || /^\s*\.dark\b/.test(sel)) continue;
        for (const prop of Array.from(r.style)) {
          if (!WATCH.has(prop)) continue;
          rules.push({ cls: m[1], prop, value: r.style.getPropertyValue(prop) });
        }
      }
    };
    for (const sheet of Array.from(document.styleSheets)) {
      let list;
      try { list = sheet.cssRules; } catch { continue; }
      for (const r of Array.from(list || [])) {
        if (r.cssRules && r.cssRules.length) walk(r.cssRules, true);
        else walk([r], false);
      }
    }

    // ── 值等价判断 ──
    // 必须容忍三件事，否则全是假阳性：
    //   ① 单位不同但等值：0.625rem ↔ 10px（rem 按根字号换算）
    //   ② 简写展开/重排：box-shadow 被浏览器规范成 `0px 0px 0px 1px`
    //   ③ transparent ↔ rgba(0,0,0,0)
    const nums = (s) => (String(s).match(/-?\d*\.?\d+(?:e-?\d+)?/gi) || [])
      .map(Number).filter((n) => Number.isFinite(n));
    const pxNums = (s) => {
      const out = [];
      const re = /(-?\d*\.?\d+)(rem|em|px)?/gi;
      let m;
      while ((m = re.exec(String(s)))) {
        let v = parseFloat(m[1]);
        if (!Number.isFinite(v)) continue;
        if (m[2] === 'rem' || m[2] === 'em') v *= rootFont;
        out.push(Math.round(v * 1000) / 1000);
      }
      return out.sort((a, b) => a - b);
    };
    const isTransparent = (s) =>
      /^(transparent|rgba?\(\s*0\s*,\s*0\s*,\s*0\s*,\s*0\s*\)|#0000)$/i.test(String(s).replace(/\s+/g, ' ').trim());
    const equiv = (want, got) => {
      const w = String(want || '').trim(), g = String(got || '').trim();
      if (w.toLowerCase() === g.toLowerCase()) return true;
      if (isTransparent(w) && isTransparent(g)) return true;
      // display：block 级元素当 flex/grid 子项时，浏览器会把 inline-* 提升为 block 级
      // （inline-flex → flex、inline-grid → grid、inline-block → block）。
      // 这是 CSS 规范行为，不是样式没生效。
      const BLOCKIFY = { 'inline-flex': 'flex', 'inline-grid': 'grid', 'inline-block': 'block' };
      if (BLOCKIFY[w] === g) return true;
      const a = pxNums(w), b = pxNums(g);
      if (a.length && a.length === b.length) {
        let same = true;
        for (let i = 0; i < a.length; i++) {
          if (Math.abs(a[i] - b[i]) > 0.02) { same = false; break; }
        }
        if (same) return true;
      }
      // 纯关键字值（如 transparent / none）退化为包含判断
      if (!a.length && !b.length) {
        return g.includes(w) || (w === 'none' && g === 'none');
      }
      return false;
    };

    const failures = [];
    let checked = 0;

    // 把值丢进一个探针元素，让浏览器把它规范化成与 getComputedStyle 同一种写法。
    // 这一步能一次性解决三类假阳性：命名色 white ↔ rgb(255,255,255)、
    // color-mix(…) ↔ color(srgb …)、box-shadow 被补全 0px 或重排。
    const probe = document.createElement('div');
    probe.style.cssText = 'position:absolute;left:-9999px;top:0;width:1px;height:1px';
    document.body.appendChild(probe);
    const canon = (prop, val) => {
      try {
        probe.style.cssText = 'position:absolute;left:-9999px;top:0;width:1px;height:1px';
        probe.style.setProperty(prop, val);
        return getComputedStyle(probe).getPropertyValue(prop).trim();
      } catch { return ''; }
    };

    for (const { cls, prop, value } of rules) {
      const el = document.querySelector('[class~="' + cls.replace(/"/g, '\\"') + '"]');
      if (!el) continue;
      const got = getComputedStyle(el).getPropertyValue(prop);
      let want = value;
      // 解析值里嵌的 var(--token)（可能还带 fallback）
      if (want.includes('var(')) {
        want = want.replace(/var\((--[\w-]+)(?:,\s*([^)]*))?\)/g, (_, name, fb) =>
          rootCs.getPropertyValue(name).trim() || (fb || '').trim());
      }
      checked++;
      if (equiv(want, got) || canon(prop, want) === got) continue;
      failures.push({ cls, prop, want: String(want).slice(0, 90), got: String(got).slice(0, 90) });
    }
    probe.remove();
    return { checked, failures };
  });
}

/**
 * coverageAudit — 找出「长得像工具类、但页面里根本没有对应规则」的 class。
 *
 * 为什么必须查：JS 里用变量/字符串常量拼出的类（例如
 * `body += '<tr class="records-row ' + cls + '">'`，cls 是常量数组里的值）
 * **不会**被 build_ports 的 @classes 机制收集到，于是 CSS 静默缺失、
 * 元素看起来"没样式"，但截图和 JS 报错都发现不了。
 * 静态提取必然有这种漏网之鱼，所以在渲染后用真实 DOM 反查一遍。
 */
async function coverageAudit(page) {
  return page.evaluate(() => {
    // 「像工具类」的前缀集合。刻意收窄：只覆盖 Twsubset 会认的那些，
    // 避免把 port-* / group/* / is-* 这类语义钩子误判。
    const UTIL = /^(bg|text|border|fill|stroke|divide|ring|outline|decoration|accent|caret|placeholder|shadow|rounded|p[xytrblse]?|m[xytrblse]?|gap|space|inset|top|right|bottom|left|start|end|w|h|size|min|max|flex|grid|inline|items|justify|self|place|content|overflow|whitespace|break|truncate|select|pointer|cursor|resize|font|leading|tracking|opacity|z|order|rotate|scale|translate|skew|transition|duration|delay|ease|animate|brightness|contrast|saturate|grayscale|invert|sepia|blur|col|row|aspect|columns|line|table|list|touch|object|backdrop|will|appearance|antialiased|italic|underline|uppercase|lowercase|capitalize|normal|visible|invisible|collapse|isolate|static|absolute|relative|fixed|sticky|sr|not-sr)-/;
    const EXACT = new Set([
      'flex', 'grid', 'block', 'inline', 'hidden', 'contents', 'table', 'flow-root',
      'absolute', 'relative', 'fixed', 'sticky', 'static', 'isolate', 'grow', 'shrink',
      'truncate', 'invisible', 'visible', 'underline', 'italic', 'antialiased',
      'uppercase', 'lowercase', 'capitalize', 'transform', 'border', 'rounded',
      'tabular-nums', 'border-collapse', 'border-separate', 'table-fixed', 'table-auto',
      'appearance-none', 'resize-none', 'pointer-events-none', 'pointer-events-auto',
      'select-none', 'select-text', 'will-change-transform', 'backface-hidden',
      'box-decoration-clone', 'box-decoration-slice', 'touch-none', 'touch-auto',
      'object-cover', 'object-contain', 'object-center', 'bg-clip-text', 'bg-none',
      'bg-cover', 'bg-contain', 'bg-center', 'bg-fixed', 'bg-local', 'bg-scroll',
      'bg-no-repeat', 'bg-repeat', 'transform-none', 'text-center', 'text-left',
      'text-right', 'text-start', 'text-end', 'align-middle', 'align-top', 'align-bottom',
      'line-clamp-none', 'isolate-auto',
    ]);
    const looksLikeUtil = (c) => UTIL.test(c) || EXACT.has(c);

    // 收集页面里所有已存在的规则：生成的 `[class~="X"]` + 自定义 CSS 的 `.X`
    const generated = new Set();
    const defined = new Set();
    for (const sheet of Array.from(document.styleSheets)) {
      let list;
      try { list = sheet.cssRules; } catch { continue; }
      const walk = (rs) => {
        for (const r of Array.from(rs || [])) {
          if (r.cssRules && r.cssRules.length) { walk(r.cssRules); continue; }
          if (!r.selectorText) continue;
          for (const m of r.selectorText.matchAll(/\[class~="([^"]+)"\]/g)) generated.add(m[1]);
          for (const m of r.selectorText.matchAll(/\.([A-Za-z_][\w-]*)/g)) defined.add(m[1]);
        }
      };
      walk(list);
    }

    const used = new Set();
    document.querySelectorAll('*').forEach((el) => {
      const raw = el.getAttribute('class');
      if (raw) raw.split(/\s+/).forEach((c) => c && used.add(c));
    });

    const missing = [];
    used.forEach((c) => {
      if (generated.has(c) || defined.has(c)) return;
      if (!looksLikeUtil(c)) return;
      missing.push(c);
    });
    return { missing: Array.from(new Set(missing)).sort(), usedCount: used.size };
  });
}

async function main() {
  const { chromium } = loadPlaywright();
  fs.mkdirSync(SHOT_DIR, { recursive: true });

  const files = fs.readdirSync(HTML_DIR).filter((f) => f.endsWith('.html'));
  const targets = ONLY ? files.filter((f) => f.startsWith(ONLY)) : files;
  if (!targets.length) {
    console.log('[verify] 没有可验证的文件');
    return 0;
  }

  const browser = await chromium.launch();
  let bad = 0;

  for (const f of targets) {
    const slug = f.replace(/\.html$/, '');
    const page = await browser.newPage({
      viewport: { width: 760, height: 560 },
      deviceScaleFactor: SCALE,
    });
    const errors = [];
    // 离线校验时字体等外部请求被主动 abort，浏览器会记一条 ERR_FAILED，
    // 属于预期噪声，不计入失败。
    const IGNORE = /ERR_FAILED|Failed to load resource|ERR_INTERNET_DISCONNECTED|ERR_NAME_NOT_RESOLVED|fonts\.googleapis|fonts\.gstatic/i;
    page.on('console', (m) => {
      if (m.type() === 'error' && !IGNORE.test(m.text())) errors.push(m.text());
    });
    page.on('pageerror', (e) => errors.push('pageerror: ' + e.message));

    const url = 'file:///' + path.join(HTML_DIR, f).replace(/\\/g, '/');

    // 拦掉一切非 file:// 请求（主要是 Google Fonts）。
    // 两个作用：① 断言「离线可用」这个承诺；② 避免无网络时 load 事件永不触发而超时。
    await page.route('**/*', (route) => {
      const u = route.request().url();
      if (u.startsWith('file://') || u.startsWith('data:')) return route.continue();
      return route.abort();
    });

    await page.goto(url, { waitUntil: 'domcontentloaded' });
    // 等自身动画跑起来（多数组件有一次性入场动画与定时器）
    await page.waitForTimeout(1200);

    // 一组探针：确认令牌层真的生效（不是靠浏览器默认样式蒙对）
    const probe = await page.evaluate(() => {
      const cs = getComputedStyle(document.documentElement);
      const bodyCs = getComputedStyle(document.body);
      const stage = document.querySelector('.port-stage');
      const inspect = (el) => (el ? {
        w: Math.round(el.getBoundingClientRect().width),
        h: Math.round(el.getBoundingClientRect().height),
      } : null);
      // 找出页面里第一个带 class 的真实组件元素，用于判断有没有尺寸
      const firstHtml = document.querySelector('.port-frame > *:not(.port-note):not(.port-variants)');
      return {
        accent: cs.getPropertyValue('--accent').trim(),
        easeStrong: cs.getPropertyValue('--ease-out-strong').trim(),
        shadowLg: cs.getPropertyValue('--shadow-lg').trim().slice(0, 24),
        fontSans: cs.getPropertyValue('--font-sans').trim().slice(0, 30),
        bodyBg: bodyCs.backgroundColor,
        bodyFont: bodyCs.fontFamily.slice(0, 24),
        stageBox: inspect(stage),
        firstBox: inspect(firstHtml),
        dark: document.documentElement.classList.contains('dark'),
      };
    });

    const audit = await styleAudit(page);
    const cov = await coverageAudit(page);

    const problems = [];
    if (errors.length) problems.push('JS 错误 ' + errors.length + ' 条');
    if (!probe.accent) problems.push('--accent 缺失');
    if (!probe.easeStrong) problems.push('--ease-out-strong 缺失');
    if (!probe.shadowLg) problems.push('--shadow-lg 缺失');
    if (!probe.stageBox || probe.stageBox.h < 100) problems.push('舞台高度异常');
    if (!probe.firstBox || probe.firstBox.w === 0) problems.push('组件宽度为 0');
    if (audit.failures.length) problems.push(`样式未生效 ${audit.failures.length} 处`);
    if (cov.missing.length) problems.push(`缺 CSS 的类 ${cov.missing.length} 个`);

    await page.screenshot({
      path: path.join(SHOT_DIR, `${slug}.light.png`),
      fullPage: true,
    });
    // 再截一张暗色，验证 .dark 令牌整组切换
    await page.evaluate(() => document.documentElement.classList.add('dark'));
    await page.waitForTimeout(350);
    await page.screenshot({
      path: path.join(SHOT_DIR, `${slug}.dark.png`),
      fullPage: true,
    });

    const ok = problems.length === 0;
    if (!ok) bad++;
    console.log(
      `[verify] ${ok ? 'OK  ' : 'FAIL'} ${slug.padEnd(20)} ` +
      `stage=${probe.stageBox ? probe.stageBox.w + 'x' + probe.stageBox.h : '-'} ` +
      `first=${probe.firstBox ? probe.firstBox.w + 'x' + probe.firstBox.h : '-'} ` +
      `accent=${probe.accent ? 'y' : 'n'} ease=${probe.easeStrong ? 'y' : 'n'} ` +
      `css=${audit.checked - audit.failures.length}/${audit.checked} ` +
      `cls=${cov.usedCount - cov.missing.length}/${cov.usedCount} ` +
      (problems.length ? '| ' + problems.join('; ') : '')
    );
    if (errors.length) errors.slice(0, 5).forEach((e) => console.log('        ! ' + e));
    audit.failures.slice(0, 8).forEach((f) =>
      console.log(`        css ! [${f.cls}] ${f.prop}: 期望 ${f.want}，实际 ${f.got}`));
    if (cov.missing.length) {
      console.log(`        cls ! 页面用到但没有 CSS 的类：${cov.missing.join(', ')}`);
    }

    await page.close();
  }

  await browser.close();
  // 只打印相对路径：绝对路径会被 self_test.py 抄进报告，把本机用户名带给别人
  console.log(`[verify] 截图输出: ${path.relative(SKILL, SHOT_DIR) || SHOT_DIR}`);
  console.log(`[verify] 失败 ${bad} / ${targets.length}`);
  return bad === 0 ? 0 : 1;
}

main().then((c) => process.exit(c)).catch((e) => {
  console.error(e);
  process.exit(1);
});
