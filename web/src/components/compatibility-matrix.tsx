'use client';

import { useMemo, useState } from 'react';
import Link from 'next/link';
import { ArrowUpRight, CheckCircle2, CircleAlert, CircleHelp, CircleX, Search } from 'lucide-react';
import { canRunAction, getActionSupport } from '@/lib/capabilities';
import { platformLabels } from '@/lib/platform';
import type { Platform, ServiceGuide, SetupAction, SupportStatus } from '@/lib/types';
import { useSetupStore, selectActivePlatform } from '@/store/setup-store';

const platforms: Platform[] = ['macos', 'windows', 'ios', 'android', 'linux', 'unknown'];

const statusLabels: Record<SupportStatus, string> = {
  supported: '진행 가능',
  conditional: '조건부',
  unsupported: '지원 안 함',
  unverified: '확인 필요',
};

const actionKindLabels: Record<SetupAction['kind'], string> = {
  web: '웹',
  download: '다운로드',
  'local-install': '로컬 설치',
  'local-build': '로컬 빌드',
  'local-browser': '로컬 브라우저',
};

function StatusIcon({ status }: { status: SupportStatus }) {
  if (status === 'supported') return <CheckCircle2 size={15} aria-hidden="true" />;
  if (status === 'conditional') return <CircleAlert size={15} aria-hidden="true" />;
  if (status === 'unsupported') return <CircleX size={15} aria-hidden="true" />;
  return <CircleHelp size={15} aria-hidden="true" />;
}

function PlatformCell({ action, platform, selected }: { action: SetupAction; platform: Platform; selected: boolean }) {
  const support = getActionSupport(action, platform);
  const allowed = canRunAction(action, platform);
  return (
    <td className={selected ? 'is-selected-platform' : undefined}>
      <div className={`matrix-status status-${support.status}`} aria-label={`${platformLabels[platform]}: ${support.reason}`}>
        <span className="matrix-status-label">
          <StatusIcon status={support.status} />
          {statusLabels[support.status]}
        </span>
        <span className="matrix-reason">{support.reason}</span>
        {support.status === 'conditional' && (
          <span className={`matrix-actionability${allowed ? ' can-run' : ''}`}>
            {allowed ? '조건을 확인한 뒤 진행' : '먼저 조건을 충족하세요'}
          </span>
        )}
      </div>
    </td>
  );
}

function PlatformPill({ action, platform, selected }: { action: SetupAction; platform: Platform; selected: boolean }) {
  const support = getActionSupport(action, platform);
  const allowed = canRunAction(action, platform);
  return (
    <div className={`mobile-matrix-cell status-${support.status}${selected ? ' is-selected-platform' : ''}`}>
      <strong>{platformLabels[platform]}</strong>
      <span className="matrix-status-label"><StatusIcon status={support.status} /> {statusLabels[support.status]}</span>
      <span className="matrix-reason">{support.reason}</span>
      {support.status === 'conditional' && (
        <span className={`matrix-actionability${allowed ? ' can-run' : ''}`}>
          {allowed ? '조건을 확인한 뒤 진행' : '먼저 조건을 충족하세요'}
        </span>
      )}
    </div>
  );
}

function ActionRow({ action, selected }: { action: SetupAction; selected: Platform }) {
  return (
    <>
      <tr className="desktop-matrix-row">
        <th scope="row" className="matrix-action-name">
          <strong>{action.label}</strong>
          <span>{actionKindLabels[action.kind]}</span>
        </th>
        {platforms.map((platform) => (
          <PlatformCell key={platform} action={action} platform={platform} selected={platform === selected} />
        ))}
      </tr>
      <tr className="mobile-matrix-row">
        <th scope="row" className="mobile-matrix-action">
          <strong>{action.label}</strong>
          <span>{actionKindLabels[action.kind]}</span>
        </th>
        <td colSpan={platforms.length}>
          <div className="mobile-matrix-grid">
            {platforms.map((platform) => (
              <PlatformPill key={platform} action={action} platform={platform} selected={platform === selected} />
            ))}
          </div>
        </td>
      </tr>
    </>
  );
}

function ServiceMatrix({ service, selected }: { service: ServiceGuide; selected: Platform }) {
  const actions = service.actions;
  if (actions.length === 0) return null;

  return (
    <section className="service-matrix" aria-labelledby={`matrix-${service.id}`}>
      <div className="service-matrix-heading">
        <div>
          <h2 id={`matrix-${service.id}`}>{service.name}</h2>
          <p>{service.subtitle}</p>
        </div>
        <Link href={`/guides/${service.slug}`}>가이드 열기 <ArrowUpRight size={13} aria-hidden="true" /></Link>
      </div>
      <div className="matrix-table-scroll" role="region" aria-label={`${service.name} 운영체제별 지원 내용`} tabIndex={0}>
        <table className="matrix-table">
          <caption className="visually-hidden">{service.name}의 작업별 운영체제 지원 상태와 근거</caption>
          <thead>
            <tr>
              <th scope="col">작업</th>
              {platforms.map((platform) => (
                <th key={platform} scope="col" className={platform === selected ? 'is-selected-platform' : undefined}>
                  {platformLabels[platform]}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {actions.map((action) => <ActionRow key={action.id} action={action} selected={selected} />)}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export function CompatibilityMatrix({ services, categories }: { services: ServiceGuide[]; categories: { id: string; label: string }[] }) {
  const selectedPlatform = useSetupStore(selectActivePlatform);
  const [query, setQuery] = useState('');
  const [categoryId, setCategoryId] = useState('all');
  const normalizedQuery = query.trim().toLocaleLowerCase('ko-KR');

  const filtered = useMemo(() => services.filter((service) => {
    if (categoryId !== 'all' && service.category !== categoryId) return false;
    if (!normalizedQuery) return true;
    return `${service.name} ${service.subtitle} ${service.description} ${service.actions.map((action) => action.label).join(' ')}`
      .toLocaleLowerCase('ko-KR')
      .includes(normalizedQuery);
  }), [categoryId, normalizedQuery, services]);

  return (
    <div className="compatibility-matrix">
      <div className="compatibility-tools">
        <label className="search-control compatibility-search">
          <Search size={18} aria-hidden="true" />
          <span className="visually-hidden">환경 표 검색</span>
          <input
            aria-label="환경 표 검색"
            type="search"
            placeholder="서비스나 작업 이름 검색"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>
        <label className="category-filter">
          <span className="visually-hidden">환경 표 주제</span>
          <select aria-label="환경 표 주제" value={categoryId} onChange={(event) => setCategoryId(event.target.value)}>
            <option value="all">모든 주제</option>
            {categories.map((category) => <option key={category.id} value={category.id}>{category.label}</option>)}
          </select>
        </label>
      </div>
      <p className="matrix-result-count" role="status" aria-live="polite">{filtered.length}개 서비스 · {selectedPlatform === 'unknown' ? '운영체제 확인 필요' : `${platformLabels[selectedPlatform]} 기준 강조`}</p>
      <div className="service-matrix-list">
        {filtered.length > 0 ? filtered.map((service) => (
          <ServiceMatrix key={service.id} service={service} selected={selectedPlatform} />
        )) : <p className="matrix-empty">조건에 맞는 서비스가 없습니다. 검색어를 바꿔 보세요.</p>}
      </div>
    </div>
  );
}
