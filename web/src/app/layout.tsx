import type { Metadata, Viewport } from 'next';
import type { ReactNode } from 'react';
import { AppShell } from '@/components/app-shell';
import './globals.css';

export const metadata: Metadata = {
  title: {
    default: 'Agent Welcome — AI 작업실 시작 가이드',
    template: '%s · Agent Welcome',
  },
  description:
    '처음 설정하는 AI 도구와 작업실을 한 단계씩 안내합니다. 계정과 API 키는 각 공식 사이트에서 직접 관리하세요.',
  applicationName: 'Agent Welcome',
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#f6f7f2',
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="ko">
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
