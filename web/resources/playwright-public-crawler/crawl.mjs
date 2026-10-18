import { mkdir, writeFile } from 'node:fs/promises';
import { isIP } from 'node:net';
import { chromium } from 'playwright';

const rawUrl = process.argv[2];
if (!rawUrl) {
  console.error('Usage: npm run crawl -- https://example.com');
  process.exit(2);
}

function parsePublicHttpsUrl(value) {
  const url = new URL(value);
  const host = url.hostname.toLowerCase();
  if (url.protocol !== 'https:') throw new Error('Only HTTPS URLs are accepted.');
  if (url.username || url.password) throw new Error('URL credentials are not accepted.');
  if (isIP(host)) throw new Error('IP-literal URLs are not accepted.');
  if (host === 'localhost' || host.endsWith('.localhost') || host.endsWith('.local') || host.endsWith('.internal')) {
    throw new Error('Local and internal hostnames are not accepted.');
  }
  return url;
}

const target = parsePublicHttpsUrl(rawUrl);
const browser = await chromium.launch({ headless: true });

try {
  const context = await browser.newContext({ serviceWorkers: 'block' });
  const page = await context.newPage();

  await page.route('**/*', async (route) => {
    try {
      const requestUrl = parsePublicHttpsUrl(route.request().url());
      if (requestUrl.origin !== target.origin) return route.abort();
      return route.continue();
    } catch {
      return route.abort();
    }
  });

  const response = await page.goto(target.href, { waitUntil: 'domcontentloaded', timeout: 20_000 });
  if (!response || !response.ok()) {
    throw new Error(`Page request failed (${response?.status() ?? 'no response'}).`);
  }
  if (new URL(page.url()).origin !== target.origin) {
    throw new Error('The page redirected outside the original public origin.');
  }

  const pageData = await page.evaluate(() => {
    const headings = Array.from(document.querySelectorAll('h1,h2,h3'))
      .map((element) => element.textContent?.trim() ?? '')
      .filter(Boolean)
      .slice(0, 100);
    const links = Array.from(document.querySelectorAll('a[href]'))
      .map((element) => ({
        text: element.textContent?.trim().replace(/\s+/g, ' ').slice(0, 300) ?? '',
        href: (element instanceof HTMLAnchorElement ? element.href : ''),
      }))
      .filter((link) => link.text && link.href.startsWith('https://') && new URL(link.href).origin === location.origin)
      .slice(0, 200);
    return {
      title: document.title.slice(0, 500),
      headings,
      links,
      textExcerpt: (document.body?.innerText ?? '').slice(0, 30_000),
    };
  });

  const result = {
    sourceUrl: target.href,
    retrievedAt: new Date().toISOString(),
    ...pageData,
  };
  const rows = [
    ...result.headings.map((text) => ({ kind: 'heading', text, href: '' })),
    ...result.links.map((link) => ({ kind: 'link', text: link.text, href: link.href })),
  ];
  const csvCell = (value) => `"${String(value).replaceAll('"', '""')}"`;
  const csv = [
    ['sourceUrl', 'title', 'retrievedAt', 'kind', 'text', 'href'].map(csvCell).join(','),
    ...rows.map((row) => [result.sourceUrl, result.title, result.retrievedAt, row.kind, row.text, row.href].map(csvCell).join(',')),
  ].join('\n');

  await mkdir('output', { recursive: true });
  await writeFile('output/public-page.json', `${JSON.stringify(result, null, 2)}\n`, 'utf8');
  await writeFile('output/public-page.csv', `${csv}\n`, 'utf8');
  console.log('Saved output/public-page.json and output/public-page.csv');
  await context.close();
} finally {
  await browser.close();
}
