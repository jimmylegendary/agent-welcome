# Jimmy Agent Skills 공개 패키지 준비 조사

> 현행 제품 결정은 [DECISIONS.md](https://github.com/jimmylegendary/agent-welcome/blob/feat/typed-setup-reference/DECISIONS.md)를 우선한다. 4개 OS 각각에서 세 agent 모두가 목표이며, 이 문서의 조사 제안은 확정 결정과 구분한다.

조사일: 2026-10-17. 현재 설치본과 2026-10-14 인벤토리를 출발점으로 삼은 기획 자료다. 원본 skill 수정·복사·공개는 하지 않았다.

## 기존 자산

기존 기존 개인 skill 인벤토리(이 저장소에는 포함하지 않음)에는 Claude Code 111개, Codex CLI 123개, prime-agent 13개 항목이 기록되어 있다. 이는 당시 agent별 등록 항목 수다. 중복을 제거한 skill 수나 Jimmy가 직접 저작한 skill 수가 아니다. 사용 횟수도 agent마다 집계 방법이 달라 품질 순위로 사용할 수 없다.

현재 `~/.agents/skills`의 일반 skill 디렉터리 22개를 확인했다. 주요 후보는 다음과 같다.

| 묶음 | 발견된 skill | 패키지에서 맡길 역할 제안 |
|---|---|---|
| 생각 정리 | `grill-me`, `grilling`, `grill-with-docs`, `domain-modeling` | 원하는 결과를 구체화하고 작업 계획 정리 |
| 문제 해결·인계 | `diagnosing-bugs`, `handoff` | 오류 설명, 작업 상태 저장·이어하기 |
| UI·마케팅 | `ui-ux-pro-max`, `product-marketing` | 웹·앱 디자인과 제품·고객 설명 |
| 게임 | `rpgmaker-core`, `rpgmaker-database`, `rpgmaker-events`, `rpgmaker-dialog`, `rpgmaker-consistency` | RPG Maker 전용 선택 팩 |
| host 운영 | `paseo`, `paseo-help`, `paseo-plugin`, `paseo-advisor`, `paseo-committee`, `paseo-handoff` | Paseo 설치·사용·문제 해결 및 고급 작업 |
| 추가 도구 의존 | `decision-models`, `graphify`, `git-guardrails-claude-code` | 별도 서비스·도구·hook 준비 여부를 확인한 뒤 제공 |

이 분류는 설치 승인이 아니라 공개 패키지 후보 정리다. 플러그인 캐시 전체는 이번에 복제하거나 재감사하지 않았다.

## 실제 확인한 차이

- 공유 경로와 Codex 경로의 `paseo` 계열 6개 및 `decision-models`는 `SKILL.md` 내용이 같았다. 패키지 원본을 여러 벌 유지할 이유를 검토할 수 있다.
- 두 경로에 있는 `ui-ux-pro-max`, `product-marketing`의 `SKILL.md`는 내용이 달랐다. 공개 기준본을 정하기 전에 변경 의도와 upstream을 확인해야 한다. 이름이 같다고 덮어쓰면 안 된다.
- 검사한 개별 일반 skill 폴더 바로 아래에는 `LICENSE*`/`COPYING*` 파일이 발견되지 않았다. **이것은 라이선스가 없다는 판정이 아니다.** 저장소 루트, frontmatter, 원본 배포 조건을 별도로 확인해야 한다.
- `decision-models`, `paseo-help`의 본문에는 절대 시스템 경로가 있다. 예시 경로인지 실제 실행 의존인지 구분해서 설치 대상의 OS와 사용자 경로로 처리해야 한다.

## 공개 저장소 설계 제안

공개 이름은 **Jimmy's Agent Skills**, 저장소 이름은 `jimmy-agent-skills`를 제안한다. 이름은 미확정이다.

| 종류 | 보관 방식 | 공개 시 필요한 정보 |
|---|---|---|
| Jimmy가 직접 만든 skill | 소스 포함 | 저작자, 적용 라이선스, 사용 예, 지원 범위 |
| 수정 가능한 외부 skill | 허용된 경우 원본·수정본 포함 | upstream URL·버전/commit·원 라이선스·수정 내역 |
| 재배포 조건이 불명확한 skill | 공식 원본 링크와 설치 안내 | 이용 조건 확인 상태, 공식 설치 경로 |
| 서비스에 종속된 plugin/connector | 해당 플랫폼 설치 안내 | 필요한 계정·요금제·연결 절차·다른 agent에서의 지원 여부 |

`SKILL.md`는 공유 형식이고, 그 안의 Python/Bash/CLI/MCP가 모든 OS에서 실행된다는 뜻은 아니다. 표준에는 환경 요구사항을 나타내는 `compatibility` 필드와 선택적 scripts 등이 있다. [Agent Skills specification](https://agentskills.io/specification)

기본 설치는 사용자가 요청한 정리된 skill 모음을 기준으로 한다. 다만 배포 전에 `agent × OS × 도구 의존성` 검증을 거쳐, 실제 사용할 수 있는 항목을 설치해야 한다. **기본 팩을 작게 할지, 분야별 팩까지 설치해 두고 필요할 때 활성화할지는 논의할 사항**이다. 전체 인벤토리를 임의로 기본 팩이라고 확정하지 않는다.

초보자 경험에 필요한 `welcome-guide`, `setup-doctor`, `credential-guide`, `first-task`, `resume-setup` 같은 안내 skill은 신규 작성 후보이며, 현재 존재하거나 검증되었다고 보지 않는다.

## 배포 전에 수행할 확인

1. 공개할 원본 목록과 기준 버전을 고정한다.
2. 저작권·라이선스·출처를 각 항목에 기록한다. 저장소 전체에 하나의 라이선스를 붙여 외부 저작물을 덮지 않는다.
3. 개인 경로, 내부 host 이름, 내부 서비스 주소, 토큰·계정 정보, 개인 전용 workflow를 점검한다.
4. 동일 이름의 다른 설치본을 비교하고 기준본을 정한다.
5. agent별 설치 위치·탐색·trigger·도구 호출을 시험한다.
6. OS별로 필요한 실행 도구를 확인한다. 설명 skill과 실행 script의 호환성을 따로 표시한다.
7. 처음부터 설치, 반복 설치, 업데이트, 실패 후 복구, 제거 시 사용자 파일 보존을 검증한다.

공개용 Markdown의 웹 링크는 공개 저장소 URL을 쓰고, 설치 기기의 로컬 파일 링크는 해당 기기 절대 경로로 생성하는 방식을 제안한다. Jimmy의 홈 경로를 다른 사용자에게 배포하지 않는다.

## 이번 조사 증거와 범위

- 읽은 자료: 기존 인벤토리의 관련 요약과 공유/Codex 일반 skill의 디렉터리 메타데이터 및 본문.
- 비교 방법: 같은 이름의 `SKILL.md`에 SHA-256을 적용하여 동일·차이를 분류.
- 설치 실행 시험: 0건. 외부 공개: 0건. 원본 수정: 0건. 커밋 생성: 없음.
- 이 결과는 배포 준비 목록이며, 라이선스 승인이나 설치 성공 인증이 아니다.
