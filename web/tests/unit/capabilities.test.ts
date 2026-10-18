import { describe, expect, it } from 'vitest';
import type { SetupAction } from '../../src/lib/types';
import { canRunAction, getActionSupport } from '../../src/lib/capabilities';

const action = (kind: SetupAction['kind'], support?: SetupAction['support']): SetupAction => ({
  id: `test-${kind}`,
  label: 'fixture action',
  kind,
  support: support ?? {},
});

describe('getActionSupport', () => {
  it.each(['web', 'download'] as const)(
    'keeps %s actions available even when the host OS is unknown',
    (kind) => {
      expect(getActionSupport(action(kind), 'unknown')).toEqual({
        status: 'supported',
        reason: expect.any(String),
      });
    },
  );

  it('uses the documented per-platform reason for a conditional local action', () => {
    const localAction = action('local-build', {
      macos: { status: 'conditional', reason: 'Xcode와 signing 설정이 필요합니다.' },
    });

    expect(getActionSupport(localAction, 'macos')).toEqual({
      status: 'conditional',
      reason: 'Xcode와 signing 설정이 필요합니다.',
    });
  });

  it('fails closed for a local action with no evidence for the selected platform', () => {
    const localAction = action('local-install', {
      windows: { status: 'conditional', reason: '지원 버전의 Node.js가 필요합니다.' },
    });

    expect(getActionSupport(localAction, 'android').status).toBe('unverified');
    expect(getActionSupport(localAction, 'unknown').status).toBe('unverified');
  });

  it('does not display a declared local capability for the unknown platform', () => {
    const localAction = action('local-install', {
      unknown: { status: 'supported', reason: 'stale or malformed support data' },
    });

    expect(getActionSupport(localAction, 'unknown')).toEqual({
      status: 'unverified',
      reason: '기기 OS를 확인하지 못해 로컬 실행 경로를 보장할 수 없습니다.',
    });
  });
});

describe('canRunAction', () => {
  it('allows conditional desktop actions while the UI displays their prerequisite', () => {
    const localAction = action('local-browser', {
      macos: { status: 'conditional', reason: 'Playwright browser binary를 설치해야 합니다.' },
    });

    expect(canRunAction(localAction, 'macos')).toBe(true);
  });

  it.each(['unsupported', 'unverified'] as const)(
    'disables local actions marked %s',
    (status) => {
      const localAction = action('local-install', {
        windows: { status, reason: '이 경로의 호스트 지원이 확인되지 않았습니다.' },
      });

      expect(canRunAction(localAction, 'windows')).toBe(false);
    },
  );

  it('never enables local execution on an unknown host, even if its fallback data says supported', () => {
    const localAction = action('local-install', {
      unknown: { status: 'supported', reason: 'fixture must not override the unknown-host gate' },
    });

    expect(canRunAction(localAction, 'unknown')).toBe(false);
  });

  it('does not disable cloud links on an unknown host', () => {
    expect(canRunAction(action('web'), 'unknown')).toBe(true);
  });
});
