'use client';

import { useMemo, useState } from 'react';
import { Search, SlidersHorizontal, X } from 'lucide-react';
import { categories, services } from '@/data/catalog';
import { EmptyState, PageHeading } from '@/components/ui';
import { ServiceCard } from '@/components/service-card';
import type { CategoryId, ServiceGuide } from '@/lib/types';

export default function CatalogPage() {
  const [query, setQuery] = useState('');
  const [categoryId, setCategoryId] = useState<CategoryId | 'all'>('all');
  const normalizedQuery = query.trim().toLocaleLowerCase('ko-KR');

  const filteredServices = useMemo(() => {
    return services.filter((service) => {
      if (categoryId !== 'all' && service.category !== categoryId) return false;
      if (!normalizedQuery) return true;
      const haystack = [service.name, service.subtitle, service.description, ...service.tags]
        .join(' ')
        .toLocaleLowerCase('ko-KR');
      return haystack.includes(normalizedQuery);
    });
  }, [categoryId, normalizedQuery]);

  const categoryLabel = (service: ServiceGuide) =>
    categories.find((category) => category.id === service.category)?.label ?? '가이드';

  function clearFilters() {
    setQuery('');
    setCategoryId('all');
  }

  return (
    <div className="catalog-page">
      <PageHeading
        eyebrow="가이드 라이브러리"
        title="가이드 둘러보기"
        description={`${services.length}개의 실제 서비스 설정을 목적과 이름으로 찾아보세요.`}
      />

      <section className="catalog-tools" aria-label="가이드 검색과 분류">
        <label className="search-control">
          <Search size={19} strokeWidth={1.8} aria-hidden="true" />
          <span className="visually-hidden">가이드 검색</span>
          <input
            type="search"
            aria-label="가이드 검색"
            placeholder="서비스 이름이나 하고 싶은 일을 검색하세요"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          {query && (
            <button type="button" className="clear-search" onClick={() => setQuery('')} aria-label="검색어 지우기">
              <X size={17} aria-hidden="true" />
            </button>
          )}
        </label>
        <label className="category-filter">
          <SlidersHorizontal size={16} aria-hidden="true" />
          <span className="visually-hidden">카테고리</span>
          <select
            aria-label="카테고리"
            value={categoryId}
            onChange={(event) => setCategoryId(event.target.value as CategoryId | 'all')}
          >
            <option value="all">모든 주제</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>{category.label}</option>
            ))}
          </select>
        </label>
      </section>

      <div className="catalog-results-bar">
        <p role="status" aria-live="polite">
          <strong>{filteredServices.length}</strong>개 가이드
          {normalizedQuery && <span> · “{query.trim()}” 검색 결과</span>}
        </p>
        {(query || categoryId !== 'all') && (
          <button type="button" className="clear-filters" onClick={clearFilters}>
            전체 보기 <X size={14} aria-hidden="true" />
          </button>
        )}
      </div>

      {filteredServices.length > 0 ? (
        <div className="service-grid catalog-grid">
          {filteredServices.map((service) => (
            <ServiceCard key={service.id} service={service} categoryLabel={categoryLabel(service)} />
          ))}
        </div>
      ) : (
        <EmptyState
          title="조건에 맞는 가이드가 없어요"
          detail="서비스 이름을 짧게 검색하거나 주제를 전체 보기로 바꿔 보세요."
        />
      )}
    </div>
  );
}
