'use client';

import Link from 'next/link';
import { AlertCircle, RotateCcw } from 'lucide-react';

export default function ErrorPage({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <section className="error-page" role="alert">
      <span className="error-icon" aria-hidden="true"><AlertCircle size={22} /></span>
      <p className="eyebrow">페이지를 불러오지 못했어요</p>
      <h1>잠시 후 다시 시도해 주세요.</h1>
      <p>문제가 계속되면 시작 화면으로 돌아가 다른 가이드를 열어 보세요.</p>
      <div className="error-actions">
        <button type="button" className="button button-primary" onClick={reset}>
          <RotateCcw size={16} aria-hidden="true" /> 다시 불러오기
        </button>
        <Link className="button button-secondary" href="/">시작 화면으로</Link>
      </div>
    </section>
  );
}
