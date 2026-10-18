'use client';

import Link from 'next/link';
import { AlertCircle } from 'lucide-react';
import './globals.css';

export default function GlobalError() {
  return (
    <html lang="ko">
      <body>
        <main className="error-page" role="alert">
          <span className="error-icon" aria-hidden="true"><AlertCircle size={22} /></span>
          <p className="eyebrow">Agent Welcome</p>
          <h1>화면을 불러오지 못했어요.</h1>
          <p>잠시 후 다시 열어 주세요.</p>
          <Link className="button button-primary" href="/">시작 화면으로</Link>
        </main>
      </body>
    </html>
  );
}
