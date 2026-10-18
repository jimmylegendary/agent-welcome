import { chromium } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';

const [base, destination] = process.argv.slice(2);
if (!base || !destination) throw new Error('Usage: node scripts/capture-preview.mjs BASE_URL OUTPUT_DIRECTORY');
await mkdir(destination, { recursive: true });
const browser = await chromium.launch({
  executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || undefined,
});
try {
  for (const item of [
    { name: 'home-desktop', route: '/', width: 1440, height: 1000 },
    { name: 'guide-desktop', route: '/guides/supabase', width: 1440, height: 1000 },
    { name: 'home-mobile', route: '/', width: 390, height: 844 },
    { name: 'catalog-mobile', route: '/catalog', width: 390, height: 844 },
  ]) {
    const context = await browser.newContext({ viewport: { width: item.width, height: item.height } });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', (error) => errors.push(error.message));
    await page.goto(new URL(item.route, base).href, { waitUntil: 'networkidle' });
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    await page.screenshot({ path: path.join(destination, `${item.name}.png`) });
    console.log(JSON.stringify({ view: item.name, overflow, pageErrors: errors }));
    await context.close();
  }
} finally {
  await browser.close();
}
