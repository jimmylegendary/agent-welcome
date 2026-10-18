#!/usr/bin/env node

/**
 * Capture the first viewport of public, official service documentation/pages.
 * This deliberately starts a clean headless browser with no user profile,
 * cookies, local storage, or authenticated state. It never clicks, submits,
 * downloads, or enters credentials. If a page is blocked, try only its listed
 * official documentation fallback; never replace a failed capture with art.
 *
 * Run from web/: node scripts/capture-guides.mjs [guide-id ...]
 * Passing guide IDs refreshes only those image/manifest entries.
 */

import fsSync from 'node:fs';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';
import sharp from 'sharp';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(__dirname, '..');
const outputDir = path.join(webRoot, 'public', 'guides');
const manifestPath = path.join(outputDir, 'manifest.json');
const checkedAt = new Date().toISOString().slice(0, 10);
const requestedIds = process.argv.slice(2);
const localBrowser = process.env.CHROME_BIN || [
  '/usr/bin/google-chrome',
  '/usr/bin/chromium',
  '/usr/bin/chromium-browser',
].find((candidate) => fsSync.existsSync(candidate));

const sources = [
  { id: 'codex', url: 'https://developers.openai.com/codex/', fallbackUrls: ['https://github.com/openai/codex'], kind: 'official-guide' },
  { id: 'openai', url: 'https://developers.openai.com/api/docs/quickstart', fallbackUrls: ['https://developers.openai.com/api/reference/overview', 'https://github.com/openai/openai-python'], kind: 'official-guide' },
  { id: 'openrouter', url: 'https://openrouter.ai/docs/quickstart', fallbackUrls: ['https://openrouter.ai/docs'], kind: 'official-guide' },
  { id: 'node', url: 'https://nodejs.org/en/download', fallbackUrls: ['https://nodejs.org/en'], kind: 'official-guide' },
  { id: 'python', url: 'https://www.python.org/downloads/', fallbackUrls: ['https://docs.python.org/3/using/index.html'], kind: 'official-guide' },
  { id: 'nextjs', url: 'https://nextjs.org/docs/app/getting-started/installation', fallbackUrls: ['https://nextjs.org/docs'], kind: 'official-guide' },
  { id: 'flutter', url: 'https://docs.flutter.dev/install', fallbackUrls: ['https://docs.flutter.dev/'], kind: 'official-guide' },
  { id: 'skills', url: 'https://developers.openai.com/codex/skills/', fallbackUrls: ['https://agentskills.io/home'], kind: 'official-guide' },
  { id: 'supabase', url: 'https://supabase.com/docs/guides/database/functions#create-a-database-function-in-the-dashboard', fallbackUrls: ['https://supabase.com/docs/guides/database/functions', 'https://supabase.com/docs/guides/getting-started/api-keys'], focusSelector: 'h3#create-a-database-function-in-the-dashboard', kind: 'official-guide' },
  { id: 'airtable', url: 'https://airtable.com/developers/web/api/introduction', fallbackUrls: ['https://support.airtable.com/docs/airtable-web-api-using-personal-access-tokens'], kind: 'official-guide' },
  { id: 'firebase', url: 'https://firebase.google.com/docs/admin/setup', fallbackUrls: ['https://firebase.google.com/docs'], kind: 'official-guide' },
  { id: 'n8n', url: 'https://docs.n8n.io/hosting/cloud/', fallbackUrls: ['https://docs.n8n.io/'], kind: 'official-guide' },
  { id: 'vercel', url: 'https://vercel.com/docs/deployments', fallbackUrls: ['https://vercel.com/docs'], kind: 'official-guide' },
  { id: 'github', url: 'https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens', fallbackUrls: ['https://docs.github.com/'], kind: 'official-guide' },
  { id: 'google-play', url: 'https://support.google.com/googleplay/android-developer/answer/6112435?hl=en', fallbackUrls: ['https://play.google.com/console/about/'], kind: 'official-guide' },
  { id: 'app-store', url: 'https://developer.apple.com/help/account/membership/program-enrollment/', fallbackUrls: ['https://developer.apple.com/programs/'], kind: 'official-guide' },
  { id: 'threads', url: 'https://developers.facebook.com/docs/threads/', fallbackUrls: ['https://developers.facebook.com/docs/'], kind: 'official-guide' },
  { id: 'instagram', url: 'https://developers.facebook.com/docs/instagram-platform/', fallbackUrls: ['https://developers.facebook.com/docs/instagram-api/'], kind: 'official-guide' },
  { id: 'gmail', url: 'https://developers.google.com/workspace/gmail/api/quickstart/python', fallbackUrls: ['https://developers.google.com/workspace/gmail/api/auth/scopes', 'https://developers.google.com/gmail/api'], kind: 'official-guide' },
  { id: 'youtube', url: 'https://developers.google.com/youtube/v3/getting-started', fallbackUrls: ['https://developers.google.com/youtube/v3'], kind: 'official-guide' },
  { id: 'google-maps', url: 'https://developers.google.com/maps/get-started', fallbackUrls: ['https://developers.google.com/maps/documentation'], kind: 'official-guide' },
  { id: 'google-drive', url: 'https://developers.google.com/drive/api/quickstart/python', fallbackUrls: ['https://developers.google.com/drive/api/guides/about-sdk'], kind: 'official-guide' },
  { id: 'google-sheets', url: 'https://developers.google.com/sheets/api/quickstart/python', fallbackUrls: ['https://developers.google.com/sheets/api'], kind: 'official-guide' },
  { id: 'google-slides', url: 'https://developers.google.com/slides/api/quickstart/python', fallbackUrls: ['https://developers.google.com/slides'], kind: 'official-guide' },
  { id: 'unity', url: 'https://docs.unity3d.com/6000.0/Documentation/Manual/GettingStartedInstallingUnity.html', fallbackUrls: ['https://unity.com/download'], kind: 'official-guide' },
  { id: 'higgsfield', url: 'https://higgsfield.ai/', fallbackUrls: ['https://higgsfield.ai/blog'], kind: 'public-page' },
  { id: 'shotstack', url: 'https://shotstack.io/docs/guide/', fallbackUrls: ['https://shotstack.io/docs/'], kind: 'official-guide' },
  { id: 'elevenlabs', url: 'https://elevenlabs.io/docs/overview', fallbackUrls: ['https://elevenlabs.io/docs/quickstart'], kind: 'official-guide' },
  { id: 'playwright', url: 'https://playwright.dev/docs/intro', fallbackUrls: ['https://playwright.dev/'], kind: 'official-guide' },
  { id: 'agent-browser', url: 'https://github.com/vercel-labs/agent-browser', fallbackUrls: ['https://agent-browser.dev/'], kind: 'official-guide' },
  { id: 'browserskill', url: 'https://github.com/Tencent/BrowserSkill', fallbackUrls: ['https://github.com/Tencent/BrowserSkill/tree/main/docs'], kind: 'official-guide' },
  { id: 'jev', url: 'https://docs.typesafe.ai/introduction', fallbackUrls: ['https://typesafe.ai/'], kind: 'official-guide' },
  { id: 'claude', url: 'https://docs.anthropic.com/en/docs/claude-code/overview', fallbackUrls: ['https://docs.anthropic.com/'], kind: 'official-guide' },
  { id: 'prime', url: 'https://github.com/PrimeIntellect-ai/prime-agent/releases/tag/v0.10.0', fallbackUrls: ['https://github.com/PrimeIntellect-ai/prime-agent'], kind: 'official-guide' },
  { id: 'paseo', url: 'https://paseo.sh/docs/', fallbackUrls: ['https://github.com/getpaseo/paseo'], kind: 'official-guide' },
];

