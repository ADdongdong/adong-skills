// 一次性脚本：用 playwright 截 SVG 为 PNG（deviceScaleFactor 3）
const { chromium } = require('C:/Users/10355/.workbuddy/binaries/node/workspace/node_modules/playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({ deviceScaleFactor: 3 });
  const page = await context.newPage();
  const html = process.argv[2];
  const out = process.argv[3];
  const url = 'file:///' + path.resolve(html).replace(/\\/g, '/');
  await page.goto(url);
  await page.waitForSelector('#framework-svg');
  const el = await page.$('#framework-svg');
  await el.screenshot({ path: out, omitBackground: false });
  console.log('saved:', out);
  await browser.close();
})();
