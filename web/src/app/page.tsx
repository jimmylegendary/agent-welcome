import Link from 'next/link';
import {
  ArrowRight,
  BookOpenCheck,
  Check,
  ChevronDown,
  Compass,
  LockKeyhole,
  Sparkles,
} from 'lucide-react';
import { services, categories, packs } from '@/data/catalog';
import { ServiceCard } from '@/components/service-card';
import { SectionTitle } from '@/components/ui';
import type { ServiceGuide } from '@/lib/types';

const codexGuide = services.find((service) => /codex/i.test(`${service.id} ${service.name}`)) ?? services[0];
const categoryName = (categoryId: ServiceGuide['category']) =>
  categories.find((category) => category.id === categoryId)?.label ?? '가이드';

const starterSteps = [
  {
    number: '01',
    title: '하고 싶은 일을 고르세요',
    body: '개발, 자동화, 콘텐츠처럼 목적에 맞는 시작 경로를 찾습니다.',
    href: '/catalog',
    label: '목적별 가이드 보기',
  },
  {
    number: '02',
    title: '내 기기에서 가능한지 확인하세요',
    body: '운영체제에 맞는 안내와 필요한 조건을 먼저 살펴봅니다.',
    href: '/compatibility',
    label: '환경 지원 확인',
  },
  {
    number: '03',
    title: '한 단계씩 직접 설정하세요',
    body: '공식 사이트에서 계정과 도구를 준비하고, 체크리스트는 내 기록으로 남깁니다.',
    href: codexGuide ? `/guides/${codexGuide.slug}` : '/catalog',
    label: codexGuide ? `${codexGuide.name}부터 시작` : '첫 가이드 열기',
  },
];

