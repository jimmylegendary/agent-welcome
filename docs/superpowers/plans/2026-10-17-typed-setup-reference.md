# Typed Setup Reference Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Follow the task scope and record red/green evidence. Do not delegate again.

**Goal:** 리뷰에서 지적된 문서·KG 조건을 바로잡고 Prime binary 설치 recipe를 독립 실행·대기·재개할 수 있게 한다.

**Architecture:** JSON catalog와 typed predicate evaluator가 적용 조건과 필수 check를 판정한다. 별도 Python runner가 상태를 원자적으로 저장하고 고정된 artifact action을 수행한다. KG는 제한된 관계 vocabulary와 source/claim/recipe 연결을 제공한다.

**Tech Stack:** Python 3.11+ standard library, JSON, unittest. 외부 runtime dependency 없음.

**Spec:** [reference-implementation.md](https://github.com/jimmylegendary/agent-welcome/blob/feat/typed-setup-reference/docs/reference-implementation.md)

## Global Constraints

- 4 OS × 3 agent 전체 지원이 제품 목표. 이 reference는 Linux userland의 Prime binary installation 범위.
- current checks / observed download digest / source-published digest를 분리한다.
- 사용자 대기와 적용 대상 아님, 지원 불가, 실행 실패, 정보 부족을 구분한다.
- code/data/schema는 자기 파일 범위만 수정한다. 외부 설치·credential·daemon 조작·기기 실행 금지.
- 테스트는 네트워크·실제 agent 없이 실행. 전체 suite는 `python3 -m unittest discover -s tests -v`.
- Git commit은 root가 통합 단위로 수행한다. worker는 commit/push하지 않는다.

## Review Focus

- 비정상 condition 입력을 true로 해석하거나 unknown을 지원으로 승격시키지 않는지: evaluator tests.
- download·archive 경로가 지정한 state directory 밖 파일에 영향을 주지 않는지: archive adversarial tests.
- 이미 성공한 version/digest를 stale recipe/environment에서 재사용하지 않는지: drift/resume tests.
- 대기와 process interruption이 시도 횟수·필수 check를 잃게 하지 않는지: persisted restart tests.
- KG에서 Codex required sandbox가 context recipe 소비 시 누락되지 않는지: catalog dependency tests.

## Task 1: 사실·결정·출처 정리

**Owner:** master.

**Files:** `DECISIONS.md`, `docs/reference-implementation.md`, `catalog/source-evidence.json`, `android-original-agent-validation.md`, `START-HERE.md`, `workflow-skill-research.md`, `local-skills-audit.md`.

- [x] 고정 tag의 Codex parser와 Prime installer 및 Codux README 근거 확인.
- [x] 잘못된 sandbox probe와 확인되지 않은 휴대폰 모델 서술 제거.
- [x] 최신 제품 결정을 조사 제안보다 우선하도록 문서 연결.
- [x] source commit/content hash/location/claim을 source evidence에 저장.

## Task 2: 정형 catalog, 실행기, regression tests

**Owner:** implementation worker. 파일 간 인터페이스가 밀접하므로 한 worker가 순차 구현한다.

**Files:** `agent_welcome/__init__.py`, `agent_welcome/__main__.py`, `agent_welcome/catalog.py`, `agent_welcome/environment.py`, `agent_welcome/artifacts.py`, `agent_welcome/runner.py`, `recipes/prime-agent-0.10.0-linux-arm64.json`, `kg/graph.json`, `schemas/`, `tests/`.

**Interfaces:**
- `catalog.load_catalog(path)` / `validate_catalog(data)`는 controlled relations, typed conditions, artifact/source/route/playbook/check 참조를 검사한다.
- `catalog.evaluate_condition(condition, observations)`은 pass/fail/unknown과 missing facts/reason을 반환한다.
- `catalog.evaluate_route(catalog, route_id, observations, check_results)`는 모든 필수 check 의존성을 적용한다.
- `environment.observe()`는 실제 현재 kernel/OS/CPU/runtime/libc 관측과 provenance를 반환한다.
- `runner.start(...)`, `runner.resume(...)`, `runner.status(...)`는 spec의 상태 기록을 반환한다. 인자·내부 자료형은 구현 시 하나로 정하고 tests/CLI에서 일관되게 사용한다.
- `artifacts`는 bounded download, digest, safe extraction, owned payload version probe만 구현한다.

- [x] Prime glibc 조건, unknown/invalid condition, Codex sandbox dependency, OAuth stage 분리의 실패 테스트를 먼저 작성하고 RED 기록.
- [x] KG schema 0.2와 5개 playbook typed bindings, controlled relations, connected Claude route, structured release facts를 작성.
- [x] evaluator/validator를 구현하고 관련 tests GREEN.
- [x] missing artifact → WAITING_USER → supply → digest/extract/version → SUCCEEDED의 실제 fixture file cycle 테스트를 먼저 작성하고 RED 기록.
- [x] atomic state, idempotent resume/reconciliation, retry budget/lock, drift 판정 구현.
- [x] checksum mismatch, archive abuse, version failure, missing required check, MFA wait, interruption/concurrent run의 failure tests와 최소 구현.
- [x] CLI validate/diagnose/start/resume/status 구현. 외부 observation은 diagnose 전용.
- [x] 전체 unittest suite와 CLI no-agent validate/diagnose 실행. command·counts·output을 report에 기록.

## Task 3: 별도 review와 master 검증·GitHub 반영

**Owner:** 별도 reviewer, master.

**Files:** 구현 diff 전부 read-only review; master는 `README.md`, `docs/implementation-results.md`와 ledger 통합 담당.

- [x] reviewer가 spec와 code를 대조하고 중요 결함을 구현 worker에게 돌려준다.
- [x] 수정한 범위 재검토 후 master가 전체 suite와 실제 CLI를 실행한다.
- [x] 12개 OS/agent 목표와 구현·실증 상태를 혼동하지 않도록 README/결과 기록 갱신.
- [ ] source links, JSON references, whitespace, Git 상태를 검증하고 commit/push 후 원격 SHA 확인.

## Preflight interface scan

| 경계 | 생산 → 소비 | 판정 |
|---|---|---|
| Task 1 → Task 2 | source-evidence의 고정 source/claim → graph와 pinned recipe | source 파일은 master 완료 후 고정. worker는 수정하지 않음. |
| catalog → runner | typed eligibility/required checks → 실제 action과 completion | unknown은 성공 불가, checks 누락 시 성공 불가. |
| artifacts → runner | digest/path/version evidence → ledger | evidence 없이 단계 완료 표시 금지. |
| Task 2 → Task 3 | code+tests+red/green report → 독립 review | reviewer는 파일 수정하지 않음. |
| Task 1 자체 | 문서 수정·근거 확인 | 본문과 KG에 같은 pinned version 사용. |
| Task 2 자체 | fixture test와 실제 adapter | fixture 성공은 기기 성공과 별도 표시. |
| Task 3 자체 | 코드 검증과 공개 상태 | 명령 실행 여부·증거 범위에 맞게 완료 보고. |
