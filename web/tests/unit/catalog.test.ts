import { describe, expect, it } from 'vitest';
import { browserTools, categories, packs, services } from '../../src/data/catalog';
import { modelProfiles } from '../../src/data/catalog';
import { canRunAction } from '../../src/lib/capabilities';
import type { Platform } from '../../src/lib/types';

const requiredIds = [
  'codex', 'openai', 'openrouter', 'node', 'python', 'nextjs', 'flutter', 'skills',
  'supabase', 'airtable', 'firebase', 'n8n', 'vercel', 'github', 'google-play',
  'app-store', 'threads', 'instagram', 'gmail', 'youtube', 'google-maps',
  'google-drive', 'google-sheets', 'google-slides', 'unity', 'higgsfield',
  'shotstack', 'elevenlabs', 'playwright', 'agent-browser', 'browserskill',
  'jev', 'claude', 'prime', 'paseo',
].sort();

const platforms: Platform[] = ['macos', 'windows', 'ios', 'android', 'linux', 'unknown'];

describe('shared service catalog', () => {
  it('contains every required guide exactly once and keeps each slug addressable', () => {
    expect(services.map(({ id }) => id).sort()).toEqual(requiredIds);
    expect(new Set(services.map(({ id }) => id)).size).toBe(requiredIds.length);
    expect(services.every(({ id, slug }) => id === slug)).toBe(true);
  });

  it('provides distinct, actionable steps and safe links for every service', () => {
    const ids = new Set(services.map(({ id }) => id));

    for (const service of services) {
      expect(service.name.trim(), service.id).not.toBe('');
      expect(service.description.trim().length, service.id).toBeGreaterThan(24);
      expect(service.outcome.trim().length, service.id).toBeGreaterThan(20);
      expect(service.steps.length, service.id).toBeGreaterThanOrEqual(3);
      expect(service.steps.length, service.id).toBeLessThanOrEqual(6);
      expect(new Set(service.steps.map(({ id }) => id)).size, service.id).toBe(service.steps.length);
      expect(new Set(service.steps.map(({ body }) => body)).size, service.id).toBe(service.steps.length);
      expect(service.sources.length, service.id).toBeGreaterThanOrEqual(1);
      expect(service.sources.every(({ url, checkedAt }) => url.startsWith('https://') && /^\d{4}-\d{2}-\d{2}$/.test(checkedAt)), service.id).toBe(true);

      const actionIds = new Set(service.actions.map(({ id }) => id));
      expect(actionIds.size, service.id).toBe(service.actions.length);
      expect(service.steps.every(({ actionId }) => !actionId || actionIds.has(actionId)), service.id).toBe(true);
      expect(service.actions.every(({ href }) => !href || href.startsWith('https://') || href.startsWith('/downloads/')), service.id).toBe(true);
      expect(service.relatedIds.every((id) => ids.has(id)), service.id).toBe(true);

      for (const setupAction of service.actions.filter(({ kind }) => kind.startsWith('local-'))) {
        expect(Object.keys(setupAction.support).sort(), `${service.id}/${setupAction.id}`).toEqual([...platforms].sort());
        expect(platforms.every((platform) => setupAction.support[platform]?.reason.trim()), `${service.id}/${setupAction.id}`).toBe(true);
      }
    }
  });

  it('uses only real guide images and the metadata supplied by the capture manifest', () => {
    for (const service of services) {
      expect(service.screenshot.src, service.id).toBe(`/guides/${service.id}.webp`);
      expect(service.screenshot.sourceUrl, service.id).toMatch(/^https:\/\//);
      expect(service.screenshot.capturedAt, service.id).toMatch(/^2026-10-18$/);
      expect(service.screenshot.alt.trim(), service.id).not.toBe('');
      expect(service.screenshot.caption.trim(), service.id).not.toBe('');
      expect(service.sources.some(({ url }) => url === service.screenshot.sourceUrl), service.id).toBe(true);
    }
  });

  it('keeps the required security and publishing distinctions in the relevant guides', () => {
    const byId = new Map(services.map((service) => [service.id, service]));

    expect(byId.get('google-maps')?.billing).toMatch(/billing|결제/i);
    expect(byId.get('google-maps')?.credential).toMatch(/restrict|제한/i);
    expect(byId.get('gmail')?.credential).toMatch(/OAuth/i);
    expect(byId.get('threads')?.credential).toMatch(/OAuth/i);
    expect(byId.get('instagram')?.credential).toMatch(/Professional|Business|Creator/i);
    expect(byId.get('app-store')?.credential).toMatch(/\.p8/);
    expect(byId.get('app-store')?.actions.some((entry) => entry.kind === 'local-build' && entry.support.macos?.status === 'conditional')).toBe(true);
    expect(byId.get('supabase')?.actions.map(({ href }) => href)).toEqual(expect.arrayContaining([
      '/downloads/supabase-admin-sql-install.sql',
      '/downloads/supabase-admin-sql-check.sql',
      '/downloads/supabase-admin-sql-uninstall.sql',
    ]));
  });

  it('gives beginners platform-correct Python activation, a concrete Codex first task, and a separate Supabase RLS path', () => {
    const byId = new Map(services.map((service) => [service.id, service]));
    const pythonVenv = byId.get('python')?.actions.find(({ id }) => id === 'python-venv');
    expect(pythonVenv?.platformCommands?.windows).toContain('py -m venv .venv');
    expect(pythonVenv?.platformCommands?.windows).toContain('Scripts\\Activate.ps1');
    expect(pythonVenv?.platformCommands?.macos).toContain('python3 -m venv .venv');
    expect(pythonVenv?.platformCommands?.linux).toContain('source .venv/bin/activate');

    const codex = byId.get('codex');
    const firstTaskStep = codex?.steps.find(({ id }) => id === 'first-task');
    const firstTaskAction = codex?.actions.find(({ id }) => id === firstTaskStep?.actionId);
    expect(firstTaskAction?.command).toMatch(/Read README\.md and package\.json/);
    expect(firstTaskAction?.command).toMatch(/do not edit files/i);
    expect(firstTaskStep?.body).toMatch(/project folder|project root/i);

    const supabase = byId.get('supabase');
    const rlsStep = supabase?.steps.find(({ id }) => id === 'test-rls');
    const rlsAction = supabase?.actions.find(({ id }) => id === rlsStep?.actionId);
    const cleanupStep = supabase?.steps.find(({ id }) => id === 'cleanup-admin');
    expect(rlsAction?.href).toBe('https://supabase.com/docs/guides/database/postgres/row-level-security');
    expect(rlsStep?.body).toMatch(/Admin RPC Check는 table RLS나 application connection을 검사하지 않습니다/);
    expect(cleanupStep?.actionId).toBe('supabase-uninstall');
  });

  it('never exposes an iOS IPA build command as a runnable Windows/Linux action', () => {
    const flutter = services.find(({ id }) => id === 'flutter');
    expect(flutter).toBeDefined();
    const ipaActions = flutter!.actions.filter(({ command }) => /flutter build ipa|xcodebuild/i.test(command ?? ''));
    expect(ipaActions.length).toBeGreaterThan(0);
    expect(ipaActions.every((entry) => entry.support.macos?.status === 'conditional')).toBe(true);
    expect(ipaActions.every((entry) => !canRunAction(entry, 'windows') && !canRunAction(entry, 'linux') && !canRunAction(entry, 'android') && !canRunAction(entry, 'ios'))).toBe(true);
    const windowsRunnableFlutterCommands = flutter!.actions
      .filter((entry) => canRunAction(entry, 'windows'))
      .map(({ command }) => command ?? '')
      .join('\n');
    expect(windowsRunnableFlutterCommands).not.toMatch(/flutter build ipa|xcodebuild/i);

    const unity = services.find(({ id }) => id === 'unity');
    expect(unity).toBeDefined();
    const windowsRunnableUnityCommands = unity!.actions
      .filter((entry) => canRunAction(entry, 'windows'))
      .map(({ command }) => command ?? '')
      .join('\n');
    expect(windowsRunnableUnityCommands).not.toMatch(/flutter build ipa|xcodebuild/i);
  });

  it('uses TypeSafe official links and keeps the Jev profile separate from Codex main LLM setup', () => {
    const jev = services.find(({ id }) => id === 'jev');
    const jevModel = modelProfiles.find(({ modelId }) => modelId === 'typesafe/jev-1.13');
    const officialTypeSafeUrl = (value: string) => {
      const hostname = new URL(value).hostname;
      return hostname === 'typesafe.ai' || hostname.endsWith('.typesafe.ai');
    };

    expect(jev).toBeDefined();
    expect(jev!.sources.every(({ url }) => officialTypeSafeUrl(url))).toBe(true);
    expect(jev!.credential).toMatch(/shared|Shared|internal|공유/);
    expect(jev!.credential).toMatch(/Codex.*main LLM/);
    expect(jevModel).toBeDefined();
    expect(officialTypeSafeUrl(jevModel!.sourceUrl)).toBe(true);
    expect(jevModel!.endpoint).toMatch(/decision_models|decision-model/);
  });
});

describe('catalog groupings and integrations', () => {
  it('keeps starter packs linked to existing guides and specifies a concrete first result', () => {
    const ids = new Set(services.map(({ id }) => id));
    expect(packs.length).toBeGreaterThanOrEqual(4);
    for (const pack of packs) {
      expect(pack.serviceIds.length, pack.id).toBeGreaterThanOrEqual(3);
      expect(pack.serviceIds.every((id) => ids.has(id)), pack.id).toBe(true);
      expect(pack.firstResult.trim().length, pack.id).toBeGreaterThan(15);
    }
  });

  it('keeps the primary browser choice, alternatives, and distinct credentialed-browser role visible', () => {
    const ids = new Set(browserTools.map(({ id }) => id));
    expect(ids).toEqual(new Set(['playwright-cli', 'playwright-mcp', 'agent-browser', 'browser-use', 'tencent-browserskill']));
    expect(browserTools.find(({ id }) => id === 'playwright-cli')?.recommendation).toMatch(/기본|추천/);
    expect(browserTools.find(({ id }) => id === 'tencent-browserskill')?.role).toMatch(/로그인|프로필|계정/);
  });

  it('exports sourced profiles for the required text, decision, image, and video roles', () => {
    expect(modelProfiles).toHaveLength(7);
    expect(modelProfiles.map(({ modelId }) => modelId).sort()).toEqual([
      'bytedance/seedance-2.5',
      'deepseek/deepseek-v4.1-flash-1017',
      'google/veo-3.1-lite',
      'qwen/qwen-image-2.1-pro',
      'qwen/qwen-image-2.1-turbo',
      'tencent/hy4-preview',
      'typesafe/jev-1.13',
    ].sort());
    expect(new Set(modelProfiles.map(({ modality }) => modality))).toEqual(new Set(['text', 'image', 'video', 'decision']));
    expect(modelProfiles.every(({ modelId, sourceUrl, verifiedAt }) => modelId.length > 5 && sourceUrl.startsWith('https://') && verifiedAt === '2026-10-18')).toBe(true);
  });

  it('defines each category label once and covers all guides', () => {
    const ids = categories.map(({ id }) => id);
    expect(new Set(ids).size).toBe(ids.length);
    expect(new Set(services.map(({ category }) => category))).toEqual(new Set(ids));
  });
});
