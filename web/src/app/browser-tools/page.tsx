import type { Metadata } from 'next';
import { ArrowUpRight, CheckCircle2, Compass, ShieldAlert } from 'lucide-react';
import { browserTools } from '@/data/catalog';
import { Note, PageHeading } from '@/components/ui';

export const metadata: Metadata = {
  title: '브라우저 자동화 도구 비교',
  description: 'agent-browser, Playwright, BrowserSkill의 역할과 제한을 공식 자료에 따라 비교합니다.',
};

export default function BrowserToolsPage() {
  return (
    <div className="browser-tools-page">
      <PageHeading
        eyebrow="브라우저 작업 준비"
        title="브라우저 도구 비교"
        description="브라우저를 조작하는 방법은 도구마다 다릅니다. 작업 목적과 실행 환경을 확인한 뒤 선택하세요."
      />
      <Note tone="amber">
        <strong>브라우저 자동화는 계정 상태와 별개예요.</strong>
        <p>도구 소개는 로그인, 설치, 권한, 실제 자동화 성공을 의미하지 않습니다. 계정에 접근하는 작업은 공식 약관을 먼저 확인하세요.</p>
      </Note>
      <section className="browser-tool-list" aria-label="브라우저 도구 비교 목록">
        {browserTools.map((tool, index) => (
          <article className={`browser-tool-card browser-tool-${index + 1}`} key={tool.id}>
            <div className="browser-tool-header">
              <span className="browser-tool-icon" aria-hidden="true"><Compass size={21} strokeWidth={1.8} /></span>
              <div>
                <span className="browser-tool-role">{tool.role}</span>
                <h2>{tool.name}</h2>
              </div>
            </div>
            <p className="browser-tool-recommendation">{tool.recommendation}</p>
            <div className="browser-tool-columns">
              <div>
                <h3><CheckCircle2 size={15} aria-hidden="true" /> 잘 맞는 점</h3>
                <p>{tool.strengths}</p>
              </div>
              <div>
                <h3><ShieldAlert size={15} aria-hidden="true" /> 확인할 제한</h3>
                <p>{tool.limits}</p>
              </div>
            </div>
            <a className="browser-tool-source" href={tool.sourceUrl} target="_blank" rel="noopener noreferrer">
              공식 자료 확인 <ArrowUpRight size={15} aria-hidden="true" />
            </a>
          </article>
        ))}
      </section>
    </div>
  );
}