const challengePattern = /verify (that )?you are human|checking your browser|access denied|unusual traffic|captcha|just a moment\.\.\./i;
const loginPattern = /\/(login|log-in|signin|sign-in|oauth)(\/|\?|$)/i;
const sourceIds = new Set(sources.map((source) => source.id));
const unknownIds = requestedIds.filter((id) => !sourceIds.has(id));
if (unknownIds.length) throw new Error(`Unknown guide ID(s): ${unknownIds.join(', ')}`);
if (new Set(requestedIds).size !== requestedIds.length) throw new Error('Guide IDs must not be repeated.');
const selectedSources = requestedIds.length
  ? sources.filter((source) => requestedIds.includes(source.id))
  : sources;

function isChallenge(title, bodyText, status) {
  if ([401, 403, 429].includes(status)) return true;
  if (/just a moment|access denied|security check/i.test(title)) return true;
  return bodyText.length < 1800 && challengePattern.test(bodyText);
}

async function captureUrl(page, url, id, focusSelector) {
  const response = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 18_000 });
  await page.waitForTimeout(700);
  await page.waitForFunction(() => (document.body?.innerText?.trim().length ?? 0) > 35, null, { timeout: 4_000 }).catch(() => {});
  if (focusSelector) {
    await page.locator(focusSelector).scrollIntoViewIfNeeded({ timeout: 4_000 }).catch(() => {});
  } else {
    await page.evaluate(() => window.scrollTo(0, 0));
  }

  const actualUrl = page.url();
  const title = await page.title().catch(() => '');
  const bodyText = await page.locator('body').innerText({ timeout: 3_000 }).catch(() => '');
  const status = response?.status() ?? 0;

  if (status >= 400 || !title.trim() || bodyText.trim().length < 35 || isChallenge(title, bodyText, status) || loginPattern.test(new URL(actualUrl).pathname)) {
    return { ok: false, url: actualUrl, title, status, note: status >= 400 ? `HTTP ${status}` : 'blocked, login redirect, or page did not render public content' };
  }

  const png = await page.screenshot({ type: 'png', animations: 'disabled', timeout: 12_000 });
  const screenshotPath = path.join(outputDir, `${id}.webp`);
  await sharp(png)
    .resize({ width: 1280, height: 800, fit: 'inside', withoutEnlargement: true })
    .webp({ quality: 78, effort: 4 })
    .toFile(screenshotPath);

  return { ok: true, url: actualUrl, title: title.trim(), status, screenshotPath };
}

