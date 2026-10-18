# Simple Mode 공개 가이드 자료

이 문서는 공개 서비스 안내 캡처와 Supabase SQL 다운로드의 사용 범위를 설명합니다. 캡처는 로그인·쿠키·로컬 프로필이 없는 새 Chromium 세션에서 공식 공개 페이지를 열어 얻었습니다. 캡처 스크립트는 페이지를 읽기만 하고, 버튼 클릭·폼 제출·가입·결제·키 발급·파일 다운로드를 하지 않습니다.

## 공개 안내 캡처

고정 guide ID 35개 각각에 `/guides/{id}.webp` 첫 화면 캡처를 제공합니다. 실제 요청 URL, 최종 이동 URL, 페이지 제목, 확인 날짜, HTTP 상태, fallback 사용 여부는 [manifest.json](/home/jimmy/.paseo/worktrees/13nkmqul/simple-mode-web/web/public/guides/manifest.json)에 기록했습니다. `captured`는 입력한 공식 URL, `fallback`은 표시된 기본 URL이 막히거나 렌더링되지 않아 목록에 지정한 공식 대체 문서를 사용한 경우입니다. manifest의 URL과 캡처는 공개 문서 페이지의 확인 증거일 뿐, 사용자의 가입·결제·설치·연결 상태를 증명하지 않습니다. 공개되지 않은 계정 화면이나 비밀 값은 캡처하지 않았습니다.

캡처를 다시 만들 때는 아래 명령을 사용합니다. 설치된 Playwright와 Sharp를 사용하며, `CHROME_BIN`을 지정하지 않으면 Playwright 브라우저가 있거나 시스템 Chrome 경로를 찾습니다. 브라우저 바이너리나 npm 패키지는 이 스크립트가 설치하지 않습니다.

```sh
cd web
node scripts/capture-guides.mjs
```

한 가이드만 갱신하려면 해당 ID를 넘깁니다. 예: `node scripts/capture-guides.mjs jev`. 기존 manifest의 다른 항목과 이미지를 유지하며 해당 ID만 새로 캡처합니다.

공식 페이지가 차단되면 스크립트의 공식 공개 문서 fallback을 시도합니다. fallback도 실패하면 임의 이미지를 만들지 않고 `screenshot: null`, `result: "failed"`로 기록하며 종료 코드를 실패로 설정합니다. 구현은 [capture-guides.mjs](/home/jimmy/.paseo/worktrees/13nkmqul/simple-mode-web/web/scripts/capture-guides.mjs)입니다.

## Supabase: 관리자 SQL RPC 설치

