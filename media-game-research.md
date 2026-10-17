# 미디어 생성·편집과 게임 제작 에이전트 도구 조사

검토 기준일은 2026-10-17이다. 이 문서는 영상·이미지·게임 도구의 공식 문서와 프로젝트 저장소를 조사해, 에이전트에 실제로 연결되는 방식과 일반 앱 사용을 구별한다. 여기 있는 프로그램 설치, API 호출, 렌더링, MCP 연결은 실행하지 않았다. **조사 완료는 설치·실행 테스트 완료를 뜻하지 않는다.**

대상 에이전트는 Claude Code, Codex, Prime Agent다. `SKILL.md`는 에이전트가 읽는 작업 지침이지 도구 연결 자체가 아니다. MCP는 선택한 에이전트 앱이 해당 MCP 방식과 권한 설정을 지원해야 하고, CLI는 에이전트가 실행되는 바로 그 기기에서 명령을 실행해야 한다. API는 생성 작업이 서비스 제공자 쪽에서 처리되며 계정·키·요금이 필요할 수 있다. 수동 앱은 실제 에이전트 통합으로 표시하지 않았다.

기기 독립성은 에이전트 호스트와 생성 처리 위치를 나누어 판단해야 한다. 예를 들어 Comfy Cloud나 Luma API는 원격 GPU를 쓰더라도 에이전트 CLI가 사용자의 현재 기기에서 실행되는 경로다. 반대로 로컬 ComfyUI나 Blender MCP는 같은 기기에 앱과 로컬 서버가 있어야 한다. 이 조사는 Claude Code·Codex·Prime Agent가 iOS나 Android에서 로컬 호스트로 실행되는지 확인하지 않으므로, 모바일 MCP·CLI 후보는 해당 플랫폼의 에이전트 실행 지원이 별도로 확인된 뒤에만 노출해야 한다.

## GitHub 탐색 목록

아래 저장소들은 후보를 찾는 인덱스다. 목록에 있다는 사실은 프로젝트의 신뢰성·보안·호환성 보증이 아니며, 목록에서 찾은 도구를 자동 설치하지 않는다. 실제 후보는 뒤에서 각 프로젝트 저장소나 공식 제품 문서로 다시 확인했다.

