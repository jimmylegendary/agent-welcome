# 모바일 원본 agent 설치 KG 초기 데이터 검토

> GitHub 배포본 안내: 아래 검사 결과와 SHA-256은 원래 로컬 조사 시점의 기록입니다. 이 사본은 링크와 경로를 저장소용으로 정리했으므로 배포본 파일의 hash와 다를 수 있습니다. 현재 상태와 자료 위치는 [README.md](https://github.com/jimmylegendary/agent-welcome/blob/main/README.md)를 참고하세요.

2026-10-17 · 조사와 설계용 seed · 자동 설치기 미구현

목표는 모바일에서 기존 Claude Code·Codex·Prime Agent를 실행하는 guide의 조건과 예외를 연결하는 것이다. 원본 agent를 별도 앱으로 대체하지 않고, source·실행 환경·증상·진단·복구 후보·성공 확인의 관계를 보관한다.

## 입력과 추출 방식

- 설계 계약: [SETUP-KG-PLAN.md](https://github.com/jimmylegendary/agent-welcome/blob/main/SETUP-KG-PLAN.md)
- Android 근거: [android-original-agent-validation.md](https://github.com/jimmylegendary/agent-welcome/blob/main/android-original-agent-validation.md)
- iOS 근거: [ios-original-agent-validation.md](https://github.com/jimmylegendary/agent-welcome/blob/main/ios-original-agent-validation.md)

관리형 worker가 지정한 세 파일에서 의미 관계를 추출하고, master가 원본 자료의 핵심 주장과 데이터 구조를 검토한다. Graphify의 `EXTRACTED / INFERRED / AMBIGUOUS` 출처 구분을 적용했다. Graphify CLI를 실행한 산출물은 아니며, 이번 단계에서 별도 graph server나 dependency를 설치하지 않았다.

`EXTRACTED`의 점수는 출처에 관계가 명시됐는지를 나타낸다. 기술적 참일 확률이나 실행 성공률이 아니다. 공식 문서·커뮤니티 보고·소스 확인·설계 제안을 구분하는 `evidence_status`와 실제 실행 검증 여부를 별도로 보존한다.

이번 semantic extraction의 정확한 input/output token 사용량과 금액은 도구에서 제공되지 않아 **미측정**이다. 0으로 기록하지 않는다.

## 이번에 수정한 근거 해석

- 공식 배포자가 게시한 checksum 확인과 다운로드 파일의 자체 hash 대조를 구분했다. 후자는 수행하지 않았다.
- Codux의 일반적인 설치 guide를 특정 휴대폰 모델에서 확인된 성공으로 확대하지 않았다. Script의 동작과 README 설명도 구분했다.
- `codex login --device-auth`는 공식 device-code 인증 경로이며, 커뮤니티 helper만의 기능으로 기록하지 않는다. 계정/조직 허용과 Android 실제 성공은 별도 조건이다.
- musl target이라는 이름만으로 dynamic loader가 필요하거나 특정 배포판만 사용할 수 있다고 가정하지 않는다. 실제 ELF·library 검사에 연결한다.
- iSH의 bitness 불일치를 재설치로 해결할 문제로 기록하지 않는다. UTM SE는 다음 시험 후보이며 성공한 복구로 기록하지 않는다.
- PRoot의 Linux userland 제공과 kernel namespace·sandbox·상시 service 지원을 구분한다. sandbox 우회를 일반 자동 복구로 채택하지 않는다.

## 실행 검증 범위

이번 후속 작업 초기에 로컬 Android 도구와 연결 기기의 OS·ABI 같은 읽기 전용 메타데이터를 확인했다. package 조회에는 권한 오류가 있었으며 agent 설치 상태나 실행 성공의 증거로 사용하지 않았다. 사용자 방향 확인 후 기기 탐색을 이어가지 않고 guide·소스 기반 조사로 진행했다.

agent 설치·실행·로그인·model API 요청·PRoot/VM 생성·자동 복구 실행은 **0건**이다. JSON 데이터의 parse·참조·출처·실행 비활성 상태를 검사한 결과와 기기 실행 성공을 구분한다.

원래 workspace는 Git 저장소가 아니며 이번에도 저장소 초기화·commit·push를 하지 않았다. **이번 변경의 commit SHA는 없다.**

## 현재 해석할 수 있는 질문

1. 같은 Android ARM64라도 Termux native와 PRoot Linux에서 설치 경로가 달라지는 이유는 무엇인가?
2. 로그인 callback 실패와 token exchange 실패를 어떤 진단으로 구분해야 하는가?
3. iSH에서 현재 배포 파일을 반복 설치해도 해결되지 않는 조건은 무엇인가?
4. 어느 복구 후보가 원본 artifact를 보존하고, 어느 후보가 binary를 수정하는가?
5. 어느 관계가 공식 문서의 사실이고, 어느 관계가 커뮤니티 보고 또는 설계 추론인가?

## 데이터와 검증 결과

초기 데이터와 최종 정적 검사 결과를 이 절에 기록한다. 이 seed는 실행 가능한 자동 설치기나 전 플랫폼 지원 완료 증명서가 아니다.

데이터 파일은 [graph.json](https://github.com/jimmylegendary/agent-welcome/blob/main/kg/graph.json)이다. 독립 reviewer는 OAuth 진단의 잘못된 연결, EXTRACTED 점수 규칙, callback과 token exchange의 혼동, Prime 적용 범위, 원본 구현과 수정 없는 binary의 구분, read-only와 쓰기 시험의 혼합을 지적했다.

master는 OAuth 단계 전용 diagnostic과 callback 증상 노드를 추가했고, device-auth를 callback/headless 조건에만 연결했다. token exchange 실패에서는 원인 진단으로 이어지고 device-auth를 검증된 해결로 연결하지 않는다. Prime의 적용 범위를 native Bionic과 PRoot userland 모두로 맞추고, 쓰기 시험을 첫 read-only 확인과 별도 단계로 나눴다. EXTRACTED 관계의 점수는 추출 계약에 맞게 1.0으로 통일했다.

master가 context-mode `ctx_execute(language="python")`에서 strict `json.loads`, ID 중복 검사, node/source 참조 검사, 관계 신뢰도 계약, 실행 비활성 상태, playbook 필수 필드·재시도 상한, Markdown 경로·구조 검사를 실행했다. OAuth 관련 graph query로 callback 대안과 token 교환 진단이 분리되는지도 확인했다. 외부 URL은 형식과 source 참조를 검사했으며, 이 검사에서 모든 URL을 다시 fetch한 것은 아니다.

실제 출력:

```text
markdown_documents=10
nodes=42
directed_links=54
sources=19
playbooks=5
local_links=17
checks_passed=14
checks_failed=0
EXTRACTED=45
INFERRED=9
bad_links=[]
bad_markdown=[]
token_exchange_diagnostic=diagnostics_auth_stages
callback_login_alternative=route_codex_device_auth_beta
token_exchange_verified_remedy=null
```

마지막 query의 `null`은 현재 KG가 token exchange 실패에 대해 device-auth를 검증된 해결책으로 연결하지 않는다는 뜻이다. 실제 서비스에서 해결책이 존재하지 않는다는 뜻은 아니다.

현재 파일 내용의 SHA-256:

```text
START-HERE.md 152236fa4bc93e2f3a46aaad00037c1bf5418116be449a66aa47cfa21935b9c3
SETUP-KG-PLAN.md a5da5d577a4681acf4d1c6ef034c192497c6e5185b85df37a199a477b194ea2d
android-original-agent-validation.md 548f360e56f8d346d746a565fa9215325057d84ac01bc541adbde826fbe55eb2
ios-original-agent-validation.md f4743529d9b592ffc4d5a808eb1d29a558af4c761dff533d66a744edbd93acaa
kg/graph.json c5088ae2a59d6b9648706c83c902521d8331b91f01c5324c91871af6aa58f836
```

이 검증 기록 자체는 자기 참조를 피하려고 SHA-256 목록에서 제외했다. 구조 검증은 실행 가능한 설치기·복구 엔진의 시험이나 실기기 재현을 대체하지 않는다.
