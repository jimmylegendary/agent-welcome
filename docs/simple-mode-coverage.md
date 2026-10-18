# Simple Mode 요구사항과 구현 범위

기준일: 2026-10-18. 이 표의 `가이드`는 실제 웹 페이지, 공식 연결 링크, 공개 화면 캡처, 사용자 확인 단계가 있다는 뜻이다. 외부 계정 가입·키 발급·결제·실제 모델 생성·앱스토어 배포 성공을 뜻하지 않는다.

| 요구사항 | 웹사이트에 포함한 항목 | 별도 확인이 필요한 부분 |
|---|---|---|
| Codex / ChatGPT | 설치·로그인·API 인증 구분, Node 선행 조건, 첫 읽기 작업 명령 | 사용자 기기의 로그인과 실제 agent 작업 |
| OpenAI API | project, key, billing, 사용량 안내 | 결제 등록과 API 호출 |
| OpenRouter | key·credits, 정확한 모델 ID, Codex profile ZIP, OS별 key 연결 | 계정별 모델 권한과 tool-call 검사 |
| 고성능 / normal LLM | HY4 Preview / DeepSeek V4.1 Flash 1017 | preview·provider 변경 및 현재 요금 |
| 영상 모델 | Seedance 2.5 / Veo 3.1 Lite | 유료 출력 품질과 route별 입력·해상도 |
| 이미지 모델 | Qwen Image 2.1 Pro / Turbo | 유료 생성·편집 결과 |
| Jev | 판정 역할, 공식 TypeSafe 안내, 별도 공유 서비스 설명 | 모든 계정의 공개 모델 사용을 보장하지 않음 |
| npm / Python | Node LTS 안내, OS별 Python venv 생성·활성화 | 로컬 SDK 설치 |
| Next.js / Zustand | 사이트 구현과 별도 feature/service/store starter ZIP | 사용자 프로젝트에 맞는 실제 기능 |
| Flutter / MVVM | Riverpod + go_router starter, Web/Android와 iOS action 분리 | 앱 실행·서명·실기기 검사 |
| Jimmy Skills | 새로 작성한 공통·코딩·브라우저·미디어·마케팅/소매·게임 skill 6개 | 기존 개인 skill 전체 공개·호환 검증은 별도 |
| Supabase | signup/project, key 역할, 최초 등록·권한 검사·제거 SQL, SQL 복사 | 실제 Supabase 실행, 앱 연결과 table RLS 검사 |
| Airtable | PAT, base/resource 접근, data/schema scope | 사용자 plan·권한별 Metadata API 허용 |
| Firebase | project/web config, Rules·Admin credential 구분 | 사용자 앱의 Rules·IAM 검증 |
| n8n Cloud | plan/API 조건, management key, node OAuth 분리, schedule | 실제 workflow 활성화·외부 서비스 연결 |
| Vercel / GitHub | project/token, GitHub PAT·repository scope, preview 배포 안내 | 사용자별 repository 연결 |
| Google Play / App Store | 개발자 가입·검증·서명·게시 절차와 링크 | 계정 심사·정책·수수료·앱 심사 |
| Threads / Instagram | Meta 앱, OAuth·권한·계정 유형·게시 검사 | 실제 token 발급·앱 검토·게시 |
| Gmail / YouTube | Google Cloud API와 OAuth 설정 | 사용자 동의·scope·실제 요청 |
| Maps / Drive / Sheets / Slides | Maps billing·제한 key, 문서 도구 OAuth 연결 | 사용자 소유 파일 접근과 API 한도 |
| Unity | Hub/Editor 및 개발·빌드 준비 | Editor/target SDK와 실제 게임 빌드 |
| Higgsfield / Shotstack / ElevenLabs | 생성·렌더·음성 서비스별 가입·credential·비용·결과 안내 | 실제 유료 생성·렌더 요청 |
| 브라우저 자동화 | Playwright CLI 기본, agent-browser·browser-use 비교 | 사용자 기기의 browser/runtime 설치 |
| 크롤링 | Playwright 코드 ZIP, Tencent BrowserSkill 별도 연결 | 사이트별 허용 범위·사용자 로그인 작업 |
| OS에 맞는 버튼 | 자동 추정·수동 수정, supported/conditional/unsupported/unverified | 브라우저로 설치·인증 여부를 확인하지 않음 |
| 스크린샷 | 35개 공개 페이지의 실제 캡처와 URL·시각·결과 manifest | 로그인 후 private console 실습 캡처는 미포함 |
| 첫 사용과 재개 | 목적별 가이드 순서, 직접 확인한 단계의 로컬 저장·초기화 | 서비스 연결 상태 자동 확인과 동일하지 않음 |

## 기기별 해석

| 행동 | macOS | Windows | Android | iOS |
|---|---|---|---|---|
| 가입·공식 문서·cloud console 열기 | 가능 | 가능 | 가능 | 가능 |
| 파일 다운로드·SQL 복사 | 가능 | 가능 | 가능 | 가능 |
| Codex 등 원본 agent 로컬 실행 | 조건 확인 | 조건 확인 | 미검증 표시 | 미검증 표시 |
| Flutter/Unity/desktop browser 도구 | 조건 확인 | 조건 확인 | 해당 desktop 경로 비활성 | 해당 desktop 경로 비활성 |
| iOS 최종 빌드·서명 | Xcode 등 조건 확인 | 비활성 | 비활성 | 비활성 |

사용자 목표인 네 OS × 세 원본 agent의 독립 host 지원은 유지한다. 이 웹사이트 배포가 모바일 원본 agent 실기기 검증을 완료시키지는 않는다. 상태는 개별 action의 증거 범위를 따라 표시한다.
