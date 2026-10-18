# 현행 제품 결정

상태는 `confirmed`(사용자 확정), `engineering`(이번 구현의 기술 선택), `open`(미정), `superseded`(대체됨)로 구분한다. 구현은 이 목록과 해당 recipe 계약을 우선하며, 조사 문서의 제안을 자동으로 확정 요구로 바꾸지 않는다.

| ID | 상태 | 결정 | 대체·제한하는 내용 |
|---|---|---|---|
| D-001 | confirmed | macOS·Windows·iOS·Android **각각에서 Claude Code·Codex·Prime Agent 모두**를 지원 목표로 한다. | OS별 하나만 제공하는 축소 해석은 채택하지 않음. 목표와 실제 검증 상태는 분리. |
| D-002 | confirmed | GUI와 기능의 제약은 agent·OS 조합별로 별도 표시한다. | 모든 GUI가 모든 agent를 제어한다는 가정은 하지 않음. |
| D-003 | confirmed | 기존 agent를 기기 안에서 실행하는 경로를 우선한다. | 자체 agent 앱으로 대체하거나 원격 host로 바꾸는 초기 대안은 미채택. 원본 구현과 수정 없는 binary는 별도 개념. |
| D-004 | confirmed | 공식 문서·블로그·GitHub의 조건과 예외를 KG로 만들고 설치·진단·복구에 사용한다. | 문서에 존재한다는 사실과 실제 실행 성공을 구분. |
| D-005 | superseded | 첫 구현은 리뷰 수정, 정형 데이터, 단일 recipe의 reference implementation이었다. 이후 작업 범위는 D-013으로 확장한다. | 실제 휴대폰 성공이나 12개 조합의 구현 완료를 선언하지 않는 원칙은 유지. |
| D-006 | confirmed | Simple Mode는 OpenAI/OpenRouter 모델 API와 요청된 cloud DB·n8n·미디어 서비스를 연결한다. | 2026-10-18 후속 사용자 요구로 명확해짐. 독립 host는 agent 실행 위치이며 모든 추론·서비스의 offline 실행을 뜻하지 않음. |
| D-007 | open | Jimmy's Agent Skills 기본 설치는 목표이며 정확한 목록은 출처·재배포 조건·호환성 정리 후 확정한다. | 연구자의 작은 기본 팩 권고는 구성 확정이 아님. |
| D-008 | engineering | 첫 reference는 Prime Agent v0.10.0 Linux ARM64 artifact의 **binary 설치 단계**다. Python 3.11+ 표준 라이브러리로 구현한다. | 모바일 guest에서 쓰일 Linux userland 조건을 다루며 Python·API 인증·전체 agent task 성공과 분리. |
| D-009 | engineering | 일반 진단은 변경 없이 실행한다. 설치 실행은 명시한 상태 디렉터리 안에서 수행하며 기본적으로 원본 배포 파일을 변경하지 않는다. | official installer의 전역 daemon 종료·기존 설치 교체·npm 제거를 호출하지 않음. |
| D-010 | engineering | artifact 미제공 시 `WAITING_USER`로 저장하고 파일 제공 후 이어간다. `--download`를 선택하면 고정 URL에서 자동 취득할 수 있다. | 사용자 대기를 실패나 재시도 소진으로 처리하지 않음. MFA 대기 상태도 같은 상태 저장 계약으로 다룸. |
| D-011 | engineering | `SUCCEEDED`는 recipe가 선언한 범위와 모든 필수 check를 만족한 경우에만 사용한다. | binary 설치 성공을 인증·kernel·첫 작품 완성으로 확대하지 않음. |
| D-013 | confirmed | Simple Mode 조사·콘텐츠 준비 후 Next.js + Zustand 웹사이트를 구현하고 Vercel에 배포한다. ui-ux-pro-max와 아름다운 HTML template을 디자인에 활용한다. | 2026-10-18 후속 요청. Codex를 기본 진입점으로 두되 D-001의 전체 목표를 삭제하지 않음. |
| D-014 | engineering | Playwright CLI를 기본 agent 브라우저 인터페이스, Playwright library/test를 반복 크롤링·검사 도구, Tencent BrowserSkill을 별도 로그인 브라우저 연결로 둔다. agent-browser는 비교 가능한 대안이다. | BrowserSkill과 Playwright의 직접 backend/세션 공유를 확인하지 않았으므로 약속하지 않음. |
| D-015 | confirmed | HY4 Preview, DeepSeek V4.1 Flash, Seedance 2.5와 Jev를 포함한다. | 정확한 model ID·API·제약은 날짜가 있는 공통 카탈로그에 보관. Jev는 판정 역할이며 기본 coding LLM이 아님. |
| D-016 | engineering | 비용효율 영상은 Veo 3.1 Lite, 이미지는 Qwen Image 2.1 Pro/Turbo를 기본 후보로 둔다. | 공개 API metadata와 동일 출력 조건 비용을 근거로 한 선택. 실제 유료 생성 품질 비교 완료 주장은 하지 않음. |
| D-017 | confirmed | 방문 OS에 따라 개별 가입·다운로드·설치·빌드 버튼의 지원 상태를 다르게 표시한다. | 브라우저 OS 추정은 설치·인증 검증이 아님. unknown 및 미검증 로컬 실행은 비활성화하고 수동 OS 수정 제공. |
| D-018 | engineering | 가이드에 실제 공개 화면과 출처를 제공하고, 체크리스트는 사용자 확인으로 명시한다. | 비공개 계정·결제·key 화면이나 연결 완료 증거를 꾸며내지 않음. API key를 웹사이트에 입력·저장하지 않음. |

첫 reference의 실행 계약은 유지하며, Simple Mode 웹사이트와 별도 범위로 검증한다. 상세 웹 계약은 [simple-mode-design.md](/home/jimmy/.paseo/worktrees/13nkmqul/simple-mode-web/docs/simple-mode-design.md)에 있다.
