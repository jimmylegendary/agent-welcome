# 조사 검증 기록

> GitHub 배포본 안내: 아래 검사 결과와 SHA-256은 원래 로컬 조사 시점의 기록입니다. 이 사본은 링크와 경로를 저장소용으로 정리했으므로 배포본 파일의 hash와 다를 수 있습니다. 현재 상태와 자료 위치는 [README.md](https://github.com/jimmylegendary/agent-welcome/blob/main/README.md)를 참고하세요.

기준일: 2026-10-17. 검증 대상은 조사 문서이며, 제품의 설치·동작 성공을 입증하는 기록이 아니다.

이 파일의 수치와 SHA-256은 **첫 6개 조사 문서를 전달한 시점의 기록**이다. 이후 원본 모바일 agent 경로와 KG 설계가 추가되고 주 기획안이 갱신되었다. 후속 산출물과 최신 검증 기록은 [GRAPH_REPORT.md](https://github.com/jimmylegendary/agent-welcome/blob/main/kg/GRAPH_REPORT.md)에서 확인한다.

## 수행한 작업

- `platform_feasibility`, `media_game_ecosystem`, `workflow_skill_ecosystem`의 독립 조사와 `research_review`의 별도 검토를 사용했다. worker 모델은 설정 파일의 `gpt-6-luna`, effort `max`를 확인하고 명시했다. 재위임은 하지 않았다.
- master가 기존 skill 인벤토리와 일반 skill 디렉터리를 조사하고, 주 기획안·로컬 skill 준비 문서를 작성했다.
- master가 공식 Apple·Android 제약, Claude Desktop Code 탭과 Windows 설치, Codex 최신 changelog, n8n 최신 FAQ, Unity 공식 skills, Canva MCP 역할을 직접 확인했다. 분야별 전체 링크에 대해 HTTP 상태 검사나 실제 설치 시험을 수행한 것은 아니다.
- Jev 1.13의 유한 후보 선택은 초기 모바일 검증, 호환되는 기본 팩, 첫 결과물 기준을 권했다. 이 응답은 참고 의견이며 실제 호환성·사용자 승인·시험 통과의 근거로 사용하지 않았다.

## 검토에서 수정한 사항

| 항목 | 반영 결과 |
|---|---|
| Claude GUI | Claude Desktop의 Chat·Cowork·Code를 구분하고 Code 탭의 로컬 파일·명령 실행 경로 추가 |
| Windows CLI | Claude Code의 native Windows에서 Git for Windows가 선택 사항이며 PowerShell 도구로 실행 가능함을 반영 |
| WSL | 같은 Windows 기기의 로컬 runtime으로 판정; Cloud·다른 기기의 SSH와 구분 |
| n8n | 대행사가 자기 instance에서 고객용 workflow를 운영하는 경우, 고객 소유 서버에 설치하는 경우, 외부 고객이 서비스에서 직접 workflow를 구성하는 경우를 구분 |
| 로컬 실행 표시 | 모델·서비스로의 데이터 전송과 보존 안내를 실행 위치와 별도 수용 조건으로 추가 |
| Canva | publisher의 OAuth 앱 준비와 최종 사용자의 계정 연결을 구분 |
| 모바일 대체 앱 | 기존 target agent를 대체하는 것은 미승인 선택지로 유지. GDevelop 자체 AI를 target agent의 로컬 host 근거로 사용하지 않음 |
| Prime–Paseo | ACP 인터페이스가 존재한다는 소스 근거와 실제 handshake 미실시를 분리 |

관련 직접 확인 자료: [Claude Desktop](https://code.claude.com/docs/en/desktop), [Claude Windows](https://code.claude.com/docs/en/getting-started), [Codex changelog](https://learn.chatgpt.com/docs/changelog), [n8n FAQ](https://support.n8n.io/article/can-i-use-your-license-for-my-use-case), [Canva MCP](https://www.canva.dev/docs/apps/mcp/).

## 실행 명령과 실제 출력

`git rev-parse --is-inside-work-tree`를 `<original-workspace>`에서 실행했다.

```text
exit_code=128
fatal: not a git repository (or any of the parent directories): .git
```

현재 작업 폴더는 Git 저장소가 아니며, 저장소를 초기화하거나 commit·push하지 않았다. **이번 작업의 commit SHA는 없다.** upstream release·source 링크는 각 조사 문서에 기록했다.

기존 인벤토리 조회는 `rg --files -g '*.md' -g '*.json' -g '*.csv'`의 제한된 경로 검색과 Python 처리를 사용했다. 일반 skill 디렉터리 조사와 같은 이름의 `SKILL.md` SHA-256 비교 결과는 [local-skills-audit.md](https://github.com/jimmylegendary/agent-welcome/blob/main/local-skills-audit.md)에 기록했다.

문서 검사는 context-mode의 `ctx_execute(language="python")`에서 수행한다. 검사 항목은 지정한 Markdown 6개 존재, 비어 있지 않은 내용, 닫힌 code fence, 한국어 본문, 로컬 링크의 절대 경로·파일 이름 라벨·실제 대상 존재, 카탈로그 행 수다. 외부 링크는 HTTPS 여부와 개수만 검사하며 접근 성공으로 해석하지 않는다.

## 기기 실행 검증 상태

| 검증 | 실행 수 | 판정 |
|---|---:|---|
| 실제 agent 설치·로그인 | 0 | 미실시 |
| iOS·Android 원본 agent 실행 | 0 | 미실시 |
| Prime–Paseo ACP handshake | 0 | 미실시 |
| 분야별 API·MCP·CLI 작업 | 0 | 미실시 |
| 비개발자 사용성 시험 | 0 | 미실시 |
| GitHub 공개·website 배포 | 0 | 미실시 |

조사 문서 검증 결과는 아래에 별도로 기록한다. 문서 검사 통과를 네 OS 지원 완료로 바꾸지 않는다.

## 문서 검사 실제 결과

위의 Python 검사에서 다음 결과를 얻었다. 후보 수는 두 카탈로그의 항목 수이며, 서로 다른 제품 수나 설치 성공 건수가 아니다.

```text
documents=6
checks_passed=9
checks_failed=0
local_links=7
external_link_occurrences=212
unique_external_urls=146
workflow_candidates=28
media_game_candidates=22
total_catalog_rows=50
relative_links=[]
missing_local_targets=[]
wrong_local_labels=[]
```

핵심 문서 5개의 SHA-256은 다음과 같다. Git commit SHA가 아니라 파일 내용 지문이다. 이 검증 기록 자체는 자기 참조를 피하려고 지문 대상에서 제외했다.

```text
START-HERE.md 0ff9d64bf8c7ffb59d81ba683a9dc477c50dc14f6f8243741bf1020468fdc820
local-skills-audit.md 4892c73ccca077d2f6b6eb6e845b55e07e9a14914b4fec13b9a5ed5e51b5fb3c
media-game-research.md d41c270a19c4ba1e0e7af9591ce2b42188fb4abb3f6be1bf2019b52b68ea5567
platform-research.md 4495003a92dc5cd5d4a7fa4622fdd296e7bce48aca375e4014c7cd4f15ab0c4c
workflow-skill-research.md 7864658bd3164699b0d39d639611400bbe340383bdbe4df22526a9cec9e3a9a6
```
