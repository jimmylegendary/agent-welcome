# Agent Welcome 웹사이트

Next.js App Router · React · TypeScript · Zustand로 만든 한국어 Simple Mode 가이드입니다. 공통 catalog가 35개 가이드, 7개 모델 프로필, 목적별 시작 순서와 OS별 action 상태를 공급합니다. 체크리스트는 사용자 확인 기록이며 외부 서비스 연결을 판정하지 않습니다.

## 로컬 실행

Node.js 24 LTS를 사용합니다. `web` 폴더에서 실행합니다.

```sh
npm ci
npm run dev
```

운영 빌드와 검사:

```sh
npm run lint
npm run typecheck
npm test
npm run build
npx playwright install chromium
npm run test:ui
```

Playwright는 사용하지 않는 지정 포트에서 개발 서버를 켰다가 종료합니다. 이미 실행 중인 운영 미리보기를 검사하려면 `PLAYWRIGHT_BASE_URL`을 설정합니다. 기존 Chrome을 사용할 경우 `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH`로 경로를 지정할 수 있습니다.

## 가이드와 다운로드 갱신

`src/data/catalog.ts`에 서비스의 action·단계·source를, `src/data/models.ts`에 모델의 정확한 ID·API·확인일을 둡니다. 명령과 상태를 바꾸면 해당 OS에서 복사되는 명령도 검사합니다. iOS 빌드는 별도 action이며 Windows의 일반 Flutter action에 섞지 않습니다.

`resources`에는 다운로드 원본이 있습니다. 원본을 고친 뒤 아래 명령으로 ZIP을 다시 만들고 두 쪽을 함께 commit합니다.

```sh
node scripts/build-downloads.mjs
```

공개 스크린샷은 `scripts/capture-guides.mjs`로 생성하고 `public/guides/manifest.json`에 실제 URL·제목·시각·상태를 기록합니다. 비공개 로그인 세션이나 credential 화면을 넣지 않습니다. 공개 문서 캡처를 사용자의 설치 성공 화면처럼 설명하지 않습니다.

Supabase SQL fixture 검사는 별도 임시 의존성을 사용하며 실계정에 접속하지 않습니다.

```sh
npm install --prefix /tmp/simple-mode-supabase-test-deps --no-save --ignore-scripts --no-audit --no-fund @electric-sql/pglite
PGLITE_MODULE_DIR=/tmp/simple-mode-supabase-test-deps/node_modules node scripts/test-supabase.mjs
```

## 배포

이 앱의 Vercel project는 `agent-welcome`입니다. 이 폴더에서 Vercel CLI로 배포하며, 계정과 project를 먼저 확인합니다. `.env.local`·`.vercel`은 Git과 다운로드 묶음에서 제외합니다. API key 입력 UI가 없으며 `NEXT_PUBLIC_*`에 provider secret을 넣지 않습니다.

```sh
vercel --prod
node scripts/verify-deployment.mjs https://YOUR-PRODUCTION-DOMAIN
```

검증 스크립트는 모든 가이드·이미지·다운로드의 HTTP 상태와 파일 형식, 없는 가이드의 404를 확인합니다. 유료 API, 로그인, 계정 가입과 결제를 수행하지 않습니다.
