const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({
    args: ['--no-sandbox', '--disable-blink-features=AutomationControlled'],
  });
  const ctx = await browser.newContext({
    viewport: { width: 540, height: 960 },   // narrower viewport so layout wraps mobile-style
    deviceScaleFactor: 2,
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  });
  const page = await ctx.newPage();
  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      await page.goto('https://mahjongatfias.in/', { waitUntil: 'domcontentloaded', timeout: 30000 });
      break;
    } catch (e) {
      console.error(`attempt ${attempt} failed:`, e.message);
      if (attempt === 3) throw e;
      await page.waitForTimeout(3000);
    }
  }
  // wait for images to load
  await page.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => {});
  await page.waitForTimeout(3000);
  await page.screenshot({ path: '03-music/assets/site_mahjongatfias.png', fullPage: true });
  await browser.close();
  console.log('done');
})();
