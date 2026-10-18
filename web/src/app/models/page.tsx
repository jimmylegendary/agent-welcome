import type { Metadata } from 'next';
import { ArrowUpRight, BadgeDollarSign, CheckCircle2, FileText, Layers3 } from 'lucide-react';
import { PageHeading, Note } from '@/components/ui';
import { modelProfiles } from '@/data/catalog';

export const metadata: Metadata = {
  title: '역할별 추천 모델',
  description: '텍스트, 이미지, 영상, 판단 작업을 맡는 모델과 확인한 가격·라이선스 자료를 살펴봅니다.',
};

const modalityLabels: Record<(typeof modelProfiles)[number]['modality'], string> = {
  text: '텍스트',
  image: '이미지',
  video: '영상',
  decision: '판단',
};

export default function ModelsPage() {
  return (
    <div className="models-page">
      <PageHeading
        eyebrow="작업에 맞는 모델"
        title="역할별 추천 모델"
        description="모델 이름과 ID를 확인하고, 가격과 사용 조건은 공식 출처에서 다시 살펴보세요."
      />
      <Note>
        <strong>모델 ID와 가격은 바뀔 수 있습니다.</strong>
        <p>아래 정보는 표시된 확인일의 공개 자료를 기준으로 정리했습니다. API 키는 각 제공자 콘솔에서 직접 관리하세요.</p>
      </Note>
      <div className="model-grid">
        {modelProfiles.map((profile) => (
          <article className="model-card" key={profile.id}>
            <div className="model-card-top">
              <span className={`model-modality modality-${profile.modality}`}>
                <Layers3 size={14} aria-hidden="true" /> {modalityLabels[profile.modality]}
              </span>
              <span className="model-verified"><CheckCircle2 size={14} aria-hidden="true" /> {profile.verifiedAt} 확인</span>
            </div>
            <p className="model-role">{profile.role}</p>
            <h2>{profile.name}</h2>
            <p className="model-description">{profile.description}</p>
            <dl className="model-facts">
              <div>
                <dt>제공자</dt>
                <dd>{profile.provider}</dd>
              </div>
              <div className="model-id-row">
                <dt>모델 ID</dt>
                <dd><code>{profile.modelId}</code></dd>
              </div>
              {profile.endpoint && (
                <div className="model-endpoint-row">
                  <dt>호출 주소</dt>
                  <dd><code>{profile.endpoint}</code></dd>
                </div>
              )}
            </dl>
            <div className="model-detail-list">
              <div>
                <BadgeDollarSign size={16} aria-hidden="true" />
                <div><strong>가격 참고</strong><p>{profile.pricingNote}</p></div>
              </div>
              <div>
                <FileText size={16} aria-hidden="true" />
                <div><strong>라이선스와 사용 조건</strong><p>{profile.licenseNote}</p></div>
              </div>
            </div>
            <a className="model-source" href={profile.sourceUrl} target="_blank" rel="noopener noreferrer">
              공식 출처에서 다시 확인 <ArrowUpRight size={15} aria-hidden="true" />
            </a>
          </article>
        ))}
      </div>
    </div>
  );
}
