import type { Platform } from './types';

export interface PlatformSignals {
  userAgent?: string;
  platform?: string;
  maxTouchPoints?: number;
}

export const platformLabels: Record<Platform, string> = {
  macos: 'macOS',
  windows: 'Windows',
  ios: 'iOS / iPadOS',
  android: 'Android',
  linux: 'Linux',
  unknown: '확인 필요',
};

/**
 * Suggests the host OS from browser-provided values. It never detects installed
 * runtimes, account access, or credentials; callers must keep manual override.
 */
export function detectPlatform({
  userAgent = '',
  platform = '',
  maxTouchPoints = 0,
}: PlatformSignals): Platform {
  const ua = userAgent.toLowerCase();
  const browserPlatform = platform.toLowerCase();

  if (/iphone|ipad|ipod/.test(ua) || /iphone|ipad|ipod/.test(browserPlatform)) {
    return 'ios';
  }

  // iPadOS may report a desktop Macintosh UA and MacIntel platform.
  if (browserPlatform === 'macintel' && maxTouchPoints > 1 && ua.includes('macintosh')) {
    return 'ios';
  }

  if (ua.includes('android') || browserPlatform.includes('android')) {
    return 'android';
  }

  if (ua.includes('windows') || browserPlatform.startsWith('win')) {
    return 'windows';
  }

  if (ua.includes('macintosh') || ua.includes('mac os') || browserPlatform.startsWith('mac')) {
    return 'macos';
  }

  if (ua.includes('linux') || ua.includes('x11') || browserPlatform.includes('linux')) {
    return 'linux';
  }

  return 'unknown';
}
