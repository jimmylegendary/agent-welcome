# 현행 제품 결정

상태는 `confirmed`(사용자 확정), `engineering`(이번 구현의 기술 선택), `open`(미정), `superseded`(대체됨)로 구분한다. 구현은 이 목록과 해당 recipe 계약을 우선하며, 조사 문서의 제안을 자동으로 확정 요구로 바꾸지 않는다.

| ID | 상태 | 결정 | 대체·제한하는 내용 |
|---|---|---|---|
| D-001 | confirmed | macOS·Windows·iOS·Android **각각에서 Claude Code·Codex·Prime Agent 모두**를 지원 목표로 한다. | OS별 하나만 제공하는 축소 해석은 채택하지 않음. 목표와 실제 검증 상태는 분리. |
| D-002 | confirmed | GUI와 기능의 제약은 agent·OS 조합별로 별도 표시한다. | 모든 GUI가 모든 agent를 제어한다는 가정은 하지 않음. |
| D-003 | confirmed | 기존 agent를 기기 안에서 실행하는 경로를 우선한다. | 자체 agent 앱으로 대체하거나 원격 host로 바꾸는 초기 대안은 미채택. 원본 구현과 수정 없는 binary는 별도 개념. |
| D-004 | confirmed | 공식 문서·블로그·GitHub의 조건과 예외를 KG로 만들고 설치·진단·복구에 사용한다. | 문서에 존재한다는 사실과 실제 실행 성공을 구분. |
| D-005 | confirmed | 이번 작업은 리뷰 수정, 정형 데이터, 단일 recipe의 reference implementation까지 진행한다. | 실제 휴대폰 성공이나 12개 조합의 구현 완료를 이번 결과로 선언하지 않음. |
| D-006 | open | 모델 추론 API 사용은 현재 설계의 잠정 전제다. | 독립 host를 모든 추론의 offline 실행과 같은 뜻으로 확정하지 않음. |
| D-007 | open | Jimmy's Agent Skills 기본 설치는 목표이며 정확한 목록은 출처·재배포 조건·호환성 정리 후 확정한다. | 연구자의 작은 기본 팩 권고는 구성 확정이 아님. |
| D-008 | engineering | 첫 reference는 Prime Agent v0.10.0 Linux ARM64 artifact의 **binary 설치 단계**다. Python 3.11+ 표준 라이브러리로 구현한다. | 모바일 guest에서 쓰일 Linux userland 조건을 다루며 Python·API 인증·전체 agent task 성공과 분리. |
| D-009 | engineering | 일반 진단은 변경 없이 실행한다. 설치 실행은 명시한 상태 디렉터리 안에서 수행하며 기본적으로 원본 배포 파일을 변경하지 않는다. | official installer의 전역 daemon 종료·기존 설치 교체·npm 제거를 호출하지 않음. |
| D-010 | engineering | artifact 미제공 시 `WAITING_USER`로 저장하고 파일 제공 후 이어간다. `--download`를 선택하면 고정 URL에서 자동 취득할 수 있다. | 사용자 대기를 실패나 재시도 소진으로 처리하지 않음. MFA 대기 상태도 같은 상태 저장 계약으로 다룸. |
| D-011 | engineering | `SUCCEEDED`는 recipe가 선언한 범위와 모든 필수 check를 만족한 경우에만 사용한다. | binary 설치 성공을 인증·kernel·첫 작품 완성으로 확대하지 않음. |

이번 기술 선택은 첫 reference 범위에 한정된다. 웹사이트·배포 앱의 최종 stack과 첫 결과물 팩은 아직 확정하지 않았다.
