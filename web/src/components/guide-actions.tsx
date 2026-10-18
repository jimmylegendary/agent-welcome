'use client';

import { useState } from 'react';
import { ArrowUpRight, Check, Clipboard, Download, ExternalLink, Info, ShieldCheck } from 'lucide-react';
import { canRunAction, getActionSupport } from '@/lib/capabilities';
import type { GuideStep, Platform, ServiceGuide, SetupAction } from '@/lib/types';
import { useSetupStore } from '@/store/setup-store';

const localKinds = new Set<SetupAction['kind']>(['local-install', 'local-build', 'local-browser']);

function isLocalAction(action: SetupAction) {
  return localKinds.has(action.kind);
}

function isSafeExternalHref(href: string) {
  return /^https:\/\//i.test(href);
}

function actionStatusLabel(status: ReturnType<typeof getActionSupport>['status']) {
  switch (status) {
    case 'supported':
      return '이 환경에서 진행 가능';
    case 'conditional':
      return '사전 조건 확인 필요';
    case 'unsupported':
      return '이 환경은 지원하지 않음';
    case 'unverified':
      return '지원 여부 확인 필요';
  }
}

function localActionIsAllowed(action: SetupAction, platform: Platform) {
  if (!isLocalAction(action) || platform === 'unknown') return false;
  const support = getActionSupport(action, platform);
  return support.status !== 'unsupported' && support.status !== 'unverified' && canRunAction(action, platform);
}

function CopyButton({
  text,
  label,
  disabled = false,
}: {
  text: string;
  label: string;
  disabled?: boolean;
}) {
  const [message, setMessage] = useState('');

  async function copy() {
    if (disabled) return;
    try {
      if (!navigator.clipboard?.writeText) throw new Error('clipboard unavailable');
      await navigator.clipboard.writeText(text);
      setMessage('복사됨');
    } catch {
      setMessage('복사할 수 없어요. 코드를 선택해 직접 복사해 주세요.');
    }
  }

  return (
    <div className="copy-control">
      <button
        type="button"
        className="button button-copy"
        onClick={copy}
        disabled={disabled}
        aria-label={`명령어 복사: ${label}`}
      >
        <Clipboard size={15} aria-hidden="true" />
        <span>{disabled ? '환경 확인 후 복사' : '명령어 복사'}</span>
      </button>
      <span className="copy-message" role="status" aria-live="polite">
        {message}
      </span>
    </div>
  );
}

