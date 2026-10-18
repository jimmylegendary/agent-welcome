import type { Platform, SetupAction, SupportDecision } from './types';

const cloudActionKinds = new Set<SetupAction['kind']>(['web', 'download']);

export function getActionSupport(action: SetupAction, platform: Platform): SupportDecision {
  if (cloudActionKinds.has(action.kind)) {
    return {
      status: 'supported',
      reason: action.kind === 'web'
        ? '계정 가입과 문서 열기는 브라우저에서 할 수 있습니다.'
        : '다운로드 파일은 현재 기기에서 열거나 저장할 수 있습니다.',
    };
  }

  if (platform === 'unknown') {
    return {
      status: 'unverified',
      reason: '기기 OS를 확인하지 못해 로컬 실행 경로를 보장할 수 없습니다.',
    };
  }

  const declared = action.support[platform];
  if (declared) return declared;

  return {
    status: 'unverified',
    reason: `${platform}용 이 로컬 실행 경로는 문서화된 호환 근거가 없습니다.`,
  };
}

export function canRunAction(action: SetupAction, platform: Platform): boolean {
  if (cloudActionKinds.has(action.kind)) return true;
  if (platform === 'unknown') return false;

  const { status } = getActionSupport(action, platform);
  return status === 'supported' || status === 'conditional';
}
