# 비개발자를 위한 AI Agent Welcome Package 조사와 논의안

> 현행 제품 결정은 [DECISIONS.md](https://github.com/jimmylegendary/agent-welcome/blob/feat/typed-setup-reference/DECISIONS.md)를 우선한다. 4개 OS 각각에서 세 agent 모두가 목표이며, 이 문서의 조사 제안은 확정 결정과 구분한다.

2026-10-17 · 기획 초안 · 설치·배포·구현 전

**후속 결정:** 모바일에서도 기존 Claude Code·Codex·Prime Agent의 실행 경로를 우선한다. 별도 자체 agent 앱으로 바꾸는 방향은 채택하지 않았다. 공식 가이드·블로그·GitHub의 설치 지식과 오류 대응을 KG로 연결하고, 사용자의 환경에 맞는 경로 선택·진단·복구·성공 확인을 자동화하는 구조를 설계한다. 상세 설계는 [SETUP-KG-PLAN.md](https://github.com/jimmylegendary/agent-welcome/blob/main/SETUP-KG-PLAN.md)에 이어서 기록한다.

이 제품의 목표는 **처음 쓰는 사람이 자기 기기에서 AI agent를 준비하고, 계정을 연결하고, 원하는 첫 결과물까지 만드는 것**이다. 웹사이트·GitHub·설치 앱·분야별 안내가 같은 설치 정보와 검증된 작업 예시를 공유해야 한다.

가장 먼저 풀어야 할 문제는 모바일이다. Jimmy는 macOS·Windows·iOS·Android 각각을 독립 host로 요구했다. 따라서 iPhone에서 다른 PC의 agent를 원격 조작하는 방식은 이 요구를 충족하지 않는다. **기존 agent의 모바일 실행 가능성을 먼저 검증하면서, 공통 안내와 분야별 팩을 설계하는 순서**를 제안한다.

## 확정된 요구와 아직 열린 선택

| 항목 | 현재 내용 |
|---|---|
| 사용자 | 왕초보·비개발자 |
| 제공물 | 웹사이트, GitHub 저장소, 매우 쉬운 설치·설정 서비스 |
| 실행 host | macOS, Windows, iOS, Android 각각 독립 실행 |
| agent | Claude, Codex, [Prime Agent](https://github.com/PrimeIntellect-ai/prime-agent) |
| GUI | Claude, Codex, Paseo |
| 기본 skill | 기존 정리본을 Jimmy's Agent Skills로 정리해 기본 설치 |
| 분야 | 영상 생성·편집, 이미지 생성·편집, 웹·모바일·desktop 코딩, SNS·예약·이벤트·브라우저 자동화, 마케팅, 온라인 소매, 게임 |
| 주변 환경 | DB, infra, n8n 등 필요한 도구·서비스와 계정·credential 발급·설정 안내 |
| 이번 단계 | 논의·리서치·계획. 실제 설치나 공개 저장소 생성은 하지 않음 |
| 가정 | agent 실행은 기기 안에서 하고 모델 추론 API와 분야별 SaaS API는 이용할 수 있다고 해석. 완전 offline 요구로 확정된 것은 아님 |
| 미정 | Claude Code CLI와 Claude Desktop의 Code·Chat·Cowork 중 포함 범위, 우선 고객·첫 작업·가격·지원 방식. 모바일은 기존 세 agent 실행 경로 우선으로 결정 |

모델·agent·GUI·skill·실행 도구는 구분해야 한다. 예를 들어 Claude 모델 API를 호출하는 자체 앱은 Claude Code가 아니며, `SKILL.md`를 설치했다고 FFmpeg·브라우저·DB 실행 기능까지 생기는 것은 아니다. Agent Skills 표준도 scripts와 환경 의존성을 별도로 다룬다. [Agent Skills specification](https://agentskills.io/specification)

현재 Claude Desktop에는 Chat·Cowork·Code 탭이 있으며, Code 탭은 로컬 파일·명령을 다루는 Claude Code GUI 경로다. 같은 앱에서도 Local·Cloud·SSH·Windows의 WSL 실행 환경을 구분한다. 이 제품에서는 같은 기기의 Local/WSL 세션을 독립 host 검증 대상으로 삼고, remote 세션을 혼동하지 않아야 한다. [Claude Code Desktop 공식 문서](https://code.claude.com/docs/en/desktop)

## 모바일 요구가 제품에 미치는 영향

| 플랫폼 | 조사 단계의 판단 | 먼저 확인할 것 |
|---|---|---|
| macOS | desktop agent와 설치 안내를 결합할 현실적인 출발점 | 지원 chip·OS, 실제 agent/GUI 조합, 사용자 권한, 설치·업데이트 |
| Windows | desktop 경로를 검증하되 native와 WSL 환경을 구분 | agent마다 native/WSL 지원, GUI와 실제 실행 위치, 한글 경로·재부팅 |
| Android | 기기 내 terminal/native runtime 경로를 실기기로 검토할 대상 | 정확한 agent binary/runtime, 파일 권한, 프로세스 유지, GUI 연결 |
| iOS | 기존 desktop agent 그대로의 설치를 현재 보장할 수 없음 | 원본 agent 실행, sandbox 범위, 코드 실행·배포 조건, background 동작 |

이 표는 설치 성공 판정이 아니다. agent별 공식 지원과 출처는 [platform-research.md](https://github.com/jimmylegendary/agent-welcome/blob/main/platform-research.md)에서 구분한다.

iOS App Review Guidelines는 앱 컨테이너 밖 접근과 기능을 바꾸는 다운로드 코드에 제한을 두며, background service 용도도 제한한다. 이 때문에 임의 shell·패키지 설치·상시 자동화까지 desktop과 같은 기능으로 약속할 수 없다. 그렇다고 모든 on-device agent가 불가능하다는 결론도 아니다. 앱에 내장한 제한된 도구와 사용자가 선택한 파일을 다루는 방식은 별도 검토할 수 있다. [Apple App Review Guidelines 2.5.2와 2.5.4](https://developer.apple.com/app-store/review/guidelines/)

Android도 기기 제조사와 사용자 배터리 제한에 따라 background 작업·network 동작이 달라진다. 따라서 foreground 첫 작업과 장시간·예약 작업의 합격 기준을 따로 잡아야 한다. [Android background restrictions](https://developer.android.com/develop/background-work/background-tasks/bg-work-restrictions?hl=en)

**네 기기 모두에서 동일한 CLI·GUI·외부 도구를 제공하는 것과, 네 기기 모두에서 독립 host로 유용한 작업을 제공하는 것은 다른 범위다.** 모바일에 별도 runtime을 만들면 제품 개발 규모가 커지므로, 먼저 원본 agent 실행 경로를 검증하고 그 결과로 범위를 결정해야 한다.

## 초보자가 따라갈 하나의 흐름

1. **하고 싶은 일 고르기:** “쇼츠 만들기”, “상품 사진 다듬기”, “내 사이트 만들기”처럼 결과로 시작한다.
2. **내 기기 확인:** OS·chip·용량·기존 설치를 확인하고 가능한 팩만 보여준다.
3. **필요한 계정과 비용 확인:** 이미 가진 구독, 새 계정, API 별도 과금, 결제가 필요한 단계를 짧게 보여준다.
4. **설치하기:** 필요한 runtime·agent·GUI·skill·도구를 해당 기기의 검증된 조합으로 준비한다.
5. **연결하기:** 지금 필요한 로그인·키 발급·권한 허용을 한 번에 하나씩 안내한다.
6. **연결 확인:** 실제로 작은 요청이나 파일 작업을 실행해서 권한·설정·실행 위치를 확인한다.
7. **첫 작품 만들기:** 예제 입력으로 쓸 수 있는 결과물을 만들고 저장 위치까지 알려준다.
8. **다시 하기와 복구:** 내 자료로 반복하고, 중단한 설정을 이어서 진행하고, 오류를 쉬운 말로 해결한다.

처음부터 agent·model·MCP·token·Docker를 모두 고르게 하지 않는 것이 제안이다. 필요한 선택은 해당 결과를 만드는 순간에 설명하고, 상세 설정은 별도 화면에서 제공한다.

## 제품을 이루는 네 부분

| 부분 | 책임 | 핵심 결과물 |
|---|---|---|
| Welcome 웹사이트 | 목적별 탐색, 호환성·비용 안내, 쉬운 사용법 | “내 기기에서 무엇을 만들 수 있나” |
| Jimmy's Agent Skills | 기본 skill과 분야별 skill의 원본·출처·버전 관리 | 검토 가능한 공개 skill 모음 |
| Setup 앱·설치기 | 진단, 설치, credential 연결, 확인, 업데이트·복구 | 정상 동작하는 기기별 환경 |
| 공통 카탈로그 | 도구·팩·가이드·설치 단계·시험 결과의 공통 데이터 | 사이트와 설치기에서 서로 어긋나지 않는 정보 |

웹페이지의 다운로드 버튼만으로 OS 권한이나 모든 계정 발급이 끝나지는 않는다. 제안하는 desktop 진입점은 서명된 설치 앱이며, 모바일 배포 경로는 실제 runtime 검증 뒤 결정한다. 웹 기반 안내만으로 가능한 작업과 설치 앱이 필요한 작업을 따로 표시한다.

저장소는 `jimmy-agent-skills`와 `agent-welcome`의 두 개를 제안한다. 전자는 skill 배포, 후자는 사이트·설치기·카탈로그·가이드·검증 이력을 맡는다. GitHub 계정·조직·이름은 아직 정하지 않았다.

기술 stack은 모바일 runtime과 GUI 연결 방법이 정해진 뒤 선택한다. 지금 React/Electron/Tauri/Flutter 중 하나로 확정하면 가장 중요한 실행 제약을 뒤늦게 맞추게 된다.

## 참고할 선례와 필요한 추가 가치

| 선례 | 확인한 기능 | 이 제품에서 더 준비할 것 |
|---|---|---|
| [Pinokio](https://github.com/pinokiocomputer/pinokio) | script 실행을 쉽게 제공하는 launcher | agent별 계정 연결과 결과별 사용 안내 |
| [Stability Matrix](https://github.com/LykosAI/StabilityMatrix) | 이미지 도구 설치·업데이트와 실행 의존성 관리 | 이미지 외 도메인과 agent host 준비 |
| [skills.sh](https://www.skills.sh/docs) | skill 검색·설치·pack 배포 | 기기별 실제 작동 검증과 첫 작업 안내 |

이 도구들을 그대로 합치면 모든 요구가 해결된다고 보지는 않는다. 재사용 가능한 부분을 조사하고, 초보자가 실제로 막히는 계정·권한·비용·복구 흐름을 우리 제품의 중심으로 만든다.

## 분야별 첫 성공 팩 제안

| 분야 | 첫 결과물 | 팩에 함께 있어야 할 것 |
|---|---|---|
| 영상 생성·편집 | 사진·문구로 짧은 세로 영상, 자막·길이 수정 | 생성 API 또는 지원 기기의 생성 도구, 편집·인코딩 도구, 예제·저장·미리보기 |
| 이미지 생성·편집 | 상품 이미지 생성, 배경·크기·문구 수정 | 생성/편집 API 또는 로컬 도구, 원본 보존·내보내기 |
| 웹 코딩 | 작은 소개 페이지 | agent, 미리보기, 기본 디자인 skill, 배포 선택 안내 |
| 모바일·desktop 코딩 | 실행 가능한 작은 앱 | target별 SDK·빌드 가능 host·실기기 시험·서명 안내. 코드 생성과 앱 빌드는 구분 |
| SNS 자동화 | 게시 초안과 승인 가능한 예약 흐름 | 공식 API 연결, 채널별 권한, 내용 확인, 실행 이력 |
| 예약·이벤트 자동화 | 정해진 조건에서 요약·파일 정리 | 실행 host의 전원·network·background 조건, 재시도·중복 방지 |
| 브라우저 자동화 | 허용한 사이트에서 반복 자료 정리 | 지원 브라우저, 로그인 세션, 실행 범위, 결과 확인 |
| 마케팅 | 고객·제품 설명, landing page 문구, 콘텐츠 계획 | product-marketing context, 분야 skill, 분석 서비스 연결 선택 |
| 온라인 소매 | 상품 설명·사진·CSV 또는 상품 초안 | 판매 채널 API, 필수 상품 필드, 이미지, 미리보기·게시 단계 |
| 게임 | 작은 플레이 가능한 장면 또는 RPG 이벤트 | 해당 engine·asset·실행 환경, 게임 분야 skill, 플레이 확인 |
| DB·infra | 예제 데이터 저장과 읽기 성공 | 계정·project·권한·connection test, 백업·삭제·비용 안내 |

세부 후보는 [media-game-research.md](https://github.com/jimmylegendary/agent-welcome/blob/main/media-game-research.md)와 [workflow-skill-research.md](https://github.com/jimmylegendary/agent-welcome/blob/main/workflow-skill-research.md)에 정리한다. 각 후보의 `skill / MCP / CLI / SDK / API / 수동 앱` 구분을 유지한다.

분야 전체를 카탈로그에 담는 것과 모든 분야를 기본 설치하는 것은 별도 선택이다. **기본 설치할 Jimmy skill의 범위는 기존 정리본을 확인하고 정한다.** 제안은 호환성이 검증된 기본 팩을 설치하고, 사용자가 선택한 분야의 실행 도구와 계정은 그때 준비하는 방식이다. 기존 자산 확인 결과는 [local-skills-audit.md](https://github.com/jimmylegendary/agent-welcome/blob/main/local-skills-audit.md)에 있다.

## 사람이 해야 하는 일도 제품 기능으로 만든다

| 단계 | 사용자가 할 일 | 제품이 준비할 일 | 완료를 판정할 증거 |
|---|---|---|---|
| 계정 생성 | 가입, 본인 확인, 필요한 약관 동의 | 정확한 공식 화면 열기, 다음 단계 안내 | 로그인 계정 확인 |
| 요금·결제 | plan 선택, 카드·결제 확인 | 구독과 API 과금 구분, 필요한 비용 설명 | 이용 가능한 기능·quota 확인 |
| OAuth | 공식 로그인·MFA·권한 동의 | 지원되는 native 로그인 흐름과 callback | 대상 계정·scope·만료 확인 |
| API key | 공식 콘솔에서 project·key 발급 | 발급 화면·선택값 안내, 안전한 입력란 | 제한된 실제 API 요청 성공 |
| 서비스 project | workspace·shop·DB 등 생성 | 이름·지역·권한 선택 설명과 기본값 | 올바른 project 읽기 성공 |
| OS 권한 | 파일·사진·알림 등의 접근 허용 | 해당 기능을 쓰는 순간 최소 권한 요청 | 선택한 자료 접근 성공 |
| 검수·게시 | 결과 확인, 게시·배포 결정 | 미리보기와 변경 내용 표시 | 실제 반영 위치·상태 확인 |

credential을 채팅에 붙여넣게 하는 대신, 전용 연결 화면으로 받는 설계를 제안한다. macOS/iOS는 Keychain, Windows는 OS credential 보호 기능, Android는 Keystore로 보호한 암호화 저장소를 후보로 한다. Android Keystore에는 보통 데이터를 암호화할 key를 보관하므로 임의 API token 저장소와 같은 것으로 설명하지 않는다. [Apple Keychain](https://developer.apple.com/documentation/security/keychain-services), [Android Keystore](https://developer.android.com/privacy-and-security/keystore)

native OAuth는 공급자가 지원하는 외부 browser·PKCE 방식부터 검토한다. 공개 배포 앱에 서비스의 confidential client secret을 넣지 않는다. 서비스가 별도 backend나 app 검수를 요구하면, 운영자가 제공할 연결 서비스와 사용자가 직접 설정할 경로를 명시적으로 결정해야 한다. 계정 자동 생성이나 모든 서비스의 key 자동 발급을 일괄 약속하지 않는다. [OAuth for Native Apps RFC 8252](https://datatracker.ietf.org/doc/html/rfc8252)

각 연결 guide에는 **왜 필요한지 → 지금 누를 곳 → 사용자가 넣을 값 → 완료 화면 → 실패 이유 → 이어하기 → 연결 해제·key 교체**가 있어야 한다. 가입·MFA·결제·권한 동의에서 멈추더라도 이미 완료한 설치를 반복하지 않아야 한다.

## 독립 host와 자동화의 경계

agent host, 모델 추론, 외부 서비스 실행을 카탈로그에서 각각 표시한다. 예를 들어 기기에서 실행하는 agent가 이미지 생성 API를 호출하는 것과, cloud agent가 프로젝트 전체를 실행하는 것은 다르다.

**기기 내 실행과 데이터가 기기 밖으로 나가는지도 별도로 안내한다.** 제안하는 수용 조건은 첫 모델·서비스 연결 화면에서 전송되는 대화·파일 내용·도구 결과의 범위, 수신 provider, 보존 정책·사용자 설정 링크를 보여주는 것이다. “로컬 실행” 표시를 “모든 데이터가 기기 안에만 남음”이라는 뜻으로 사용하지 않는다.

n8n Cloud나 hosted scheduler가 workflow를 실행하면 그 자동화의 실행 host는 외부 서비스다. 외부 API 이용 범위가 허용되더라도 이를 “모든 실행이 휴대폰 안에서 끝난다”로 설명하면 안 된다. 엄격한 로컬 실행 팩과 외부 서비스 이용 팩의 표시 방식은 사용자와 결정해야 한다.

PC가 꺼져 있거나 모바일 OS가 작업을 중단한 상황에서 정확한 시각의 계속 실행을 보장할 수 없다. 완전한 기기 내 실행이 필수라면 이 조건을 기능 설명·예약 설정·시험에 포함한다. 원격 서버를 기본 해법으로 바꾸지는 않는다.

## 광범위한 조사와 유지관리 방법

`awesome agent skills`, `awesome claude skills`, `awesome codex`, `awesome video generation`, `awesome image editing`, `awesome n8n`, `awesome marketing`, `awesome ecommerce`, `awesome gamedev` 등을 발견 경로로 쓰고, 실제 판정은 원본 저장소·공식 문서·실행 시험으로 한다.

이번에 저장소 존재와 설명을 확인한 발견 출발점은 [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills), [travisvn/awesome-claude-skills](https://github.com/travisvn/awesome-claude-skills), [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills), [awesome-generative-ai](https://github.com/steven2358/awesome-generative-ai), [sindresorhus/awesome](https://github.com/sindresorhus/awesome)이다. 목록 저장소의 라이선스나 설명이 그 안에 연결된 모든 skill의 재배포 조건·품질을 보증하지는 않는다.

카탈로그에는 결과물, 원본 URL, 유형, 지원 OS·architecture·agent·GUI, local/API 실행 위치, 필요한 계정·권한·결제, 라이선스, 고정 버전/commit, 설치·검증·복구·제거 방법, 확인일을 기록한다. 별점이나 다운로드 수만으로 기본 설치 대상을 정하지 않는다.

표시는 `발견 → 공식 문서 확인 → 실행 확인 → 초보자 시험 통과 → 기본 팩 채택`으로 나눈다. 이번 조사에서 문서를 확인한 후보를 설치 시험에 통과한 것으로 올리지 않는다. 새 버전이 나오면 영향받는 조합을 재검증하고, 실패한 조합은 추천 상태를 내린다.

공개 skill은 출처와 라이선스를 보존하고, 고정한 버전으로 검증한다. 기존 파일은 설치 전 변경 내역을 보여주고 보존하며, 제거할 때 사용자의 프로젝트·결과물·다른 도구 설정을 지우지 않는 것을 설치기 수용 조건으로 제안한다.

## 구현에 들어가기 전 단계별 계획

| 단계 | 작업 | 통과 기준 |
|---|---|---|
| 0. 제품 범위 결정 | 첫 사용자·첫 결과물, 모델/API 허용 범위, 모바일 agent 정체성 결정 | 바꿀 수 없는 조건과 기능 차이 문서화 |
| 1. 실행 가능성 확인 | 네 OS에서 agent별 설치·로그인·skill·파일·도구 시험; 모바일부터 위험 검증 | 각 조합의 성공·실패 로그와 실행 host 증거 |
| 2. 기본 skill 정리 | 기존 인벤토리 기준본·출처·라이선스·개인 설정 정리 | 공개 가능한 목록과 호환성 표 |
| 3. 안내 경험 검증 | 대표 작업 하나의 계정·credential·설치·복구 안내를 초보자와 확인 | 어디서 막히는지 실제 관찰 기록 |
| 4. 첫 제품 구현 | 공통 카탈로그, 웹 안내, 검증된 host 설치기, 첫 성공 팩 | 처음부터 설치·첫 결과·재실행·복구·제거 통과 |
| 5. 분야 확대 | 분야별 도구·skill·서비스를 같은 검증 절차로 추가 | 지원·비용·유지관리 책임이 있는 팩으로 출시 |

단계 1에서 모바일 실현 가능성을 해결하지 못하면 “4개 OS 독립 host 지원”을 완료로 선언하지 않는다. 지원 범위 변경은 Jimmy가 결정한다. desktop을 먼저 공개할지 여부도 아직 확정하지 않는다.

시험 항목은 깨끗한 사용자 계정, 기존 설치가 있는 기기, 한글·공백 경로, 권한 거절, 잘못된/만료된 key, network 단절, quota 부족, 재부팅, 모바일 잠금·background·강제 종료, 반복 설치·업데이트·제거를 포함한다. agent 파일 작업과 실제 child process 실행 위치를 확인해 remote 실행이 섞이지 않았음을 판정한다.

초기 성공 지표는 설치 개수보다 **도움 없이 첫 결과물을 만든 비율, 시작부터 결과까지 시간, credential 단계 이탈, 실패 후 복구율, 7일 뒤 재사용**으로 제안한다. 소수 비개발자 관찰 시험으로 시작하고, 시간·성공률 목표는 관찰값을 얻은 뒤 확정한다. 현재 근거 없이 “누구나 5분” 같은 약속을 잡지 않는다.

무료 공개 skill·guide와 유료 설치 편의·유지관리·지원의 조합은 수익화 가설이다. 서비스별 이용 조건과 실제 지원 비용을 확인한 뒤 정해야 하며, 가격은 아직 제안하지 않는다.

## 다음 논의에서 먼저 정할 것

모바일은 **기존 Claude Code·Codex·Prime Agent 자체를 실행하는 경로부터 조사**하기로 결정했다. 공식·커뮤니티 가이드의 실행 조건과 예외를 KG에 기록하고, 설치 중 환경 진단과 성공 확인을 통해 적용 여부를 판단한다. 가이드에서 보고된 성공과 우리 설치기의 실제 성공은 별도 기록한다.

그다음은 첫 고객 한 명이 어떤 결과를 얻어야 하는지다. 후보로는 “사진으로 홍보 영상 만들기”, “상품 사진·설명 만들기”, “작은 소개 사이트 만들기”가 있다. 전체 분야를 카탈로그에 담되, 처음부터 끝까지 검증할 대표 흐름은 먼저 하나를 정하는 것을 제안한다.

## 조사 상태

공식 자료와 기존 인벤토리를 바탕으로 한 1차 조사다. 제품의 구현·공개·설치 시험은 수행하지 않았다. 개별 후보의 미확인 사항은 분야별 문서에 남긴다. 최종 실행 검증과 변경 범위 증거는 [verification.md](https://github.com/jimmylegendary/agent-welcome/blob/main/verification.md)에 기록한다.
