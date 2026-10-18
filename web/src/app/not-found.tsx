import Link from 'next/link';
import { ArrowLeft, Search } from 'lucide-react';

export default function NotFound() {
  return (
    <section className="not-found-page">
      <span className="not-found-icon" aria-hidden="true"><Search size={22} /></span>
      <p className="eyebrow">페이지를 찾을 수 없습니다</p>
      <h1>주소를 다시 확인해 주세요.</h1>
      <p>요청하신 가이드가 없거나 주소가 바뀌었을 수 있어요.</p>
      <Link className="button button-primary" href="/catalog">
        <ArrowLeft size={16} aria-hidden="true" /> 가이드 둘러보기
      </Link>
    </section>
  );
}
