# Typed setup reference 검증 기록

기준일: 2026-10-17. 사용자 확정 범위는 **4개 OS 각각에서 3개 원본 agent 지원을 목표**로 유지하면서, 리뷰 수정·정형 데이터·단일 recipe reference를 구현하는 것이다. GUI·기능별 제한은 별도로 표시한다.

## 변경 내용

- Codex `rust-v0.159.1`의 sandbox probe를 `codex sandbox -- /bin/true`로 정정했다. permission profile의 명시와 실행 증거가 없는 상태는 sandbox 검증 통과가 아니다.
- 고정 Codux README에서 뒷받침되지 않는 특정 휴대폰 기종 성공 주장을 제거했다.
- [DECISIONS.md](https://github.com/jimmylegendary/agent-welcome/blob/feat/typed-setup-reference/DECISIONS.md)에 현행 결정과 미정 사항을 기록하고 12개 필수 지원 목표를 별도 catalog로 만들었다.
- KG schema 0.2에는 88개 node, 145개 link, 10개 relation type, 5개 playbook이 있다. 기존 관계의 설명을 보존하면서 공통 relation과 조건·필수 check를 분리했다. Claude 연결, Codex sandbox 의존성, OAuth 단계별 진단, Prime의 version·digest·glibc 조건을 정형화했다.
- 대상 agent 없이 동작하는 Python 표준 라이브러리 CLI를 만들었다. Prime v0.10.0 Linux ARM64·glibc >= 2.35 recipe가 `WAITING_USER → archive 확인 → 추출 → version 확인 → SUCCEEDED`를 저장·재개한다.
- archive hash mismatch, 경로 탈출·link·중복·크기 초과, version mismatch, recipe/environment drift, 동시 실행을 판정한다. 잘못된 archive 이후 교체, 설치 중단 이후 조정, 설치 파일 변경 이후 성공 무효화도 처리한다.

`kernel_os`는 실행 환경이고 `host_os`는 확인된 host다. PRoot 관측만으로 물리 host를 Android로 추정하지 않는다. Prime recipe의 Linux 조건과 Android/iOS 연구 경로의 host 조건을 구분한다.

## 첫 snapshot의 master 실행 증거

검증 snapshot: `6fda71e7deb53290399e36789155214b0a137c26`.

| 명령 | 환경 | 실제 결과 |
|---|---|---|
| `python3.14 -m unittest discover -s tests -v` | Python 3.14.3, Linux x86_64 | exit 0, `Ran 34 tests`, `OK` |
| `python3.11 -m unittest discover -s tests -v` | Python 3.11.14, Linux x86_64 | exit 0, `Ran 34 tests`, `OK` |
| `python3.11 -m agent_welcome validate` | 대상 agent·credential 불필요 | exit 0, `VALID`, schema 0.2, 82 nodes / 106 links / 5 playbooks |
| `python3.11 -m agent_welcome diagnose --recipe prime-agent-0.10.0-linux-arm64` | 실제 Linux x86_64 관측 | exit 0, `NOT_APPLICABLE` |
| `start`, `status`, `resume`을 임시 `--state-dir`에 순서대로 실행 | 실제 Linux x86_64 관측 | 각 exit 0, `NOT_APPLICABLE`, attempts total 0, completed steps 없음, observed digest null |
| `git diff --cached --check` | snapshot commit 직전 | exit 0, 출력 없음 |

테스트는 temporary directory의 작은 tar와 무해한 version script를 사용한다. 정상 경로뿐 아니라 조건 누락·오류, 필수 sandbox check 누락, callback/token exchange 구분, user wait, archive 거부, 재시도 상한과 중단·변조 복구를 검사한다. `--observations`는 진단에서만 허용하고 실제 설치 CLI에서는 거부한다.

구현 worker의 최초 RED 실행은 package가 없는 상태에서 `Ran 5 tests`, import error 3건·validate failure 1건이었다. 이것은 기능별 회귀 테스트가 모두 개별적으로 실패하는 것을 관측했다는 뜻이 아니다. 이후 worker와 master가 해당 snapshot의 suite를 각각 실행했다.

## 독립 검토와 회귀 검증

별도 reviewer가 첫 snapshot에서 P1 2건과 P2 5건을 임시 fixture로 재현했다. 기존 34개 테스트 통과만으로 완료하지 않고 다음 수용 기준을 추가했다.

| 재현된 문제 | 수정 수용 기준 |
|---|---|
| archive 파일명으로 state 밖 경로 접근, pinned URL 변경 허용 | 안전한 단일 파일명·containment·source binding 확인, 거절 시 기존 파일 보존 |
| hash 확인 후 외부 archive 변경 | bounded private snapshot의 동일 bytes를 검사·추출 |
| prefix만 같은 staging 폴더 삭제 | 생성한 정확한 경로와 소유권을 확인한 항목만 정리 |
| 미구현 필수 check를 무시한 성공 | 지원하지 않는 check 거부, 모든 성공 경로에서 필수 check 전체 확인 |
| Codex의 integrity/read-only/profile 및 runtime 의존성 누락 | 필수 gate 상속, 미관측 runtime/profile은 unknown |
| `True`와 `1`을 혼동하는 `in` 비교 | 후보별 자료형과 값 모두 일치해야 pass |
| malformed observation이 READY로 판정됨 | CLI와 공개 API에서 알려진 필드 자료형 검증 |

수정 전 추가 회귀 실행은 `python3 -m unittest discover -s tests -q`에서 exit 1, `Ran 47 tests`, failures 14 / errors 2였다. 기존 구현이 이미 통과하던 `PI_PACKAGE_DIR` 격리 시험은 실패를 재현한 항목과 구분한다.

## 수정 snapshot의 master 검증

검증 snapshot: `662b1bb4265f78a4ad35836ad13b1f597062c917`.

| 명령·검사 | 실제 결과 |
|---|---|
| `python3.14 -m unittest discover -s tests -v` (Python 3.14.3) | exit 0, `Ran 49 tests`, `OK`; 개별 ok 49개 |
| `python3.11 -m unittest discover -s tests -v` (Python 3.11.14) | exit 0, `Ran 49 tests`, `OK`; 개별 ok 49개 |
| `python3.11 -m agent_welcome validate` | exit 0, `VALID`, schema 0.2, 88 nodes / 145 links / 5 playbooks |
| 실제 host `diagnose`, 임시 state directory의 `start` → `status` → `resume` | 각 exit 0, Linux x86_64에서 `NOT_APPLICABLE`; 설치 시도 0회, observed digest null |
| 고정 source record 7개의 KG 복사본 대조 | 모든 원본 필드 일치, 차이 0개 |
| 지원 목표와 검증 상태 대조 | 12개 모두 required=true / runtime_verified=false; KG 자동 실행·실기기 재현 false 유지 |
| `git diff --cached --check` | exit 0, 출력 없음 |

## 마지막 경계 수정과 검증

별도 reviewer는 `662b1bb`에서 이전 7건이 차단됨을 독립 fixture로 확인했다. 이어서 수정 경계의 P2 3건을 재현했다. 허용된 `provenance: null`에서의 예외, observer의 `linux_userland`를 auth route가 거절하는 조건, FIFO를 regular file로 검사하기 전 `open()`에서 멈추는 경우다.

각각 예외·route fail·subprocess timeout의 RED를 확인하고 null 보존, runtime 조건 일치, nonblocking open 후 descriptor 검사를 적용했다. 세 개의 회귀 테스트를 더했다.

검증 snapshot: `ac2a8f2c5c72330a1884416f4bf9922a096d9771`.

| 명령 | 실제 결과 |
|---|---|
| `python3.14 -m unittest discover -s tests -v` (Python 3.14.3) | exit 0, `Ran 52 tests`, `OK`; 개별 ok 52개 |
| `python3.11 -m unittest discover -s tests -v` (Python 3.11.14) | exit 0, `Ran 52 tests`, `OK`; 개별 ok 52개 |
| `python3.11 -m agent_welcome validate` | exit 0, `VALID`, 88 nodes / 145 links / 5 playbooks |
| `git diff --cached --check` | exit 0, 출력 없음 |

같은 reviewer가 `ac2a8f2`의 세 수정과 직접 영향을 받는 경계를 재확인했다. Python 3.14.3에서 직접 실행한 7개 시험이 모두 통과했고 failure/error/skip은 0이었다. 이전 7건의 해결 판정을 유지하며, 지정 검토 범위에 잔여 P1/P2는 없었다. 전체 52개 suite는 위 표의 master 실행 증거다.

## 증거 범위와 남은 작업

`SUCCEEDED`의 범위는 **binary_installation**이다. 실제 upstream Prime archive 다운로드·bytes hash 대조·ARM64 binary 실행, provider 로그인, Python kernel 초기화, 모델 작업, 네 OS 실기기 설치는 이번 검증에 포함하지 않았다. published SHA-256과 fixture 실행 때의 observed digest를 구분한다. 12개 지원 목표의 runtime 검증 표시는 여전히 false다.

고정한 source 7개와 claim 9개는 실행 조건의 핵심 근거다. 이전 연구 source 19개는 `legacy_unresolved`로 보존했으며 전체 연구 자료의 revision 고정을 완료한 상태는 아니다. 초기 [GRAPH_REPORT.md](https://github.com/jimmylegendary/agent-welcome/blob/ab4b7c3abc5a84a3eb6af3cbc184bf8e5327c688/kg/GRAPH_REPORT.md)와 [verification.md](https://github.com/jimmylegendary/agent-welcome/blob/ab4b7c3abc5a84a3eb6af3cbc184bf8e5327c688/verification.md)의 개수·hash는 당시 연구본의 기록이다.

runner가 관리하는 파일은 지정 state directory에 둔다. version subprocess는 검증한 payload를 제한된 환경 변수와 timeout으로 실행하지만 OS sandbox로 감싸지는 않는다. fixture 시험은 외부 binary의 임의 동작까지 제한한다는 보증이 아니다.

이 reference는 배포용 설치 앱이나 전 OS 설치기 완성본이 아니다. GUI·인증·첫 결과물 흐름과 기기별 adapter는 후속 구현 대상이다. 실행 계약은 [reference-implementation.md](https://github.com/jimmylegendary/agent-welcome/blob/feat/typed-setup-reference/docs/reference-implementation.md)에 있다.
