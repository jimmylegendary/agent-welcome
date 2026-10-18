# Agent Welcome

## Simple Mode 웹사이트

**[Agent Welcome 시작하기](https://agent-welcome-alpha.vercel.app)**

초보자가 목적에 맞는 도구를 고르고 가입·설치·계정 연결을 따라갈 수 있는 한국어 가이드입니다. Next.js + Zustand로 구현하고 ui-ux-pro-max와 Tabler HTML 레이아웃을 참고했습니다.

- 서비스 가이드 35개, 실제 공개 화면 캡처 35개, 목적별 시작 경로 8개
- 모델 프로필 7개: HY4 Preview, DeepSeek V4.1 Flash, Seedance 2.5, Veo 3.1 Lite, Qwen Image Pro/Turbo, Jev
- OS 추정·수동 수정, 지원하지 않는 로컬 action의 비활성화, 사용자 체크리스트 저장
- Codex/OpenRouter·Next/Zustand·Flutter/MVVM·Jimmy Skills·크롤러 ZIP과 Supabase 등록·검사·제거 SQL

요구사항별 범위는 [simple-mode-coverage.md](https://github.com/jimmylegendary/agent-welcome/blob/feat/simple-mode-web/docs/simple-mode-coverage.md), 검증과 제한은 [simple-mode-verification.md](https://github.com/jimmylegendary/agent-welcome/blob/feat/simple-mode-web/docs/simple-mode-verification.md), 로컬 실행은 [README.md](https://github.com/jimmylegendary/agent-welcome/blob/feat/simple-mode-web/web/README.md)에 정리했습니다. 계정 가입·결제·key 발급은 사용자가 공식 서비스에서 직접 진행하며, 체크리스트는 사용자가 확인한 기록입니다.

## Easy Install

The approved 12-target Easy Install implementation is in
[easy-install.md](https://github.com/jimmylegendary/agent-welcome/blob/feat/typed-setup-reference/docs/easy-install.md), with the contract addendum in
[easy-install-decision.md](https://github.com/jimmylegendary/agent-welcome/blob/feat/typed-setup-reference/docs/easy-install-decision.md). Start with
`./easy-install.sh --target macos-codex` or
`.\easy-install.ps1 -Target windows-codex`. The first run records a concrete
official-installer plan; it executes only after explicit
`--approve-install` / `-ApproveInstall` consent. Runtime/device/auth evidence
is intentionally separate from implementation and fixture coverage.

왕초보·비개발자가 자기 기기에서 AI agent를 준비하고 첫 결과물까지 만들도록 돕는 웹사이트, skill 저장소, 쉬운 설치 서비스 프로젝트입니다.

현재는 **Simple Mode 웹사이트, 조사 자료, 정형 KG·catalog, 설치 recipe의 reference implementation**이 있습니다. 모바일 원본 agent 실행·실계정 연결·배포용 설치 앱의 검증은 웹사이트 배포와 별도 범위입니다.

## 제품 방향

- macOS, Windows, iOS, Android 각각을 독립 agent host로 다룹니다.
- 네 OS **각각에서** 기존 Claude Code, Codex, [Prime Agent](https://github.com/PrimeIntellect-ai/prime-agent) **세 agent 모두**를 기기 안에서 실행하는 것을 목표로 합니다. 12개 조합의 목표와 실제 검증 상태를 구분합니다.
- Claude·Codex·Paseo GUI와 실제 agent 실행 위치를 구분합니다.
- Jimmy's Agent Skills 기본 팩과 영상·이미지·코딩·자동화·마케팅·온라인 소매·게임 분야의 추가 도구를 함께 안내합니다.
- 공식 문서·블로그·GitHub 가이드를 KG로 연결해 환경 조건 → 오류 진단 → 복구 → 성공 확인에 사용합니다.
- 가입·credential 발급·로그인·권한·결제 등 사람이 해야 하는 단계도 안내 흐름에 포함합니다.

모바일의 원본 agent 실행과 각 도구 조합은 문서 근거와 실제 실행 검증을 구분합니다. 모델 추론 API 이용은 현재 기획의 잠정 전제입니다.

## Reference 실행

Python **3.11 이상**이 필요하며 Python 표준 라이브러리만 사용합니다. 저장소 루트에서 실행합니다. 대상 agent나 계정 없이 데이터 검증과 환경 진단이 가능합니다.

```bash
python3 -m agent_welcome validate
python3 -m agent_welcome diagnose --recipe prime-agent-0.10.0-linux-arm64
python3 -m unittest discover -s tests -v
```

첫 recipe는 **Prime Agent v0.10.0의 Linux ARM64·glibc >= 2.35 binary installation**입니다. 실제 kernel·CPU·libc 조건에 맞는 환경에서만 다음 단계로 진행합니다. Android·iOS에서 Linux guest가 실행되더라도 이것만으로 해당 휴대폰의 전체 지원이 입증되지는 않습니다.

```bash
python3 -m agent_welcome start --recipe prime-agent-0.10.0-linux-arm64 --state-dir .agent-welcome/prime
python3 -m agent_welcome status --state-dir .agent-welcome/prime
python3 -m agent_welcome resume --state-dir .agent-welcome/prime --artifact-file /path/to/prime-agent-0.10.0-linux-arm64.tar.gz
```

조건이 맞고 archive가 없으면 `WAITING_USER`로 저장합니다. `--artifact-file`로 파일을 제공하거나 `--download`로 고정 release 다운로드를 선택하면 게시된 hash 확인, 제한된 archive 추출, `--version` 확인을 수행합니다. 설치 파일과 상태는 지정한 state directory에 둡니다. 전체 성공 범위는 `binary_installation`이며 로그인·모델 요청·Python kernel·첫 결과물 성공을 뜻하지 않습니다.

`--observations FILE`은 `diagnose`에서만 사용할 수 있습니다. 실제 설치는 현재 실행 환경을 다시 관측합니다. 상세 실행 계약은 [reference-implementation.md](https://github.com/jimmylegendary/agent-welcome/blob/feat/typed-setup-reference/docs/reference-implementation.md)에 있습니다.

## 먼저 읽기

| 파일 | 내용 |
|---|---|
| [implementation-results.md](https://github.com/jimmylegendary/agent-welcome/blob/feat/typed-setup-reference/docs/implementation-results.md) | 실행 명령·테스트·독립 리뷰·미검증 범위 |
| [DECISIONS.md](https://github.com/jimmylegendary/agent-welcome/blob/feat/typed-setup-reference/DECISIONS.md) | 현행 결정, 조사 제안과의 우선순위, 미정 사항 |
| [support-targets.json](https://github.com/jimmylegendary/agent-welcome/blob/feat/typed-setup-reference/catalog/support-targets.json) | 12개 필수 지원 목표와 별도 검증 상태 |
| [reference-implementation.md](https://github.com/jimmylegendary/agent-welcome/blob/feat/typed-setup-reference/docs/reference-implementation.md) | 조건 판정, 실행·대기·재개, 필수 검사와 완료 범위 |
| [source-evidence.json](https://github.com/jimmylegendary/agent-welcome/blob/feat/typed-setup-reference/catalog/source-evidence.json) | 고정 source revision·hash·위치와 구조화된 주장 |
| [START-HERE.md](https://github.com/jimmylegendary/agent-welcome/blob/feat/typed-setup-reference/START-HERE.md) | 전체 제품 범위, 분야별 팩, 계정 연결, 단계별 계획 |
| [SETUP-KG-PLAN.md](https://github.com/jimmylegendary/agent-welcome/blob/feat/typed-setup-reference/SETUP-KG-PLAN.md) | 설치 지식 KG와 자동 예외 대응 설계 |
| [graph.json](https://github.com/jimmylegendary/agent-welcome/blob/feat/typed-setup-reference/kg/graph.json) | 공통 관계·조건·필수 check로 연결한 schema 0.2 KG와 5개 playbook |
| [GRAPH_REPORT.md](https://github.com/jimmylegendary/agent-welcome/blob/ab4b7c3abc5a84a3eb6af3cbc184bf8e5327c688/kg/GRAPH_REPORT.md) | 초기 KG의 근거 해석과 당시 검증 기록 |

## 조사 자료

| 파일 | 내용 |
|---|---|
| [platform-research.md](https://github.com/jimmylegendary/agent-welcome/blob/feat/typed-setup-reference/platform-research.md) | OS·agent·GUI 지원과 실행 위치 |
| [android-original-agent-validation.md](https://github.com/jimmylegendary/agent-welcome/blob/feat/typed-setup-reference/android-original-agent-validation.md) | Android에서 원본 agent를 실행할 경로와 오류 사례 |
| [ios-original-agent-validation.md](https://github.com/jimmylegendary/agent-welcome/blob/feat/typed-setup-reference/ios-original-agent-validation.md) | iOS runtime별 원본 agent 후보와 제약 |
| [workflow-skill-research.md](https://github.com/jimmylegendary/agent-welcome/blob/feat/typed-setup-reference/workflow-skill-research.md) | 코딩·자동화·마케팅·소매·DB·infra 후보 28개 |
| [media-game-research.md](https://github.com/jimmylegendary/agent-welcome/blob/feat/typed-setup-reference/media-game-research.md) | 영상·이미지·게임 후보 22개 |
| [local-skills-audit.md](https://github.com/jimmylegendary/agent-welcome/blob/feat/typed-setup-reference/local-skills-audit.md) | 기존 Jimmy skill 모음의 배포 준비 조사 |
| [verification.md](https://github.com/jimmylegendary/agent-welcome/blob/ab4b7c3abc5a84a3eb6af3cbc184bf8e5327c688/verification.md) | 첫 조사 문서의 검증 기록 |

## KG 데이터 상태

KG의 연구 경로와 playbook은 실행 검증·자동 실행이 비활성인 상태를 유지합니다. 실제 reference runner는 별도 pinned recipe의 제한된 action만 처리하며, KG에 들어 있는 설명이나 shell 문자열을 실행하지 않습니다.

`input_files`와 source의 `file_path`는 저장소 루트 기준 경로이며, 각 로컬 source에는 GitHub 문서 URL도 있습니다. `EXTRACTED`는 입력 자료에 관계가 명시됐다는 뜻이며 실제 실행 성공률을 뜻하지 않습니다.

설치기 테스트는 임시 archive와 작은 fixture executable로 설치·실패·대기·재개를 확인합니다. 실제 Prime 배포 파일 실행, 네 OS 실기기 설치, credential 연결의 증거는 아닙니다. 외부 agent binary나 기존 개인 skill 모음을 재배포하지 않으며, Simple Mode에는 새로 작성한 starter skill을 제공합니다. 초기 조사 기준일은 2026-10-17이며, 과거 검증 문서의 hash와 개수는 당시 사본에 대한 기록입니다.