async function main() {
  await fs.mkdir(outputDir, { recursive: true });
  const mergedEntries = new Map();
  if (requestedIds.length) {
    const previousManifest = JSON.parse(await fs.readFile(manifestPath, 'utf8'));
    if (previousManifest.schemaVersion !== 1 || !Array.isArray(previousManifest.entries)) {
      throw new Error('Selective capture needs an existing schemaVersion 1 manifest.');
    }
    for (const entry of previousManifest.entries) mergedEntries.set(entry.id, entry);
    const missingIds = sources.map((source) => source.id).filter((id) => !mergedEntries.has(id));
    if (missingIds.length) throw new Error(`Existing manifest is missing guide ID(s): ${missingIds.join(', ')}`);
  }

  const browser = await chromium.launch({
    headless: true,
    ...(localBrowser ? { executablePath: localBrowser } : {}),
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
  });
  const entries = [];

  try {
    for (const source of selectedSources) {
      const context = await browser.newContext({
        viewport: { width: 1440, height: 900 },
        deviceScaleFactor: 1,
        locale: 'en-US',
        timezoneId: 'UTC',
        colorScheme: 'light',
      });
      const page = await context.newPage();
      const candidates = [source.url, ...source.fallbackUrls];
      let captured = null;
      let lastFailure = null;

      for (const [index, url] of candidates.entries()) {
        try {
          const result = await captureUrl(page, url, source.id, source.focusSelector);
          if (result.ok) {
            captured = { ...result, usedFallback: index > 0 };
            break;
          }
          lastFailure = result;
        } catch (error) {
          lastFailure = {
            url,
            title: '',
            status: 0,
            note: error instanceof Error ? error.message.split('\n')[0].slice(0, 240) : String(error).slice(0, 240),
          };
        }
      }

      await page.close().catch(() => {});
      await context.close().catch(() => {});

      const screenshot = captured ? `/guides/${source.id}.webp` : null;
      if (!captured) await fs.rm(path.join(outputDir, `${source.id}.webp`), { force: true });
      const title = captured?.title || lastFailure?.title || source.id;
      const finalUrl = captured?.url || lastFailure?.url || source.url;
      const kind = source.kind;
      const result = captured ? (captured.usedFallback ? 'fallback' : 'captured') : 'failed';
      const entry = {
        id: source.id,
        requestedUrl: source.url,
        sourceUrl: finalUrl,
        url: finalUrl,
        title,
        capturedAt: checkedAt,
        result,
        screenshot,
        kind,
        alt: `${title} 공식 공개 페이지의 첫 화면. 새 비인증 브라우저에서 캡처함.`,
        caption: `공식 공개 ${kind === 'public-page' ? '서비스 페이지' : '안내 페이지'} 캡처 · ${checkedAt} · ${title}`,
        httpStatus: captured?.status ?? lastFailure?.status ?? null,
        ...(captured?.usedFallback ? { note: `기본 URL을 렌더링하지 못해 공식 공개 대체 페이지를 사용함 (기본: ${source.url})` } : {}),
        ...(!captured ? { note: lastFailure?.note || 'No official public page rendered successfully.' } : {}),
      };
      entries.push(entry);
      mergedEntries.set(entry.id, entry);
      console.log(`${source.id}: ${result} · HTTP ${entry.httpStatus ?? 'n/a'} · ${finalUrl} · ${title}`);
    }
  } finally {
    await browser.close();
  }

  const finalEntries = requestedIds.length
    ? sources.map((source) => mergedEntries.get(source.id))
    : entries;
  const manifest = { schemaVersion: 1, generatedAt: checkedAt, entries: finalEntries };
  await fs.writeFile(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, 'utf8');
  const capturedCount = entries.filter((entry) => entry.screenshot).length;
  console.log(`Manifest: ${path.relative(webRoot, manifestPath)} · ${capturedCount}/${selectedSources.length} selected screenshots; ${finalEntries.length} total entries`);
  if (capturedCount !== selectedSources.length) process.exitCode = 1;
}

await main();
