import type { Metadata } from 'next';
import { MonitorCheck } from 'lucide-react';
import { CompatibilityMatrix } from '@/components/compatibility-matrix';
import { Note, PageHeading } from '@/components/ui';
import { categories, services } from '@/data/catalog';

export const metadata: Metadata = {
  title: '운영체제 호환성',
  description: '서비스별 웹 작업과 로컬 실행의 운영체제 지원 상태, 조건, 근거를 확인합니다.',
};

export default function CompatibilityPage() {
  return (
    <div className="compatibility-page">
      <PageHeading
        eyebrow="내 기기에서 가능한 작업"
        title="운영체제 호환성"
        description="가입, 웹 문서, 다운로드, 로컬 설치를 구분해 각 작업의 지원 근거와 조건을 확인합니다."
      />
      <Note tone="amber">
        <strong>설치 상태를 자동으로 확인하지 않아요.</strong>
        <p>표시된 지원 여부는 문서 근거입니다. 체크리스트는 내 기록일 뿐, 설치나 계정 연결을 검증하지 않습니다.</p>
      </Note>
      <div className="compatibility-legend" aria-label="호환성 상태 범례">
        <span><MonitorCheck size={16} aria-hidden="true" /> 현재 선택한 운영체제를 강조합니다.</span>
        <span className="legend-supported">진행 가능</span>
        <span className="legend-conditional">조건부 · 먼저 조건 확인</span>
        <span className="legend-blocked">지원 안 함 또는 확인 필요</span>
      </div>
      <CompatibilityMatrix services={services} categories={categories} />
    </div>
  );
}
