import { expect, test } from '@playwright/test';

test('home presents the first setup steps and the real guide library', async ({ page }) => {
  await page.goto('/');

  await expect(
    page.getByRole('heading', { level: 1, name: 'AI 작업실, 오늘 첫 단계를 시작해요.' }),
  ).toBeVisible();
  await expect(page.getByRole('heading', { name: '시작 순서' })).toBeVisible();
  await expect(page.getByRole('link', { name: '가이드 둘러보기' })).toHaveAttribute('href', '/catalog');
});

test('catalog search opens the matching OpenRouter guide', async ({ page }) => {
  await page.goto('/catalog');

  await page.getByRole('searchbox', { name: '가이드 검색' }).fill('OpenRouter');
  const guideLink = page.getByRole('link', { name: /OpenRouter/i }).first();
  await expect(guideLink).toBeVisible();
  await guideLink.click();

  await expect(page).toHaveURL(/\/guides\//);
  await expect(page.getByRole('heading', { level: 1, name: /OpenRouter/i })).toBeVisible();
  await page.getByRole('link', { name: 'API key와 credits 열기' }).first().click();
  await expect(page).toHaveURL(/#action-openrouter-keys$/);
});

test('category filter keeps only guides in the selected topic', async ({ page }) => {
  await page.goto('/catalog');
  await page.getByRole('combobox', { name: '카테고리' }).selectOption('development');
  await page.getByRole('searchbox', { name: '가이드 검색' }).fill('Node.js + npm');

  await expect(page.getByRole('link', { name: /Node\.js/i }).first()).toBeVisible();
  await expect(page.locator('.catalog-results-bar [role="status"]')).toContainText('1개 가이드');
});

test('manual operating system choice persists across reloads', async ({ page }) => {
  await page.goto('/');

  const platform = page.getByRole('combobox', { name: '운영체제 선택' });
  await platform.selectOption('windows');
  await expect(platform).toHaveValue('windows');
  await page.reload();
  await expect(page.getByRole('combobox', { name: '운영체제 선택' })).toHaveValue('windows');

  const savedState = await page.evaluate(() => localStorage.getItem('agent-welcome-simple-mode'));
  expect(savedState).toContain('platformOverride');
  expect(savedState).not.toMatch(/api.?key|secret|token|credential/i);
  const parsedState = JSON.parse(savedState ?? '{}');
  expect(Object.keys(parsedState.state).sort()).toEqual(['completedGuideStepIds', 'platformOverride']);
});

test('malformed local state still enables manual setup and checklist controls', async ({ page }) => {
  await page.goto('/');
  await page.evaluate(() => localStorage.setItem('agent-welcome-simple-mode', '{malformed'));
  await page.reload();

  const platform = page.getByRole('combobox', { name: '운영체제 선택' });
  await expect(platform).toBeEnabled();
  await platform.selectOption('windows');

  await page.goto('/guides/openrouter');
  const firstStep = page.getByRole('checkbox').first();
  await expect(firstStep).toBeEnabled();
  await page.locator('.step-check-label').first().click();
  await expect(firstStep).toBeChecked();
});

test('unavailable browser storage still allows in-memory setup', async ({ page }) => {
  await page.addInitScript(() => {
    const originalGetItem = Storage.prototype.getItem;
    Storage.prototype.getItem = function (key) {
      if (key === 'agent-welcome-simple-mode') throw new Error('storage unavailable for this test');
      return originalGetItem.call(this, key);
    };
  });
  await page.goto('/');

  const platform = page.getByRole('combobox', { name: '운영체제 선택' });
  await expect(platform).toBeEnabled();
  await platform.selectOption('windows');
  await page.goto('/guides/openrouter');

  const firstStep = page.getByRole('checkbox').first();
  await expect(firstStep).toBeEnabled();
  await page.locator('.step-check-label').first().click();
  await expect(firstStep).toBeChecked();
});

test('guide checklist is a user note that survives reload and can be reset', async ({ page }) => {
  await page.goto('/catalog');
  await page.getByRole('searchbox', { name: '가이드 검색' }).fill('OpenRouter');
  await page.getByRole('link', { name: /OpenRouter/i }).first().click();

  await page.locator('.step-check-label').first().click();
  await page.reload();
  await expect(page.getByRole('checkbox').first()).toBeChecked();
  await expect(page.getByText(/설치나 계정 연결을 확인하는 기능은 아닙니다/)).toBeVisible();

  await page.getByRole('button', { name: '체크리스트 초기화' }).click();
  await expect(page.getByRole('checkbox').first()).not.toBeChecked();
});

test('footer can clear all user-marked checklist progress without changing the OS choice', async ({ page }) => {
  await page.goto('/catalog');
  await page.getByRole('searchbox', { name: '가이드 검색' }).fill('OpenRouter');
  await page.getByRole('link', { name: /OpenRouter/i }).first().click();
  await page.locator('.step-check-label').first().click();
  await page.getByRole('combobox', { name: '운영체제 선택' }).selectOption('windows');

  page.once('dialog', (dialog) => dialog.accept());
  await page.getByRole('button', { name: /체크리스트 기록 지우기/ }).click();

  await expect(page.getByRole('checkbox').first()).not.toBeChecked();
  const savedState = await page.evaluate(() => JSON.parse(localStorage.getItem('agent-welcome-simple-mode') ?? '{}'));
  expect(savedState.state.completedGuideStepIds).toEqual([]);
  expect(savedState.state.platformOverride).toBe('windows');
});

test('unsupported local action stays disabled and keeps its reason visible', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('combobox', { name: '운영체제 선택' }).selectOption('unknown');
  await page.goto('/catalog');
  await page.getByRole('searchbox', { name: '가이드 검색' }).fill('Node.js + npm');
  await page.getByRole('link', { name: /Node\.js/i }).first().click();

  const blockedCard = page.locator('.action-card-blocked').first();
  const blockedAction = blockedCard.getByRole('button').first();
  await expect(blockedAction).toBeDisabled();
  await expect(blockedCard.locator('.action-reason')).toBeVisible();
  await expect(blockedCard.getByRole('link')).toHaveCount(0);
  await expect(page).toHaveURL(/\/guides\//);
});

test('copy action confirms when a supported command is copied', async ({ page }) => {
  await page.goto('/catalog');
  await page.getByRole('searchbox', { name: '가이드 검색' }).fill('Node.js + npm');
  await page.getByRole('link', { name: /Node\.js/i }).first().click();
  await page.getByRole('combobox', { name: '운영체제 선택' }).selectOption('windows');
  await page.context().grantPermissions(['clipboard-read', 'clipboard-write']);

  await page.getByRole('button', { name: /명령어 복사/ }).first().click();
  await expect(page.getByText('복사됨').first()).toBeVisible();
  await expect.poll(() => page.evaluate(() => navigator.clipboard.readText())).toContain('node --version');
});

test('Python virtual environment step copies the selected Windows commands', async ({ page }) => {
  await page.goto('/guides/python');
  await page.getByRole('combobox', { name: '운영체제 선택' }).selectOption('windows');
  await page.context().grantPermissions(['clipboard-read', 'clipboard-write']);

  await page.getByRole('button', { name: /명령어 복사: Project별 venv/ }).click();
  const copied = await page.evaluate(() => navigator.clipboard.readText());
  expect(copied).toContain('py -m venv .venv');
  expect(copied).toContain('Activate.ps1');
  expect(copied).not.toContain('source .venv/bin/activate');
});

test('mobile app release pack reveals every guide in the declared order', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto('/');

  const packs = page.locator('.starter-pack-card');
  await expect(packs).toHaveCount(8);
  const mobilePack = packs.filter({ hasText: '모바일 앱 출시 준비' });
  await expect(mobilePack).toHaveCount(1);
  await mobilePack.locator('summary').click();

  const orderedLinks = mobilePack.locator('.starter-pack-route a');
  await expect(orderedLinks).toHaveCount(6);
  const paths = [];
  for (let index = 0; index < await orderedLinks.count(); index += 1) {
    paths.push(await orderedLinks.nth(index).getAttribute('href'));
  }
  expect(paths).toEqual([
    '/guides/codex',
    '/guides/node',
    '/guides/flutter',
    '/guides/github',
    '/guides/google-play',
    '/guides/app-store',
  ]);

  const dimensions = await page.evaluate(() => ({
    viewport: document.documentElement.clientWidth,
    document: document.documentElement.scrollWidth,
  }));
  expect(dimensions.document).toBeLessThanOrEqual(dimensions.viewport + 1);
});

test('a real local download is available from its guide', async ({ page }) => {
  await page.goto('/catalog');
  await page.getByRole('searchbox', { name: '가이드 검색' }).fill('Supabase');
  await page.getByRole('link', { name: /Supabase/i }).first().click();
  await page.context().grantPermissions(['clipboard-read', 'clipboard-write']);

  const downloadLink = page.getByRole('link', { name: /다운로드/ }).first();
  await expect(downloadLink).toHaveAttribute('download');
  await expect(downloadLink).toHaveAttribute('href', /\/downloads\//);
  await page.getByRole('button', { name: /SQL 복사/ }).first().click();
  await expect(page.getByText('SQL 복사됨').first()).toBeVisible();
  const copiedSql = await page.evaluate(() => navigator.clipboard.readText());
  const sqlHref = await downloadLink.getAttribute('href');
  const sourceSql = await page.evaluate(async (href) => (await fetch(href ?? '')).text(), sqlHref);
  expect(copiedSql).toBe(sourceSql);

  const downloadPromise = page.waitForEvent('download');
  await downloadLink.click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toMatch(/\.sql$/);
  expect(await download.failure()).toBeNull();
});

test('catalog fits a 375px viewport without horizontal page overflow', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto('/catalog');

  const dimensions = await page.evaluate(() => ({
    viewport: document.documentElement.clientWidth,
    document: document.documentElement.scrollWidth,
  }));
  expect(dimensions.document).toBeLessThanOrEqual(dimensions.viewport + 1);
  await expect(page.getByRole('heading', { level: 1, name: '가이드 둘러보기' })).toBeVisible();
});

test('mobile header keeps the brand clear of the OS selector and preserves Korean headline words', async ({ page }) => {
  for (const width of [375, 390]) {
    await page.setViewportSize({ width, height: 812 });
    await page.goto('/');

    const layout = await page.evaluate(() => {
      const brand = document.querySelector('.brand-compact');
      const wordmark = brand?.querySelector('.brand-copy strong');
      const platform = document.querySelector('.platform-picker');
      const headline = document.querySelector('.home-hero h1');
      if (!brand || !wordmark || !platform || !headline) throw new Error('mobile header elements missing');
      return {
        brandRight: brand.getBoundingClientRect().right,
        wordmarkRight: wordmark.getBoundingClientRect().right,
        platformLeft: platform.getBoundingClientRect().left,
        wordmarkText: wordmark.textContent,
        wordBreak: getComputedStyle(headline).wordBreak,
        viewport: document.documentElement.clientWidth,
        documentWidth: document.documentElement.scrollWidth,
      };
    });

    expect(layout.wordmarkText).toBe('Agent Welcome');
    expect(layout.brandRight).toBeLessThanOrEqual(layout.platformLeft);
    expect(layout.wordmarkRight).toBeLessThanOrEqual(layout.platformLeft);
    expect(layout.wordBreak).toBe('keep-all');
    expect(layout.documentWidth).toBeLessThanOrEqual(layout.viewport + 1);
  }
});

test('app responses include the basic security headers', async ({ page }) => {
  const response = await page.goto('/');
  expect(response).not.toBeNull();
  const headers = response?.headers() ?? {};
  expect(headers['x-content-type-options']).toBe('nosniff');
  expect(headers['referrer-policy']).toBe('strict-origin-when-cross-origin');
  expect(headers['x-frame-options']).toBe('DENY');
});

test('model, compatibility, and browser comparison routes render', async ({ page }) => {
  for (const [href, title] of [
    ['/models', '역할별 추천 모델'],
    ['/compatibility', '운영체제 호환성'],
    ['/browser-tools', '브라우저 도구 비교'],
  ]) {
    await page.goto(href);
    await expect(page.getByRole('heading', { level: 1, name: title })).toBeVisible();
  }
});
