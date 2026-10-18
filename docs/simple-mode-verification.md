# Simple Mode 웹사이트 검증 기록

기준일: 2026-10-18. 기반 commit: `0f998df29184274d9c60317d2c8973c5a38e4d02`.

## 구현과 독립 검토

- 관리형 worker가 화면, 공통 catalog·호환성, 모델·starter, 공개 캡처·SQL을 분담했다. 별도 worker가 다른 작업자의 구현을 검토했고, 독립 최종 reviewer가 전체 변경을 검토했다.
- 수정한 실제 문제: hydration 전 상태 저장으로 진행 기록 유실, Windows에서 iOS 명령이 섞여 복사됨, Windows Python 단계의 Unix 명령 복사, 목적 팩의 첫 가이드만 노출, Jev의 제3자 페이지를 공식으로 오표시, 초보자용 첫 작업·key 연결·RLS 단계의 부정확한 연결.
- 추가 보완: 저장소 차단·손상 JSON 시 메모리 내 사용, 같은 출처 SQL 복사, 단계에서 해당 작업으로 이동, 작은 화면의 헤더·한국어 줄바꿈.
- 독립 최종 검토 결과 P1/P2 잔여 문제 없음. 리뷰만으로 외부 계정·기기 실행 성공을 주장하지 않는다.

## Master 실제 실행

Node 24.15.0, Chrome 152. 운영 서버는 `npm run start -- --port 3117`로 실행했다.

| 검사 | 명령 | 결과 |
|---|---|---|
| 정적 lint | `npm run lint` | exit 0 |
| TypeScript | `npm run typecheck` | exit 0 |
| 단위 검사 | `npm test` | 3 files, 29/29 PASS |
| 운영 서버 브라우저 검사 | `PLAYWRIGHT_BASE_URL=http://127.0.0.1:3117 PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/google-chrome npm run test:ui` | 16/16 PASS |
| 전체 페이지·이미지·다운로드 | `node scripts/verify-deployment.mjs http://127.0.0.1:3117` | 84 PASS, 0 FAIL |
| Supabase SQL lifecycle | `PGLITE_MODULE_DIR=/tmp/simple-mode-supabase-test-deps/node_modules node scripts/test-supabase.mjs` | 12/12 PASS, in-memory PGlite |
| 운영 의존성 알려진 취약점 | `npm audit --omit=dev --json` | total 0 |
| ZIP 경로·CRC·개인 경로 | Python zipfile 검사 | 5개 정상, 실제 key/config 및 개인 절대 경로 없음 |

UI 구현자의 `npm run build`는 Next.js 16.4.2에서 정적 페이지 43개 생성으로 통과했다. TypeScript 7.0.2와 현재 Next ESLint parser의 비호환을 확인해 6.0.2로 고정했고, 전체 Next TypeScript lint 규칙을 유지했다.

Desktop 1440×1000, mobile 390×844의 홈·가이드·catalog 화면을 master가 캡처해 직접 확인했다. 네 화면 모두 가로 overflow와 page error가 없었다. Clef 화면 판정은 헤더·줄바꿈 보정의 보조 근거로만 사용했다. 최종 스타일 보정은 별도 focused 확인을 수행한다.

## 자료·starter 검증

- 35개 screenshot manifest는 실제 공개 페이지 HTTP 200과 최종 URL·제목·시각을 기록한다. 34개 직접 캡처와 n8n 공식 문서 fallback 1개다. Jev는 TypeSafe 공식 문서에서 다시 캡처했다.
- 7개 모델 프로필은 일반 text 목록과 별도 image/video API를 구분한다. 가격은 공개 metadata의 날짜 있는 snapshot이다. 유료 미디어 생성은 수행하지 않았다.
- Next/Zustand starter의 TypeScript·ESLint, Flutter/Riverpod starter의 `flutter analyze --no-pub`와 포맷, skill 6개의 validator, TOML parsing, crawler JavaScript syntax가 worker 검사에서 통과했다.
- 독립 reviewer는 ZIP 5개를 원본 bytes와 비교했고, 기본 Supabase role/NOINHERIT 조건의 별도 fixture에서 service_role 실행과 anon 차단을 확인했다.

## 기존 Python reference의 별도 상태

저장소 AGENTS가 지정한 `python3 -m unittest discover -s tests -v`도 실행했다. **90개 중 77 PASS, 6 FAIL, 3 ERROR, 4 SKIP**였다. 웹 구현 전 같은 기반 코드에서 관측한 기존 bootstrap/easy-install 환경 의존 실패이며, 이번 웹 작업은 Python 구현을 수정하지 않았다. 웹사이트 다운로드에는 해당 기존 설치기를 포함하지 않는다. 이 결과를 전체 저장소 테스트 통과로 표현하지 않는다.

## 관측하지 않은 범위

실제 사용자 가입·결제·key 발급, 모델별 유료 tool-call·미디어 생성, 실 Supabase/PostgREST 연결, Android/iOS 원본 agent 실행, 앱스토어 게시, 전체 개인 skill inventory 설치는 이번 검증에 포함하지 않았다. 브라우저 체크리스트는 사용자 기록이다. Table RLS·앱 연결은 관리자 RPC 함수 권한 검사와 별도로 사용자가 확인한다.

## 배포

Vercel 배포 URL·최종 commit·공개 HTTP/browser 결과는 배포 후 이 절에 기록한다.
