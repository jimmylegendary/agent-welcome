'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  BookOpen,
  Bot,
  Compass,
  Eraser,
  House,
  Layers3,
  Monitor,
  ShieldCheck,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { detectPlatform, platformLabels } from '@/lib/platform';
import type { Platform } from '@/lib/types';
import { selectActivePlatform, useSetupStore } from '@/store/setup-store';

const primaryNavigation = [
  { href: '/', label: '시작', mobileLabel: '시작', icon: House },
  { href: '/catalog', label: '가이드 둘러보기', mobileLabel: '가이드', icon: BookOpen },
  { href: '/models', label: '추천 모델', mobileLabel: '모델', icon: Layers3 },
  { href: '/compatibility', label: '내 환경', mobileLabel: '환경', icon: Monitor },
  { href: '/browser-tools', label: '브라우저 도구', mobileLabel: '브라우저', icon: Compass },
];

const platformOptions: Platform[] = ['macos', 'windows', 'linux', 'android', 'ios', 'unknown'];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  useEffect(() => {
    let mounted = true;
    const detectedPlatform = detectPlatform({
      userAgent: navigator.userAgent,
      platform: navigator.platform,
      maxTouchPoints: navigator.maxTouchPoints,
    });
    const finishInitialization = () => {
      if (!mounted) return;
      try {
        useSetupStore.getState().completeHydration(detectedPlatform);
      } catch {
        // Zustand updates in-memory state before a storage write can fail.
      }
    };
    try {
      void Promise.resolve(useSetupStore.persist.rehydrate())
        .then(finishInitialization, finishInitialization)
        .catch(finishInitialization);
    } catch {
      finishInitialization();
    }
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    document.getElementById('main-content')?.focus({ preventScroll: true });
  }, [pathname]);

  return (
    <div className="site-shell">
      <a className="skip-link" href="#main-content">
        본문으로 건너뛰기
      </a>
      <aside className="sidebar" aria-label="주 메뉴">
        <Brand />
        <div className="sidebar-eyebrow">작업실</div>
        <Navigation pathname={pathname} mobile={false} />
        <div className="sidebar-spacer" />
        <div className="privacy-note">
          <div className="privacy-note-icon" aria-hidden="true">
            <ShieldCheck size={17} strokeWidth={1.8} />
          </div>
          <div>
            <strong>안전하게 직접 설정</strong>
            <p>API 키와 비밀번호를 이 사이트에 입력하지 않아요.</p>
          </div>
        </div>
        <div className="sidebar-caption">Agent Welcome · Simple Mode</div>
      </aside>

      <div className="workspace">
        <header className="topbar">
          <div className="mobile-brand">
            <Brand compact />
          </div>
          <div className="topbar-context">
            <span className="topbar-overline">Jimmy&apos;s setup desk</span>
            <span className="topbar-title">처음 시작하는 AI 작업실</span>
          </div>
          <PlatformSelector />
        </header>
        <main id="main-content" className="page-main" tabIndex={-1}>
          {children}
        </main>
        <SiteFooter />
      </div>
      <nav className="mobile-nav" aria-label="주 메뉴">
        <Navigation pathname={pathname} mobile />
      </nav>
    </div>
  );
}

function SiteFooter() {
  const completedIds = useSetupStore((state) => state.completedGuideStepIds);
  const resetSteps = useSetupStore((state) => state.resetGuideSteps);
  const [feedback, setFeedback] = useState('');

  function clearChecklist() {
    if (completedIds.length === 0) return;
    const confirmed = window.confirm('이 브라우저에 저장된 모든 체크리스트 표시를 지울까요? 운영체제 선택은 그대로 유지됩니다.');
    if (!confirmed) return;
    resetSteps(completedIds);
    setFeedback('체크리스트 기록을 지웠습니다.');
  }

  return (
    <footer className="site-footer">
      <p>체크리스트와 운영체제 선택은 이 브라우저에만 저장됩니다. 설치나 계정 연결 여부는 확인하지 않습니다.</p>
      <div className="site-footer-actions">
        <span role="status" aria-live="polite">{feedback}</span>
        <button type="button" className="footer-reset" onClick={clearChecklist} disabled={completedIds.length === 0}>
          <Eraser size={15} aria-hidden="true" /> 체크리스트 기록 지우기
        </button>
      </div>
    </footer>
  );
}

function Brand({ compact = false }: { compact?: boolean }) {
  return (
    <Link className={`brand${compact ? ' brand-compact' : ''}`} href="/" aria-label="Agent Welcome 시작 화면">
      <span className="brand-mark" aria-hidden="true">
        <Bot size={19} strokeWidth={1.8} />
      </span>
      <span className="brand-copy">
        <strong>Agent Welcome</strong>
        {!compact && <span>Jimmy&apos;s setup desk</span>}
      </span>
    </Link>
  );
}

function Navigation({ pathname, mobile }: { pathname: string; mobile: boolean }) {
  return (
    <ul className={`navigation${mobile ? ' navigation-mobile' : ''}`}>
      {primaryNavigation.map(({ href, label, mobileLabel, icon: Icon }) => {
        const active = href === '/' ? pathname === '/' : pathname.startsWith(href);
        return (
          <li key={href}>
            <Link
              className={`navigation-link${active ? ' is-active' : ''}`}
              href={href}
              aria-current={active ? 'page' : undefined}
              aria-label={mobile ? label : undefined}
            >
              <Icon size={18} strokeWidth={active ? 2.1 : 1.8} aria-hidden="true" />
              <span>{mobile ? mobileLabel : label}</span>
            </Link>
          </li>
        );
      })}
    </ul>
  );
}

function PlatformSelector() {
  const platformOverride = useSetupStore((state) => state.platformOverride);
  const activePlatform = useSetupStore(selectActivePlatform);
  const setPlatformOverride = useSetupStore((state) => state.setPlatformOverride);
  const detectedPlatform = useSetupStore((state) => state.detectedPlatform);
  const hasHydrated = useSetupStore((state) => state.hasHydrated);

  function updatePlatform(value: string) {
    if (value === 'auto') {
      setPlatformOverride(null);
      return;
    }
    setPlatformOverride(value as Platform);
  }

  return (
    <label className="platform-picker">
      <span className="platform-picker-label">내 운영체제</span>
      <span className="platform-select-wrap">
        <Monitor size={15} strokeWidth={1.8} aria-hidden="true" />
        <select
          aria-label="운영체제 선택"
          value={platformOverride ?? 'auto'}
          disabled={!hasHydrated}
          onChange={(event) => updatePlatform(event.target.value)}
        >
          <option value="auto">자동 감지 · {platformLabels[detectedPlatform]}</option>
          {platformOptions.map((platform) => (
            <option key={platform} value={platform}>
              {platformLabels[platform]}
              {platform === activePlatform && !platformOverride ? ' · 자동 감지' : ''}
            </option>
          ))}
        </select>
      </span>
    </label>
  );
}
