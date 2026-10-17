# Agent Welcome 작업 규칙

- 현행 제품 계약은 [DECISIONS.md](https://github.com/jimmylegendary/agent-welcome/blob/feat/typed-setup-reference/DECISIONS.md), reference 구현 계약은 [reference-implementation.md](https://github.com/jimmylegendary/agent-welcome/blob/feat/typed-setup-reference/docs/reference-implementation.md)를 따른다. 과거 조사 문서의 제안을 확정 요구로 승격하지 않는다.
- 목표는 4개 OS 각각에서 세 agent 모두를 독립 host로 제공하는 것이다. 구현한 단일 recipe나 fixture 시험을 12개 조합의 실제 지원 완료로 보고하지 않는다.
- 판정 조건·필수 check·대기/실패/지원 불가 상태는 정형 데이터와 코드로 처리한다. source의 명시, 추론, 직접 관측은 구분한다.
- 전체 검증 명령은 `python3 -m unittest discover -s tests -v`다. 실제 agent·credential·휴대폰 없이 수행한 fixture 시험은 그 범위로 보고한다.
- runtime 명령은 사용자에게 명시한 state directory 안의 작업만 수행한다. 외부 설치기 script, 전역 서비스·PATH·계정 설정을 자동 변경하지 않는다.