- 영상: [awesome-ai-video](https://github.com/thoxakihiko/awesome-ai-video)
- 이미지 API·도구: [awesome-image-generation](https://github.com/backblaze-labs/awesome-image-generation)
- 게임 에이전트·도구: [awesome-ai-game-dev-tools](https://github.com/SubmitGame/awesome-ai-game-dev-tools)
- 게임용 `SKILL.md` 모음: [awesome-gamedev-agent-skills](https://github.com/gamedev-skills/awesome-gamedev-agent-skills)

## 영상 생성·편집

1. **[Remotion Agent Skills](https://github.com/remotion-dev/skills) — 공식 Skill 저장소.** 영상 프로젝트에서 Remotion을 쓰는 방법을 에이전트에게 가르치는 `SKILL.md` 묶음이다. 저장소는 Claude Code와 Codex를 명시하며, `npx skills add remotion-dev/skills` 설치 방법을 제공한다. 스킬만으로 렌더러가 생기지는 않는다. 같은 컴퓨터의 Node.js 프로젝트와 Remotion이 필요하고, API 계정은 필요하지 않다. 초보자에게는 에이전트가 코드를 써 주는 장점이 있지만 터미널과 프로젝트 폴더를 다뤄야 한다.

2. **[Remotion](https://www.remotion.dev/docs/) — 영상 구성·렌더링 라이브러리와 CLI.** React로 장면과 타이밍을 만들고 로컬에서 MP4 등을 렌더링한다. `SKILL.md`나 API가 아닌 CLI와 프로젝트 파일을 에이전트가 조작하는 경로다. 사용자 컴퓨터에서 Node.js와 브라우저 기반 렌더링이 필요하며, 모델로 장면 영상을 생성하는 서비스는 아니다. 간단한 타이틀·제품 소개 영상에는 적합하고, 처음 설치하는 비개발자에게는 중간 난이도다. 상업 사용·재배포 조건은 이 조사에서 확인하지 않았다.

3. **[FFmpeg](https://ffmpeg.org/) — 영상·오디오 처리 CLI.** 자르기, 합치기, 크기·코덱 변환 같은 결정적인 후처리를 에이전트가 명령어로 실행한다. 이미지나 영상을 생성하는 AI 도구가 아니며, 별도 Skill/MCP가 필요한 것은 아니다. 실행 파일은 사용자가 쓰는 같은 컴퓨터에 설치한다. 계정이나 API 키가 필요 없다. 터미널 명령을 검토해야 하므로 초보자에게는 에이전트가 옵션을 정리해 주는 경우에만 적합하다.

4. **[Luma Dream Machine API](https://docs.lumalabs.ai/docs/video-generation) — 호스팅 영상 생성·수정 API.** 텍스트·이미지 기반 영상 생성과 [영상 수정 요청](https://docs.lumalabs.ai/reference/modifyvideo)을 지원한다. 에이전트 앱에서 REST API를 부르며, 생성은 Luma 서비스에서 처리되므로 로컬 GPU나 상시 켜진 데스크톱은 필요하지 않다. 사용자가 Luma API 플랫폼에서 계정을 만들고 키를 받아 Bearer 인증으로 연결해야 하며, 사용량은 크레딧/과금 조건을 확인해야 한다. 비동기 상태 확인, 파일 업로드·다운로드와 키 보관이 필요해 초보자 난이도는 낮지 않다.

5. **[CapCut](https://www.capcut.com/tools/video-editor-download) — 모바일·데스크톱 수동 편집 앱.** 짧은 영상 자르기, 자막, 효과, 템플릿을 사용자가 앱에서 직접 편집하는 경로다. 공식 에이전트용 MCP나 CLI 연결은 확인하지 못했으므로 Claude/Codex/Prime 통합 도구로 취급하지 않는다. iOS·Android 앱은 앱 스토어에서, 데스크톱 앱은 CapCut 공식 배포 경로에서 설치한다. 편집 초보의 마지막 손질에 적합하며, 계정·유료 기능 조건은 기능과 지역에 따라 확인이 필요하다.

## 이미지 생성·편집 및 교차 미디어

6. **[ComfyUI](https://github.com/Comfy-Org/ComfyUI) — 로컬 노드형 이미지·미디어 엔진.** 로컬 모델과 워크플로를 돌리고, 로컬 API로 앱이나 다른 도구에서 작업을 보낼 수 있다. Windows·macOS·Linux용 설치 경로가 있지만, 모바일 앱으로 확인되지는 않았다. 로컬 생성은 모델 파일과 충분한 저장 공간·연산 성능이 필요하고, 일반적으로 API 계정은 필요하지 않다. 초보자에게는 기본 워크플로와 사전 설치 모델을 제공해야 편하다. GitHub SPDX 메타데이터는 저장소 코드에 `GPL-3.0`을 표시한다. 모델·노드·산출물의 이용 조건은 별도로 확인해야 한다.

7. **[Comfy-Org/comfy-mcp](https://github.com/Comfy-Org/comfy-mcp) — ComfyUI용 공식 조직 MCP 서버.** README는 `generate_image`, 워크플로 실행, 설치된 노드·모델 조회를 설명하고, 로컬 ComfyUI를 MCP 에이전트가 직접 조작하도록 한다. 같은 기기에 ComfyUI와 MCP 서버를 설치하고 에이전트 설정에 로컬 `stdio` 서버를 연결해야 한다. 기본 로컬 모델 경로에는 API 키가 필요하지 않지만 모델 설치와 GPU가 필요할 수 있다. MCP 클라이언트와 프로젝트 설정을 별도로 확인해야 해 설치 난이도는 중간 이상이며, Prime Agent 호환성은 이 조사에서 확인하지 않았다. 저장소 라이선스 메타데이터는 `NOASSERTION`이어서 재배포 권리를 추정하지 않는다.

8. **[Comfy-Org/comfy-cli](https://github.com/Comfy-Org/comfy-cli) — ComfyUI 설치·실행 및 생성 CLI와 번들 Skill.** `comfy setup`은 로컬 또는 Comfy Cloud 사용을 안내하고, `comfy generate`는 지원되는 이미지·영상 제공자 모델을 워크플로 JSON 없이 호출하는 경로를 제공한다. CLI는 에이전트가 실행되는 기기에 설치한다. 로컬 경로는 모델·GPU가 필요하지만, Comfy Cloud 경로는 로컬 GPU 없이 브라우저 OAuth 로그인으로 작업을 제출하고 결과를 해당 기기에 내려받는다. Cloud 계정과 사용료를 확인해야 한다. 번들 `SKILL.md` 문서는 Claude·Cursor를 대상으로 명시하므로 Codex·Prime의 스킬 자동 설치를 보장하지 않는다. 다른 에이전트는 CLI를 실행할 수 있는지와 사용자 권한을 따로 확인해야 한다. 저장소 SPDX 메타데이터는 `GPL-3.0`이다.

9. **[Krita AI Diffusion](https://github.com/Acly/krita-ai-diffusion) — Krita용 커뮤니티 생성형 편집 플러그인.** 캔버스에서 영역·마스크를 지정해 생성, 인페인팅, 아웃페인팅을 하고 로컬 ComfyUI를 관리형 설치로 설정하거나 기존 서버에 연결한다. 플러그인 문서는 Windows·Linux·macOS를 안내한다. 로컬 서버와 모델을 같은 컴퓨터에 두는 경로를 우선한다. 에이전트가 Krita 화면을 직접 조작하는 MCP/CLI/Skill 연결은 확인되지 않아, 에이전트가 만든 프롬프트와 사용자의 GUI 편집을 잇는 도구로 본다. 플러그인 저장소는 `GPL-3.0`이며 Krita 공식 지원 채널이 아닌 제3자 플러그인이다.

10. **[InvokeAI](https://invoke.ai/) — 로컬 이미지 제작·레이어 캔버스 앱.** [공식 Launcher](https://invoke-ai.github.io/InvokeAI-7/start-here/installation/)는 Windows·macOS·Linux 설치와 업데이트를 관리하며, 이미지를 로컬에서 만들고 캔버스로 편집한다. 로컬 모델이면 API 키가 필요 없지만 모델 다운로드와 성능에 맞는 하드웨어가 필요하다. 일부 모델 다운로드나 외부 제공 모델은 별도 토큰·서비스를 요구할 수 있다. 외부 에이전트용 공식 Skill/MCP를 확인하지 못했으므로 수동 GUI 후보로 분류한다. 저장소 SPDX 메타데이터는 `Apache-2.0`이다.

11. **[OpenAI Images API](https://developers.openai.com/api/docs/guides/images-vision) — 호스팅 이미지 생성·편집.** Images API와 Responses API로 이미지 생성·편집 요청을 보내며, [편집 API](https://developers.openai.com/api/reference/resources/images/methods/edit)는 원본 이미지와 지시문을 받는다. 이미지 처리는 OpenAI 서비스에서 수행되어 사용자의 데스크톱 GPU나 별도 서버를 요구하지 않는다. 사용자는 OpenAI Platform 계정·API 키·API 결제를 준비해야 한다. [ChatGPT와 API 결제는 별도](https://help.openai.com/en/articles/9039756)다. 키는 채팅이나 저장소가 아닌 선택한 에이전트의 비밀 저장소/환경 설정에 넣고, 이미지는 외부 서비스에 전송된다는 점을 안내한다. API를 직접 호출할 수 있는 에이전트 설정이 필요하며 단순 앱 연결은 아니다.

12. **[Draw Things](https://drawthings.ai/downloads/) — Apple 기기 로컬 생성 앱.** 공식 안내는 iPhone·iPad·Mac에서 이미지 모델을 내려받아 기기에서 실행하는 흐름을 제공한다. Apple 앱에서 모델을 한 번 내려받은 뒤 텍스트 생성과 이미지 편집을 사용할 수 있고, 로컬 사용에는 API 키가 필요하지 않다. Android 앱은 이 조사에서 확인되지 않았다. 공식 업데이트 항목에 API 서버용 Bridge Mode가 언급되지만, Claude Code·Codex·Prime Agent와 연결하는 설치 문서는 확인하지 못했으므로 기본 소개는 수동 앱으로 제한한다. 초보자가 Apple 기기에서 로컬 이미지 생성에 먼저 성공하기 좋은 경로다.

13. **[Canva MCP](https://www.canva.dev/docs/apps/mcp/) — 공식 원격 MCP 디자인 연결과 Canva 앱.** MCP는 디자인 생성·수정, 자산 검색, 내보내기 등을 에이전트에 제공한다. [접근 문서](https://www.canva.dev/docs/apps/mcp/access/)는 각 사용자가 Canva OAuth로 인증한다고 설명한다. 새 에이전트 앱 연결에는 Developer Portal에서 앱을 만들고 MCP를 켜 OAuth client ID/secret과 redirect URL을 설정하거나, 일부 client 방식에서는 허용 절차가 필요할 수 있다. 이 개발자 등록은 패키지 운영자(publisher)가 준비할 일이고, 일반 사용자는 자신의 Canva 계정 선택과 권한 동의를 맡는 흐름으로 설계한다. 공개 native 앱에 confidential client secret을 포함하지 않도록 공급자가 지원하는 인증 구조를 먼저 검증해야 한다. 디자인 자체는 Canva 웹·모바일 앱에서 사용할 수 있지만, MCP는 Canva 원격 서비스에 연결되므로 로컬 생성이 아니다. 수동 앱은 초보자에게 쉽고, 새 MCP 통합은 운영자 측 개발자 설정이 필요하다. 일부 기능은 유료 플랜에 좌우된다.

## 게임 제작 및 에이전트 보조

14. **[GDevelop](https://gdevelop.io/en-gb/game-makers) — 노코드 게임 제작 도구와 내장 AI 보조.** 이벤트와 오브젝트를 시각적으로 편집해 게임을 만들며, 공식 문서상 데스크톱·브라우저와 iOS·Android 앱에서 제작할 수 있다. [GDevelop AI](https://wiki.gdevelop.io/gdevelop5/interface/ai/chat/)의 “Build for me” 기능은 현재 프로젝트의 게임 기능을 만들 수 있지만, 이는 Claude/Codex/Prime용 MCP나 Skill이 아니라 GDevelop 안에 포함된 자체 도우미다. AI 사용은 계정과 크레딧/요금제 조건을 확인해야 한다. 초보자용 앱 경로로 좋지만 외부 에이전트 호스트의 존재를 입증하지 않는다.

15. **[Godot Engine](https://godotengine.org/download/) — 로컬 게임 엔진.** Windows·macOS·Linux에 설치하고 프로젝트 파일과 GDScript를 에이전트가 작성하게 한 뒤, 같은 기기의 Godot 편집기나 CLI로 미리보기·실행한다. 엔진 자체에는 계정이나 API 키가 필요하지 않다. 공식 Godot 저장소는 MIT 메타데이터를 표시한다. 설치 뒤 프로젝트를 실행하는 것은 비교적 쉽지만, 게임 동작을 수정하려면 코드와 씬 구조를 알아야 하므로 초보자 난이도는 중간이다. 이 조사에서 Godot 공식 Skill/MCP를 확인하지 못했다.

16. **[awesome-gamedev-agent-skills](https://github.com/gamedev-skills/awesome-gamedev-agent-skills) — 커뮤니티 게임용 Skill 모음.** 저장소는 여러 엔진별 `SKILL.md`와 작업 지침을 제공하고, 설치 문서는 Codex 등을 위한 `npx skills add` 경로를 설명한다. Skill은 엔진이나 앱을 설치하지 않고, 에이전트에게 프로젝트별 작업법을 알려준다. 게임 프로젝트와 엔진은 여전히 같은 기기에 설치해야 한다. 저장소 SPDX 메타데이터는 `Apache-2.0`이다. 여러 Skill을 한꺼번에 가져오기보다 필요한 엔진만 고르고 지침·스크립트를 먼저 검토해야 한다.

17. **[Unity-Technologies/skills](https://github.com/Unity-Technologies/skills) — Unity가 제공하는 공식 에이전트 Skill 저장소.** Unity 워크플로를 위한 지침과 도구를 제공하며 `npx skills add Unity-Technologies/skills` 설치 방법이 있다. 저장소 README는 Unity가 유지·자동 게시한다고 밝히고, Unity CLI와 함께 사용하도록 안내한다. 이 저장소는 Skill이며, Unity 편집기 조작은 다음 항목의 CLI/MCP가 맡는다. 스킬 설치만으로 Unity Editor가 생기지 않는다. 저장소 라이선스 메타데이터는 `NOASSERTION`이어서 재배포 상태는 표기하지 않는다.

18. **[Unity CLI와 Editor MCP](https://github.com/Unity-Technologies/skills/tree/main/skills/unity-cli) — Unity가 관리하는 로컬 도구 연결.** Unity CLI는 편집기 설치·프로젝트·빌드를 다루고, `unity mcp`는 실행 중인 로컬 Unity Editor의 명령을 MCP 도구로 노출한다. Unity Hub·Editor·CLI 설치와 계정/라이선스 활성화가 필요하며, 에이전트 클라이언트에 MCP를 연결해야 한다. 작업 대상과 Unity Editor는 해당 기기에 있어야 한다. 에이전트가 씬을 직접 다루는 강한 연결이지만 다운로드 규모와 설정이 커서 첫 게임 제작용으로는 난이도가 높다. 일반 게임 서비스에 대한 API 키는 필요하지 않다.

19. **[RPG Maker MZ](https://www.rpgmakerweb.com/products/rpg-maker-mz) — GUI 중심 RPG 제작 앱.** Windows·Mac 제품을 설치하고 맵·이벤트·대사를 편집한다. 기본 앱은 외부 에이전트 연결 없이도 쓸 수 있고, 프로젝트 파일 작업을 에이전트에 보조시키려면 아래 Skill/MCP가 별도로 필요하다. 제품을 구입하고 공식 상점 또는 Steam에서 활성화해야 한다. 공식 [FAQ/EULA](https://www.rpgmakerweb.com/eula)는 구매 라이선스로 상업 게임 제작을 허용하지만, 포함 리소스 사용은 RPG Maker로 만든 게임에 한정한다고 안내한다. 배포 전에 현재 EULA와 개별 리소스 조건을 읽어야 한다. RPG를 만들고 싶은 비개발자에게 GUI는 친숙하지만, 이벤트 시스템과 데이터 파일에 익숙해지는 과정이 필요하다.

20. **[RPG Maker Agent Skills](https://github.com/nightquill/rpgmaker-agent-skills) — 커뮤니티 MV/MZ `SKILL.md` 팩.** 데이터베이스·이벤트·대사 파일을 에이전트가 읽고 쓰도록 작업 규칙을 제공한다. Claude Code용 기본 설치 안내가 있고, Codex에는 Skill 폴더를 별도로 복사하는 단계가 문서화되어 있다. RPG Maker MZ/MV 프로젝트와 앱은 같은 컴퓨터에 필요하며 계정/API 키는 없다. 저장소 SPDX 메타데이터는 `MIT`다. 저장소 설치 지침에는 원격 셸 스크립트를 실행하는 예시가 있으므로 그대로 자동 실행하지 말고 파일·권한을 확인한다. 공식 RPG Maker 발행 Skill은 확인하지 못했다.

21. **[RPG Maker MZ MCP](https://github.com/Redseb/rpgmaker-mz-mcp) — 커뮤니티 MCP 프로젝트 연결.** 저장소는 MZ 프로젝트의 데이터와 이벤트를 읽고 쓰는 도구를 설명하며 128개 도구를 광고한다. 프로젝트 저장소는 `MIT` 메타데이터를 표시한다. MCP 서버를 로컬에 설치하고 해당 프로젝트 경로에 권한을 준 뒤 MCP 클라이언트 설정을 해야 한다. 저장소 빠른 시작은 Claude 경로를 중심으로 하므로 Codex·Prime Agent 연결은 각 MCP 클라이언트 지원을 확인하고 직접 검증해야 한다. 프로젝트 데이터를 수정하는 권한을 주므로 초보자에게는 백업 프로젝트에서 시험하는 것이 적합하다. 설치·안전성은 검증하지 않았다.

22. **[Blender Labs MCP Server](https://www.blender.org/lab/mcp-server/) — Blender 공식 사이트의 실험적 MCP 통합.** Blender 세션을 Python API로 제어해 게임 에셋, 재질, 씬, 렌더링을 만들 수 있다. Blender 앱, Labs 애드온, MCP 서버와 MCP 에이전트를 같은 기기에 설치해야 하며 서비스 API 키는 필요하지 않다. Blender 사이트는 이 서버가 에이전트 생성 코드를 보호장치 없이 실행하며 파일 삭제·외부 전송을 막지 않는다고 경고한다. 초보자용 기본 옵션으로 노출하지 말고, 격리된 테스트 프로젝트에서 검토하는 고급 선택지로 표시한다. 저장소 수준 라이선스는 이 조사에서 확인하지 않았다.

## 첫 성공까지의 권장 흐름

1. **Claude Code 또는 Codex가 지원되는 데스크톱에서 짧은 모션 영상을 만든다.** 사람이 새 프로젝트 폴더를 정하고 Node.js를 설치한다. 에이전트에게 Remotion 프로젝트와 Skill을 구성하게 한 뒤, 제목·이미지·마지막 카드의 3장면만 만들어 Remotion Studio에서 확인하고 MP4로 로컬 렌더링한다. API 키 없이 결과를 만들 수 있다. 원본 영상 생성이 아니라 텍스트·도형·이미지로 구성한 모션그래픽이라는 점을 안내한다.

2. **같은 데스크톱에서 ComfyUI 이미지를 에이전트에게 요청한다.** 로컬 ComfyUI와 필요한 모델이 정상 동작하는 기기에서 공식 `comfy-mcp`를 설정하고, MCP 지원이 확인된 에이전트에 연결한다. 준비된 템플릿으로 아이콘 하나를 생성하고 저장 위치를 확인한 뒤, 사용자가 Krita에서 손질한다. 로컬 생성이라 API 키는 없지만 모델 다운로드와 하드웨어가 필요하다. 모바일 앱에서 이 로컬 서버에 접속한다는 가정은 하지 않는다.

3. **Codex와 Godot용 커뮤니티 Skill로 작은 2D 게임을 만든다.** 컴퓨터에 Godot을 설치하고 새 빈 프로젝트를 연다. 필요한 Godot용 Skill만 프로젝트에 추가한 뒤 “캐릭터가 움직이고 동전을 하나 먹으면 점수가 올라가는 장면”처럼 한 기능을 요청한다. Codex가 프로젝트 파일을 바꾼 뒤 사용자가 Godot에서 실행해 동작을 확인한다. 외부 API 키가 필요 없고, 엔진과 프로젝트는 Codex가 실행되는 같은 기기에 둔다.

4. **모바일 게임 제작은 GDevelop 자체 앱을 보조 경로로 쓴다.** iOS나 Android 기기에 GDevelop 앱을 설치하고 계정으로 로그인한다. 새 프로젝트에서 내장 Ask AI/Build for me에 “버튼을 누르면 점수가 1씩 올라가는 화면”을 요청하고 즉시 미리보기한다. 이 흐름은 Claude/Codex/Prime 연결이 아니라 GDevelop 자체 AI 기능을 쓰는 모바일 앱 경로라고 분명히 표시한다. AI 크레딧과 앱에서 가능한 편집·내보내기 범위는 현재 요금제에서 확인한다.

5. **원격 API 생성은 에이전트가 현재 기기에서 호출할 수 있을 때만 추가한다.** 예를 들어 OpenAI Images API로 참조 이미지를 편집하거나 Luma API로 짧은 영상을 만든 뒤 파일을 현재 기기로 내려받아 Canva·CapCut에서 사람이 최종 손질한다. 계정·키·비용은 해당 제공자에서 따로 설정한다. iOS/Android의 Claude·Codex·Prime Agent가 이 API를 로컬에서 호출하고 비밀 키를 안전하게 보관하는지는 이 조사의 도구 검증 범위에 없으므로, 해당 모바일 에이전트 경로가 별도로 검증된 뒤 소개한다.

## 유지보수·라이선스 근거

GitHub 공개 API의 `pushed_at` 필드를 2026-10-17 UTC에 조회했다. 아래 날짜는 저장소에 마지막으로 push된 시점을 나타내는 메타데이터이지 최신 릴리스, 품질, 보안, 기능 동작을 입증하지 않는다.

- `2026-10-16`: [Remotion Skills](https://github.com/remotion-dev/skills), [Remotion](https://github.com/remotion-dev/remotion), [FFmpeg](https://github.com/FFmpeg/FFmpeg), [ComfyUI](https://github.com/Comfy-Org/ComfyUI), [Comfy CLI](https://github.com/Comfy-Org/comfy-cli), [Comfy MCP](https://github.com/Comfy-Org/comfy-mcp), [InvokeAI](https://github.com/invoke-ai/InvokeAI), [Godot](https://github.com/godotengine/godot), [GDevelop](https://github.com/4ian/GDevelop), [Unity Skills](https://github.com/Unity-Technologies/skills), [awesome game-dev tools](https://github.com/SubmitGame/awesome-ai-game-dev-tools).
- `2026-10-09`: [game-dev skills](https://github.com/gamedev-skills/awesome-gamedev-agent-skills). `2026-10-07`: [awesome image-generation](https://github.com/backblaze-labs/awesome-image-generation). `2026-10-03`: [Krita AI Diffusion](https://github.com/Acly/krita-ai-diffusion). `2026-09-27`: [awesome AI video](https://github.com/thoxakihiko/awesome-ai-video). `2026-09-25`: [RPG Maker MZ MCP](https://github.com/Redseb/rpgmaker-mz-mcp). `2026-04-22`: [RPG Maker Agent Skills](https://github.com/nightquill/rpgmaker-agent-skills).

공개 저장소 라이선스 메타데이터를 확인한 항목만 표기했다: ComfyUI·Comfy CLI·Krita 플러그인 `GPL-3.0`, InvokeAI·게임용 Skill 모음 `Apache-2.0`, Godot·RPG Maker Agent Skills·RPG Maker MZ MCP `MIT`. 이 표시는 각 저장소 코드에 대한 메타데이터일 뿐, 내려받은 모델·노드·게임 에셋·폰트·영상·생성 결과의 재배포 권리를 보장하지 않는다. 그 조건은 모델·에셋·서비스별 라이선스에서 따로 확인해야 한다. 나머지 제품·서비스의 라이선스와 산출물 권리는 확인되지 않아 추정하지 않았다.
