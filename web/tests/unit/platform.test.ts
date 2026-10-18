import { describe, expect, it } from 'vitest';
import { detectPlatform, platformLabels } from '../../src/lib/platform';

describe('detectPlatform', () => {
  it('recognizes iPad desktop-mode Safari before classifying MacIntel as macOS', () => {
    expect(detectPlatform({
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15) AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1',
      platform: 'MacIntel',
      maxTouchPoints: 5,
    })).toBe('ios');
  });

  it.each([
    [{ userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X)', platform: 'iPhone', maxTouchPoints: 5 }, 'ios'],
    [{ userAgent: 'Mozilla/5.0 (Linux; Android 15; Pixel 9)', platform: 'Linux armv8l', maxTouchPoints: 5 }, 'android'],
    [{ userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', platform: 'Win32', maxTouchPoints: 0 }, 'windows'],
    [{ userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 15_0)', platform: 'MacIntel', maxTouchPoints: 0 }, 'macos'],
    [{ userAgent: 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64)', platform: 'Linux x86_64', maxTouchPoints: 0 }, 'linux'],
  ] as const)('detects %s as %s', (signals, expected) => {
    expect(detectPlatform(signals)).toBe(expected);
  });

  it('returns unknown when the browser provides no recognizable platform signals', () => {
    expect(detectPlatform({})).toBe('unknown');
  });
});

describe('platformLabels', () => {
  it('provides a visible uncertainty label for unknown devices', () => {
    expect(platformLabels.unknown).toBe('확인 필요');
  });
});