Supabase Postgres 함수는 데이터베이스 안에서 실행되며 앱에서는 `rpc()`로 호출합니다. Edge Function은 별도 서버 런타임에서 실행되므로 이 SQL 다운로드의 대상이 아닙니다. [Supabase 데이터베이스 함수 안내](https://supabase.com/docs/guides/database/functions)와 [API 키 문서](https://supabase.com/docs/guides/getting-started/api-keys)를 함께 확인하세요.

먼저 Supabase Dashboard에서 프로젝트를 선택하고 **SQL Editor → New query**를 엽니다. [supabase-admin-sql-install.sql](/home/jimmy/.paseo/worktrees/13nkmqul/simple-mode-web/web/public/downloads/supabase-admin-sql-install.sql)의 내용을 직접 붙여 넣어 한 번 실행합니다. 이는 프로젝트 소유자로 로그인한 사람이 해야 하는 계정 단계이며 Simple Mode가 대신 실행하지 않습니다. 설치 SQL 전체는 트랜잭션 안에서 적용됩니다.

설치 파일은 `public.simple_mode_admin_sql(p_sql text)` 데이터베이스 함수를 만듭니다. 고정된 빈 `search_path`, 완전히 지정된 함수 이름, `SECURITY DEFINER`를 설정합니다. 재설치 시 기존 함수만 `DROP`한 뒤 다시 생성하므로 이전에 어떤 custom role에 직접 부여한 실행 grant도 남지 않습니다. 기존 객체가 이 함수에 의존하면 `CASCADE` 없이 설치 전체가 실패하고 롤백됩니다. 새 함수는 `PUBLIC`, `anon`, `authenticated`의 실행 권한을 회수하고 `service_role`만 실행하도록 허용하며, Supabase의 JWT role claim도 `service_role`인지 확인합니다. 성공 응답은 `{ "ok": true, "rows_affected": ... }`입니다. 이는 문장이 DB에서 오류 없이 실행됐다는 응답이며, 별도의 read-back 확인과는 구분됩니다.

이 함수는 함수 소유자인 `postgres` 권한으로 전달된 SQL을 실행합니다. 따라서 임의 SQL 입력자는 데이터와 스키마를 변경·삭제할 수 있고 RLS도 우회할 수 있습니다. Supabase의 `SECURITY DEFINER` 안내가 설명하는 권한 모델 그대로이므로 신뢰 가능한 서버에서만 호출하고, 사용자 입력을 그대로 SQL로 보내면 안 됩니다. 프론트엔드·브라우저·배포된 앱에 Supabase secret key 또는 과거 `service_role` 키를 넣지 마세요. 서버에 별도의 사용자 권한 확인, 허용된 쿼리 정책, 요청 제한, 감사 로그를 마련한 뒤에만 사용해야 합니다.

예를 들어 서버에서 허가된 관리 작업을 호출하는 형태는 다음과 같습니다. 실제 URL이나 키는 웹사이트 폼·Zustand·브라우저 저장소에 입력하거나 보관하지 않습니다.

```ts
const { data, error } = await supabaseAdmin.rpc('simple_mode_admin_sql', {
  p_sql: 'CREATE TABLE IF NOT EXISTS public.example_records (id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, note text NOT NULL)',
});
```

각 RPC 요청에는 최상위 SQL 문장 하나를 전달합니다. `SELECT`의 행 결과는 버리고 상태 JSON만 반환합니다. 권한·테이블 설정 문장은 분리해 보내고, 각 작업 뒤 별도 읽기 전용 조회로 실제 상태를 확인하세요. 함수 실행 중 문장이 오류를 내면 해당 RPC 트랜잭션이 실패합니다. 이 경로가 적합하지 않으면 Dashboard SQL Editor나 관리자가 통제하는 마이그레이션으로 직접 작업하세요. Management API는 다른 관리 인터페이스이며 이 데이터베이스 RPC를 대신 설치하거나 대체하는 경로로 이 가이드에서 취급하지 않습니다.

설치 상태는 [supabase-admin-sql-check.sql](/home/jimmy/.paseo/worktrees/13nkmqul/simple-mode-web/web/public/downloads/supabase-admin-sql-check.sql)을 Dashboard SQL Editor에서 실행해 확인합니다. 이 read-only 점검은 함수 존재, `SECURITY DEFINER`, `postgres` 소유권, 빈 `search_path`, `service_role` 실행 허용, `PUBLIC`·`anon`·`authenticated` 실행 불가, owner와 `service_role` 외 직접 grant 및 `service_role`에서 상속된 실행 권한 없음까지 표시합니다. 모든 조건이 참일 때 `overall_status`가 `PASS`입니다. 이 점검은 함수를 호출하거나 권한을 변경하지 않습니다.

제거하려면 [supabase-admin-sql-uninstall.sql](/home/jimmy/.paseo/worktrees/13nkmqul/simple-mode-web/web/public/downloads/supabase-admin-sql-uninstall.sql)을 SQL Editor에서 실행합니다. 함수만 삭제하며 이를 통해 만든 테이블·데이터·다른 권한은 유지됩니다. 데이터 삭제가 필요하면 별도 마이그레이션을 검토하고 사용자가 직접 수행해야 합니다.

## 근거 자료

- [Supabase Database Functions](https://supabase.com/docs/guides/database/functions): `rpc()` 호출, `SECURITY DEFINER` / `SECURITY INVOKER`, 빈 `search_path`, 함수별 execute grant 및 SQL Editor 안내.
- [Supabase API Keys](https://supabase.com/docs/guides/getting-started/api-keys): publishable key와 secret key의 역할, secret key는 backend에서만 사용, 구형 `service_role` 키 전환 안내.
- [Supabase Securing your data](https://supabase.com/docs/guides/database/secure-data): 공개 프런트엔드 키에는 RLS와 최소 권한 적용, secret/service-role 키를 클라이언트에 노출하지 말라는 안내.
