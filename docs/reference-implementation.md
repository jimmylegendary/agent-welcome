# Typed setup reference specification

사용자 확정 범위는 [DECISIONS.md](https://github.com/jimmylegendary/agent-welcome/blob/feat/typed-setup-reference/DECISIONS.md)를 따른다. 이 변경은 기존 연구 seed의 기계 판정 가능한 조건을 보강하고 대상 agent가 없어도 동작하는 첫 설치 실행기를 만든다.

## 데이터 계약

- KG schema `0.2`. 기존 관계의 상세 의미는 `details.original_relation`에 보존하고 작은 고정 relation vocabulary로 정규화한다.
- 모든 playbook은 agent, symptom, diagnostic, route, required check ID를 명시한다. Claude도 최소 한 조사 route와 연결한다.
- artifact에는 agent/version/target/고정 URL/published SHA-256/size를 저장한다. 다운로드 시 관측한 SHA-256은 run record의 별도 값이다.
- Prime v0.10.0 Linux ARM64: `aarch64`, GNU/glibc, **glibc >= 2.35**, archive `prime-agent-0.10.0-linux-arm64.tar.gz`, published SHA-256 `f3cab3530a4d7ca43dbef8321bf13f260d1ba05d8b5dde057165a20bd4f675c4`, 21858488 bytes.
- 조건은 자연어의 재해석 없이 `all`, `any`, `eq`, `in`, `version_gte`로 판정한다. 관측이 없으면 unknown이다. 지원하지 않는 연산자나 잘못된 자료형은 검증 오류다. `2.9 < 2.35`, `2.35 == 2.35.0`으로 비교한다.
- `observations`는 OS/kernel/CPU/runtime/libc/capabilities/auth 단계 등을 구조화한다. `kernel_os`와 확인 가능한 `host_os`는 별개다. 공개 API와 CLI는 알려진 필드의 자료형을 검증하며, 잘못된 자료형을 관측 누락과 구분한다. 외부 파일 관측은 진단용이며 실제 설치 CLI는 현재 실행 환경을 새로 관측한다.
- Codex PRoot 경로는 artifact/version/read-only 확인 외에 sandbox check를 반드시 요구한다. 다른 playbook 소비 시에도 이 요구를 상속한다. source와 version을 확인한 probe는 `codex sandbox -- /bin/true`; permission profile은 별도 명시 필드이며 미지정 상태를 보안 검증 통과로 취급하지 않는다.
- callback/headless와 callback 이후 token exchange 실패는 다른 조건이다. MFA/login 입력은 `WAITING_USER`이며 실패/지원 불가와 구분한다.
- 모든 자동 실행 여부와 device/runtime 검증 이력은 근거에 맞게 유지한다. 코드가 존재한다는 이유로 기존 조합의 `runtime_tested`를 true로 바꾸지 않는다.

## Reference recipe와 실행 범위

첫 실제 action adapter는 고정된 Prime archive를 내려받거나 제공받아 hash를 확인하고, 지정한 상태 디렉터리의 소유한 설치 영역에 추출한 뒤 해당 payload의 `--version`을 검사한다. 외부 source 문자열을 shell로 실행하지 않으며 upstream installer script를 실행하지 않는다.

`SUCCEEDED`의 범위는 **binary_installation**이다. provider 인증, Python kernel 초기화, 실제 모델 작업은 확인하지 않은 check로 명시한다. artifact가 없고 자동 다운로드를 선택하지 않으면 공식 다운로드 위치와 필요한 입력을 안내하고 `WAITING_USER(artifact_file)`로 종료한다. 파일을 제공한 resume은 이미 통과한 단계들을 재검증·조정하며 필요 없이 재설치하지 않는다.

기본 CLI:

```text
python3 -m agent_welcome validate
python3 -m agent_welcome diagnose --recipe prime-agent-0.10.0-linux-arm64 [--observations FILE]
python3 -m agent_welcome start --recipe prime-agent-0.10.0-linux-arm64 --state-dir DIR [--artifact-file FILE | --download]
python3 -m agent_welcome resume --state-dir DIR [--artifact-file FILE | --download]
python3 -m agent_welcome status --state-dir DIR
```

외부 observations 파일은 diagnose에만 사용한다. start/resume은 실제 환경을 관측한다. CLI는 JSON으로 판정과 다음 행동, 완료/미검증 check를 반환한다. 대상 agent, LLM credential, graph DB가 없어도 validate/diagnose/status가 동작해야 한다.

## 상태와 재개

상태 집합은 `READY`, `RUNNING`, `WAITING_USER`, `SUCCEEDED`, `NOT_APPLICABLE`, `UNSUPPORTED`, `FAILED`, `NEEDS_DIAGNOSIS`다. action 실행 이전과 이후에 상태를 원자적으로 저장한다. 단계별 최대 2회, run 전체 최대 6회의 실제 action 시도를 허용하고, 대기 상태 조회는 시도 횟수를 증가시키지 않는다.

저장 내용: recipe ID/version/hash, 관측 fingerprint, current step, completed steps, required check 결과와 evidence, supplied artifact의 observed digest, wait reason/resume 위치, 단계별·전체 attempt 수. 비밀번호·token·authorization code를 저장하지 않는다.

recipe 또는 핵심 환경 fingerprint가 바뀌면 기존 성공을 그대로 재사용하지 않는다. 설치가 중단되었으면 소유한 임시 영역과 설치 manifest를 확인하여 재개한다. checksum, version 또는 필수 capability 검증 실패를 success로 승격시키지 않는다. 지원 불가에는 재시도하지 않는다. 동시 실행은 상태 디렉터리 lock으로 막고 프로세스 종료 뒤 재개할 수 있어야 한다.

runner가 구현하지 않은 필수 check는 recipe validation에서 거절한다. 최초 실행과 reconciliation의 모든 성공 경로에서 recipe가 요구하는 check 전체를 확인한다. Codex 연구 경로는 실행 runtime이 알려지지 않았거나 sandbox permission profile이 확인되지 않았으면 `pass`로 판정하지 않는다.

## 파일·실행 계약

- 실제 변경은 `--state-dir` 내부로 제한한다. 임의 기존 설치·전역 PATH·서비스·계정 설정을 바꾸지 않는다.
- SHA-256이 맞지 않으면 추출이나 실행을 하지 않는다. 파일이 존재하는 것만으로 verification을 통과시키지 않는다.
- 외부 archive는 byte 상한을 적용한 private snapshot으로 취득한다. hash 검증과 추출에는 동일한 snapshot bytes를 사용하여 원본 경로 교체나 변경에 영향을 받지 않는다.
- archive는 상대 경로의 regular file/directory만 허용한다. 절대 경로, `..`, symlink/hardlink, device/FIFO, 중복 경로와 파일/디렉터리 충돌을 거부한다. member 수와 총 uncompressed byte 상한을 둔다.
- download에는 timeout과 byte 상한을 둔다. URL과 단일 archive 파일명은 pinned artifact와 일치해야 한다. 최종 경로의 state directory containment도 확인한다. 공급자가 게시한 hash를 actual download hash와 별도로 기록한다.
- staging 정리는 생성한 경로와 run 소유권을 확인한 항목에만 적용한다. 이름의 prefix만 같은 미등록 파일·폴더를 지우지 않는다.
- version probe는 검증한 owned payload를 argv 배열로 호출하고 `shell=True`를 사용하지 않는다. timeout/실패/기대 version 불일치를 기록한다. 종료 코드 0만으로 판정하지 않는다.
- 이 first reference는 Linux userland 설치를 실행한다. 다른 OS에서도 진단은 가능하지만 이 artifact가 맞지 않으면 `NOT_APPLICABLE`이다. 이는 제품의 4 OS 목표를 축소하지 않는다.

## 테스트와 증거

표준 `unittest`를 사용한다. 외부 다운로드·실기기·LLM credential 없이 temporary directory의 fixture archive와 무해한 version probe로 파일·상태 side effect를 검증한다. fixture 결과를 실제 Prime/Android/iOS 성공이라고 기록하지 않는다.

필수 failure cases: glibc 2.31 부적합 및 2.35/2.9 비교, 누락 관측 unknown, 잘못된 condition operator, checksum 불일치 시 무실행, archive traversal/link/중복 거부, version mismatch, sandbox 필수 gate 누락, callback/token exchange 분리, MFA 대기 중 이전 check 보존, 중단 후 재개, 반복 resume의 비중복 변경, retry budget 재시작 보존, recipe/environment drift, 동시 run 거부.
