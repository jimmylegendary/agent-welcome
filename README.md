# Agent Welcome

왕초보·비개발자가 AI agent 환경을 준비하고 첫 결과물까지 만들도록 돕는 웹사이트, skill 저장소, 쉬운 설치 서비스의 조사·설계 자료입니다.

현재는 **조사와 기획 단계**입니다. 설치기와 자동 복구 실행 엔진은 아직 구현하지 않았습니다.

## 제품 방향

- macOS, Windows, iOS, Android 각각을 독립 agent host로 다룹니다.
- 기존 Claude Code, Codex, [Prime Agent](https://github.com/PrimeIntellect-ai/prime-agent)를 기기 안에서 실행하는 경로를 우선합니다.
- Claude·Codex·Paseo GUI와 실제 agent 실행 위치를 구분합니다.
- Jimmy's Agent Skills 기본 팩과 영상·이미지·코딩·자동화·마케팅·온라인 소매·게임 분야의 추가 도구를 함께 안내합니다.
- 공식 문서·블로그·GitHub 가이드를 KG로 연결해 환경 조건 → 오류 진단 → 복구 → 성공 확인에 사용합니다.
- 가입·credential 발급·로그인·권한·결제 등 사람이 해야 하는 단계도 안내 흐름에 포함합니다.

모바일의 원본 agent 실행과 각 도구 조합은 문서 근거와 실제 실행 검증을 구분합니다. 모델 추론 API 이용은 현재 기획의 잠정 전제입니다.

## 먼저 읽기

| 파일 | 내용 |
|---|---|
| [START-HERE.md](https://github.com/jimmylegendary/agent-welcome/blob/main/START-HERE.md) | 전체 제품 범위, 분야별 팩, 계정 연결, 단계별 계획 |
| [SETUP-KG-PLAN.md](https://github.com/jimmylegendary/agent-welcome/blob/main/SETUP-KG-PLAN.md) | 설치 지식 KG와 자동 예외 대응 설계 |
| [graph.json](https://github.com/jimmylegendary/agent-welcome/blob/main/kg/graph.json) | 42개 노드·54개 관계·5개 복구 후보를 담은 초기 KG |
| [GRAPH_REPORT.md](https://github.com/jimmylegendary/agent-welcome/blob/main/kg/GRAPH_REPORT.md) | KG의 근거 해석, 독립 검토와 로컬 검증 기록 |

## 조사 자료

| 파일 | 내용 |
|---|---|
| [platform-research.md](https://github.com/jimmylegendary/agent-welcome/blob/main/platform-research.md) | OS·agent·GUI 지원과 실행 위치 |
| [android-original-agent-validation.md](https://github.com/jimmylegendary/agent-welcome/blob/main/android-original-agent-validation.md) | Android에서 원본 agent를 실행할 경로와 오류 사례 |
| [ios-original-agent-validation.md](https://github.com/jimmylegendary/agent-welcome/blob/main/ios-original-agent-validation.md) | iOS runtime별 원본 agent 후보와 제약 |
| [workflow-skill-research.md](https://github.com/jimmylegendary/agent-welcome/blob/main/workflow-skill-research.md) | 코딩·자동화·마케팅·소매·DB·infra 후보 28개 |
| [media-game-research.md](https://github.com/jimmylegendary/agent-welcome/blob/main/media-game-research.md) | 영상·이미지·게임 후보 22개 |
| [local-skills-audit.md](https://github.com/jimmylegendary/agent-welcome/blob/main/local-skills-audit.md) | 기존 Jimmy skill 모음의 배포 준비 조사 |
| [verification.md](https://github.com/jimmylegendary/agent-welcome/blob/main/verification.md) | 첫 조사 문서의 검증 기록 |

## KG 데이터 상태

`kg/graph.json`은 `research_seed`입니다. `automatic_execution_enabled`, `runtime_tested`, `direct_reproduction`은 모두 `false`입니다.

`input_files`와 source의 `file_path`는 저장소 루트 기준 경로이며, 각 로컬 source에는 GitHub 문서 URL도 있습니다. `EXTRACTED`는 입력 자료에 관계가 명시됐다는 뜻이며 실제 실행 성공률을 뜻하지 않습니다.

이 저장소에는 조사 문서와 초기 KG만 포함되어 있습니다. 개별 skill의 실행 파일이나 외부 도구를 재배포하는 저장소는 아직 아닙니다. 자료 기준일은 2026-10-17이며, 과거 검증 문서의 hash는 원래 로컬 사본에 대한 기록입니다.