function CopySqlButton({ href, label }: { href: string; label: string }) {
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);

  async function copySql() {
    setBusy(true);
    setMessage('');
    try {
      const resourceUrl = new URL(href, window.location.origin);
      if (resourceUrl.origin !== window.location.origin || !resourceUrl.pathname.toLowerCase().endsWith('.sql')) {
        throw new Error('SQL downloads must use a same-origin .sql resource.');
      }
      const response = await fetch(resourceUrl, { credentials: 'omit' });
      if (!response.ok || new URL(response.url).origin !== window.location.origin) {
        throw new Error('The SQL resource could not be loaded safely.');
      }
      const sql = await response.text();
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard access is unavailable.');
      await navigator.clipboard.writeText(sql);
      setMessage('SQL 복사됨');
    } catch {
      setMessage('SQL을 복사하지 못했어요. 파일을 다운로드해 직접 열어 주세요.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="sql-copy-control">
      <button
        type="button"
        className="button button-copy"
        onClick={copySql}
        disabled={busy}
        aria-label={`SQL 복사: ${label}`}
      >
        <Clipboard size={15} aria-hidden="true" />
        <span>{busy ? 'SQL 준비 중' : 'SQL 복사'}</span>
      </button>
      <span className="copy-message" role="status" aria-live="polite">{message}</span>
    </div>
  );
}

export function SetupActionCard({ action, platform }: { action: SetupAction; platform: Platform }) {
  const support = getActionSupport(action, platform);
  const local = isLocalAction(action);
  const allowed = local ? localActionIsAllowed(action, platform) : true;
  const command = action.platformCommands?.[platform] ?? action.command;
  const href = action.href;
  const canOpenHref = Boolean(href) && (!local || allowed) && (!/^https?:\/\//i.test(href ?? '') || isSafeExternalHref(href ?? ''));
  const isExternal = Boolean(href && isSafeExternalHref(href));
  const statusTone = support.status === 'supported' ? 'support-supported' : support.status === 'conditional' ? 'support-conditional' : 'support-blocked';

  return (
    <article id={`action-${action.id}`} className={`action-card${local && !allowed ? ' action-card-blocked' : ''}`}>
      <div className="action-card-header">
        <span className={`action-type-icon ${local ? 'action-type-local' : 'action-type-web'}`} aria-hidden="true">
          {action.kind === 'download' ? <Download size={17} /> : local ? <ShieldCheck size={17} /> : <ExternalLink size={17} />}
        </span>
        <div className="action-card-title">
          <h3>{action.label}</h3>
          <span className={`support-status ${statusTone}`}>
            <span className="support-status-dot" aria-hidden="true" />
            {local ? actionStatusLabel(support.status) : action.kind === 'download' ? '웹에서 안전하게 받기' : '공식 웹사이트 열기'}
          </span>
        </div>
        {canOpenHref && href ? (
          <a
            className="button button-secondary action-open"
            href={href}
            target={isExternal ? '_blank' : undefined}
            rel={isExternal ? 'noopener noreferrer' : undefined}
            download={action.kind === 'download' ? true : undefined}
          >
            <span>{action.kind === 'download' ? '다운로드' : '열기'}</span>
            {action.kind === 'download' ? <Download size={15} aria-hidden="true" /> : <ArrowUpRight size={15} aria-hidden="true" />}
          </a>
        ) : null}
      </div>

      {action.kind === 'download' && href?.startsWith('/') && href.toLowerCase().endsWith('.sql') && (
        <CopySqlButton href={href} label={action.label} />
      )}

      {command && (
        <div className="action-command">
          <pre><code>{command}</code></pre>
          <CopyButton text={command} label={action.label} disabled={local && !allowed} />
        </div>
      )}

      {local && (
        <p className={`action-reason ${support.status === 'conditional' ? 'action-reason-conditional' : ''}`}>
          <Info size={15} aria-hidden="true" />
          <span>{support.reason}</span>
        </p>
      )}
      {local && !allowed && !command && (
        <button className="button button-disabled-action" type="button" disabled aria-describedby={`reason-${action.id}`}>
          현재 환경에서 실행할 수 없음
        </button>
      )}
      {local && !allowed && !command && (
        <span id={`reason-${action.id}`} className="visually-hidden">{support.reason}</span>
      )}
    </article>
  );
}

export function SetupActions({ actions }: { actions: SetupAction[] }) {
  const platform = useSetupStore((state) => state.platformOverride ?? state.detectedPlatform);

  return (
    <div className="action-list">
      {actions.map((action) => (
        <SetupActionCard key={action.id} action={action} platform={platform} />
      ))}
    </div>
  );
}

export function GuideCode({
  service,
  step,
  platform,
}: {
  service: ServiceGuide;
  step: GuideStep;
  platform: Platform;
}) {
  if (!step.code) return null;
  const action = step.actionId ? service.actions.find((candidate) => candidate.id === step.actionId) : undefined;
  const isLocal = action ? isLocalAction(action) : false;
  const canCopy = action ? (!isLocal || localActionIsAllowed(action, platform)) : false;
  const code = action?.platformCommands?.[platform] || step.code;
  const reason = action && isLocal ? getActionSupport(action, platform).reason : '';

  return (
    <div className="step-code">
      <pre><code>{code}</code></pre>
      {action ? (
        <CopyButton text={code} label={step.title} disabled={!canCopy} />
      ) : (
        <p className="code-copy-note">
          <Info size={14} aria-hidden="true" />
          이 코드에는 실행 환경 정보가 연결되지 않아 복사 버튼을 제공하지 않아요.
        </p>
      )}
      {isLocal && !canCopy && reason && <p className="action-reason code-reason"><Info size={15} aria-hidden="true" />{reason}</p>}
    </div>
  );
}

export function GuideChecklist({ service }: { service: ServiceGuide }) {
  const completedIds = useSetupStore((state) => state.completedGuideStepIds);
  const setComplete = useSetupStore((state) => state.setGuideStepComplete);
  const resetSteps = useSetupStore((state) => state.resetGuideSteps);
  const platform = useSetupStore((state) => state.platformOverride ?? state.detectedPlatform);
  const hasHydrated = useSetupStore((state) => state.hasHydrated);
  const stepStorageIds = service.steps.map((step) => `${service.id}:${step.id}`);
  const completedCount = stepStorageIds.filter((id) => completedIds.includes(id)).length;

  return (
    <section className="guide-checklist" aria-labelledby="guide-checklist-title">
      <div className="checklist-heading">
        <div>
          <p className="eyebrow">내 진행 기록</p>
          <h2 id="guide-checklist-title">단계별 체크리스트</h2>
          <p className="checklist-description">직접 마친 단계를 표시해 두세요.</p>
        </div>
        <button
          type="button"
          className="button button-reset"
          onClick={() => resetSteps(stepStorageIds)}
          disabled={completedCount === 0}
        >
          <span>체크리스트 초기화</span>
        </button>
      </div>
      <p className="checklist-disclaimer">
        <Info size={15} aria-hidden="true" />
        선택한 내용은 이 브라우저에 저장되는 내 기록입니다. 설치나 계정 연결을 확인하는 기능은 아닙니다.
      </p>
      <ol className="guide-step-list">
        {service.steps.map((step, index) => {
          const storageId = `${service.id}:${step.id}`;
          const checked = completedIds.includes(storageId);
          const linkedAction = step.actionId ? service.actions.find((action) => action.id === step.actionId) : undefined;
          return (
            <li className={`guide-step${checked ? ' is-complete' : ''}`} key={storageId}>
              <label className="step-check-label">
                <input
                  type="checkbox"
                  checked={checked}
                  disabled={!hasHydrated}
                  onChange={(event) => setComplete(storageId, event.target.checked)}
                  aria-label={`${step.title} 완료 표시`}
                />
                <span className="step-checkmark" aria-hidden="true"><Check size={14} /></span>
                <span className="step-number step-number-small">{String(index + 1).padStart(2, '0')}</span>
                <span className="step-title">{step.title}</span>
              </label>
              <div className="step-body">
                <p>{step.body}</p>
                {step.note && <p className="step-note">{step.note}</p>}
                {linkedAction && (
                  <div className="step-action-reference">
                    <span>연결된 작업</span>
                    <a href={`#action-${linkedAction.id}`}>{linkedAction.label}</a>
                  </div>
                )}
                <GuideCode service={service} step={step} platform={platform} />
              </div>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