export default function HomePage() {
  const featuredGuides = services.filter((service) => service.featured).slice(0, 3);
  const visiblePacks = packs;

  return (
    <div className="home-page">
      <section className="home-hero" aria-labelledby="home-title">
        <div className="home-hero-copy">
          <div className="hero-kicker">
            <span className="hero-kicker-dot" />
            처음 시작하는 분을 위한 안내
          </div>
          <h1 id="home-title">AI 작업실, 오늘 첫 단계를 시작해요.</h1>
          <p>
            어떤 도구를 골라야 할지부터 내 기기에 맞는 설정까지,
            <br className="desktop-break" />
            복잡한 준비를 이해하기 쉬운 순서로 안내할게요.
          </p>
          <div className="hero-actions">
            <Link
              className="button button-light"
              href={codexGuide ? `/guides/${codexGuide.slug}` : '/catalog'}
            >
              <span>{codexGuide ? `${codexGuide.name}로 시작하기` : '첫 가이드 열기'}</span>
              <ArrowRight size={17} aria-hidden="true" />
            </Link>
            <Link className="hero-quiet-link" href="/catalog">
              전체 가이드 보기
            </Link>
          </div>
        </div>
        <div className="hero-guide-card" aria-label={`${services.length}개의 실제 설정 가이드` }>
          <div className="hero-orbit hero-orbit-one" aria-hidden="true" />
          <div className="hero-orbit hero-orbit-two" aria-hidden="true" />
          <div className="hero-guide-icon" aria-hidden="true">
            <Sparkles size={22} strokeWidth={1.8} />
          </div>
          <p className="hero-guide-label">AGENT WELCOME LIBRARY</p>
          <strong className="hero-guide-count">{services.length}<span>개</span></strong>
          <p className="hero-guide-caption">직접 확인할 수 있는 설정 가이드</p>
          <div className="hero-guide-rule" />
          <div className="hero-guide-foot">
            <span>가입과 결제는 공식 사이트에서</span>
            <Check size={15} strokeWidth={2.4} aria-hidden="true" />
          </div>
        </div>
        <div className="hero-decoration" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
      </section>

      <section className="home-steps" aria-labelledby="start-sequence-title">
        <div className="home-section-intro">
          <p className="eyebrow">처음이라면 이 순서로</p>
          <h2 id="start-sequence-title">시작 순서</h2>
          <p>한 번에 다 설정하지 않아도 괜찮아요. 필요한 것부터 천천히 준비하세요.</p>
        </div>
        <div className="home-step-grid">
          {starterSteps.map((step) => (
            <article className="home-step-card" key={step.number}>
              <span className="step-number">{step.number}</span>
              <div className="home-step-copy">
                <h3>{step.title}</h3>
                <p>{step.body}</p>
              </div>
              <Link className="home-step-link" href={step.href}>
                {step.label} <ArrowRight size={15} aria-hidden="true" />
              </Link>
            </article>
          ))}
        </div>
      </section>

      <section className="home-packs" aria-labelledby="starter-packs-title">
        <SectionTitle
          title="목적에 맞는 시작 경로"
          detail="필요한 서비스와 첫 번째 결과를 함께 살펴보세요."
          action={{ href: '/catalog', label: '가이드 전체 보기' }}
        />
        <div className="starter-pack-grid">
          {visiblePacks.map((pack, index) => {
            const packServices = pack.serviceIds
              .map((id) => services.find((service) => service.id === id))
              .filter((service) => service !== undefined);
            const firstService = packServices[0];
            return (
              <details className={`starter-pack-card starter-pack-${(index % 3) + 1}`} key={pack.id}>
                <summary className="starter-pack-summary">
                  <span className="starter-pack-top">
                    <span className="starter-pack-icon" aria-hidden="true">
                      <Compass size={20} strokeWidth={1.8} />
                    </span>
                    <span className="starter-pack-count">{packServices.length}개 가이드</span>
                  </span>
                  <h3 className="starter-pack-title">{pack.name}</h3>
                  <span className="starter-pack-description">{pack.description}</span>
                  <span className="starter-pack-expand">
                    가이드 순서 보기 <ChevronDown size={15} aria-hidden="true" />
                  </span>
                </summary>
                <div className="starter-pack-expanded">
                  <div className="starter-pack-result">
                    <BookOpenCheck size={16} aria-hidden="true" />
                    <span>첫 결과</span>
                    <strong>{pack.firstResult}</strong>
                  </div>
                  <ol className="starter-pack-route" aria-label={`${pack.name} 가이드 순서`}>
                    {packServices.map((service, serviceIndex) => (
                      <li key={service.id}>
                        <Link href={`/guides/${service.slug}`}>
                          <span>{String(serviceIndex + 1).padStart(2, '0')}</span>
                          <strong>{service.name}</strong>
                          <ArrowRight size={15} aria-hidden="true" />
                        </Link>
                      </li>
                    ))}
                  </ol>
                  <Link
                    className="starter-pack-link"
                    href={firstService ? `/guides/${firstService.slug}` : '/catalog'}
                    aria-label={`${pack.name} 첫 번째 가이드 시작`}
                  >
                    {firstService ? `${firstService.name}부터 시작` : '가이드 전체 보기'}
                    <ArrowRight size={16} aria-hidden="true" />
                  </Link>
                </div>
              </details>
            );
          })}
        </div>
      </section>

      <section className="home-featured" aria-label="바로 시작할 수 있는 가이드">
        <SectionTitle
          title="바로 시작할 수 있는 가이드"
          detail="검증된 공개 자료와 실제 설정 순서를 한곳에서 확인합니다."
          action={{ href: '/catalog', label: `${services.length}개 가이드 살펴보기` }}
        />
        <div className="service-grid home-service-grid">
          {(featuredGuides.length > 0 ? featuredGuides : services.slice(0, 3)).map((service) => (
            <ServiceCard
              key={service.id}
              service={service}
              categoryLabel={categoryName(service.category)}
              compact
            />
          ))}
        </div>
      </section>

      <section className="home-security" aria-label="설정 시 주의할 점">
        <div className="home-security-icon" aria-hidden="true">
          <LockKeyhole size={19} strokeWidth={1.8} />
        </div>
        <div>
          <strong>비밀 키는 공식 서비스 안에서만 관리하세요</strong>
          <p>이 사이트는 API 키, 비밀번호, 결제 정보를 입력받거나 저장하지 않습니다.</p>
        </div>
        <Link href="/compatibility">지원 환경 확인하기 <ArrowRight size={15} aria-hidden="true" /></Link>
      </section>
    </div>
  );
}
