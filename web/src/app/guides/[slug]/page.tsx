import Image from 'next/image';
import Link from 'next/link';
import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import {
  ArrowLeft,
  ArrowUpRight,
  CalendarDays,
  CheckCircle2,
  Clock3,
  CreditCard,
  KeyRound,
  Target,
} from 'lucide-react';
import { services, categories } from '@/data/catalog';
import { GuideChecklist, SetupActions } from '@/components/guide-actions';
import { PageHeading, SectionTitle } from '@/components/ui';
import { ServiceCard } from '@/components/service-card';

export const dynamicParams = false;

export function generateStaticParams() {
  return services.map((service) => ({ slug: service.slug }));
}

type GuidePageProps = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: GuidePageProps): Promise<Metadata> {
  const { slug } = await params;
  const service = services.find((candidate) => candidate.slug === slug);
  if (!service) return { title: '가이드를 찾을 수 없습니다' };
  return {
    title: `${service.name} 설정 가이드`,
    description: service.description,
    alternates: { canonical: `/guides/${service.slug}` },
  };
}

export default async function GuidePage({ params }: GuidePageProps) {
  const { slug } = await params;
  const service = services.find((candidate) => candidate.slug === slug);
  if (!service) notFound();

  const categoryLabel = categories.find((category) => category.id === service.category)?.label ?? '가이드';
  const relatedServices = service.relatedIds
    .map((id) => services.find((candidate) => candidate.id === id))
    .filter((candidate) => candidate !== undefined)
    .slice(0, 3);

  return (
    <div className="guide-page">
      <nav className="breadcrumbs" aria-label="현재 위치">
        <Link href="/">시작</Link>
        <span aria-hidden="true">/</span>
        <Link href="/catalog">가이드</Link>
        <span aria-hidden="true">/</span>
        <span aria-current="page">{service.name}</span>
      </nav>

      <header className="guide-intro">
        <div className="guide-intro-main">
          <div className="guide-meta-row">
            <span className="guide-category-label">{categoryLabel}</span>
            <span className="guide-meta-item"><Clock3 size={15} aria-hidden="true" /> 약 {service.estimatedMinutes}분</span>
          </div>
          <PageHeading
            eyebrow="설정 가이드"
            title={service.name}
            description={service.subtitle}
            action={{ href: '/catalog', label: '전체 가이드', back: true }}
          />
          <p className="guide-description">{service.description}</p>
          <div className="guide-tag-list" aria-label="가이드 키워드">
            {service.tags.map((tag) => <span key={tag}>{tag}</span>)}
          </div>
        </div>
        <aside className="guide-outcome-card">
          <div className="guide-outcome-icon" aria-hidden="true"><Target size={19} /></div>
          <p className="eyebrow">이 가이드를 마치면</p>
          <p>{service.outcome}</p>
        </aside>
      </header>

      <div className="guide-layout">
        <div className="guide-content-column">
          <GuideChecklist service={service} />

          <section className="guide-actions-section" aria-labelledby="guide-actions-title">
            <SectionTitle
              id="guide-actions-title"
              title="필요한 사이트와 도구"
              detail="웹사이트는 직접 확인하고, 로컬 작업은 선택한 운영체제 지원을 확인한 뒤 진행하세요."
            />
            <SetupActions actions={service.actions} />
          </section>

          <section className="guide-screenshot-section" aria-labelledby="guide-screenshot-title">
            <SectionTitle
              id="guide-screenshot-title"
              title="화면을 보며 따라가기"
              detail="공개된 공식 페이지를 캡처한 자료입니다. 로그인 후 화면은 포함하지 않았습니다."
            />
            <figure className="guide-screenshot">
              <div className="guide-screenshot-topline">
                <span className="screenshot-kind">{service.screenshot.kind === 'public-page' ? '공개 페이지 캡처' : '공식 가이드 캡처'}</span>
                <a href={service.screenshot.sourceUrl} target="_blank" rel="noopener noreferrer">
                  원문 보기 <ArrowUpRight size={14} aria-hidden="true" />
                </a>
              </div>
              <div className="guide-image-frame">
                <Image
                  src={service.screenshot.src}
                  alt={service.screenshot.alt}
                  width={1280}
                  height={720}
                  sizes="(max-width: 800px) 100vw, 920px"
                  unoptimized
                />
              </div>
              <figcaption>
                <p>{service.screenshot.caption}</p>
                <span><CalendarDays size={14} aria-hidden="true" /> 캡처 날짜: {service.screenshot.capturedAt}</span>
              </figcaption>
            </figure>
          </section>

          <section className="guide-source-section" aria-labelledby="guide-source-title">
            <SectionTitle id="guide-source-title" title="근거와 공식 문서" detail="가격, 모델, 설치 안내는 바뀔 수 있으니 출처의 최신 내용을 확인하세요." />
            <ul className="source-list">
              {service.sources.map((source) => (
                <li key={source.url}>
                  <div>
                    <strong>{source.title}</strong>
                    <span>확인일 {source.checkedAt}</span>
                  </div>
                  <a href={source.url} target="_blank" rel="noopener noreferrer">
                    공식 출처 열기 <ArrowUpRight size={14} aria-hidden="true" />
                  </a>
                </li>
              ))}
            </ul>
          </section>
        </div>

        <aside className="guide-sidebar" aria-label="가이드 요약">
          <div className="guide-facts-card">
            <p className="eyebrow">시작 전에 확인</p>
            <div className="guide-fact">
              <span className="guide-fact-icon" aria-hidden="true"><CreditCard size={17} /></span>
              <div><strong>요금과 결제</strong><p>{service.billing}</p></div>
            </div>
            <div className="guide-fact">
              <span className="guide-fact-icon" aria-hidden="true"><KeyRound size={17} /></span>
              <div><strong>계정과 인증 정보</strong><p>{service.credential}</p></div>
            </div>
            <div className="guide-fact guide-fact-result">
              <span className="guide-fact-icon" aria-hidden="true"><CheckCircle2 size={17} /></span>
              <div><strong>기대할 수 있는 결과</strong><p>{service.outcome}</p></div>
            </div>
          </div>

          <div className="guide-account-note">
            <strong>계정 정보는 본인만 입력하세요</strong>
            <p>비밀번호와 API 키는 공식 서비스 화면에서 직접 관리하고, 이 사이트에는 붙여 넣지 마세요.</p>
          </div>

          {relatedServices.length > 0 && (
            <div className="guide-related">
              <SectionTitle title="함께 보면 좋은 가이드" />
              <div className="guide-related-list">
                {relatedServices.map((related) => (
                  <ServiceCard
                    key={related.id}
                    service={related}
                    categoryLabel={categories.find((category) => category.id === related.category)?.label ?? '가이드'}
                    compact
                  />
                ))}
              </div>
            </div>
          )}
        </aside>
      </div>

      <div className="guide-bottom-return">
        <Link className="button button-secondary" href="/catalog">
          <ArrowLeft size={16} aria-hidden="true" /> 모든 가이드로 돌아가기
        </Link>
      </div>
    </div>
  );
}
