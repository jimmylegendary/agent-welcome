# 플랫폼별 로컬 agent 실행 가능성

**조사 기준일: 2026-10-17.** 여기서 “로컬 host”는 프롬프트를 받은 뒤 agent loop, 저장소 접근, 도구 실행을 해당 기기에서 수행하는 프로세스를 뜻한다. 휴대폰에서 다른 컴퓨터에 연결해 그 컴퓨터에서 실행되는 작업을 조종하는 UI는 로컬 host로 세지 않았다.

**가정:** 아래 내용은 root가 제시한 잠정 해석에 따라, 모델 추론은 원격 API를 써도 되며 agent 도구와 저장소 작업만 각 기기에서 수행하는 구조를 기준으로 한다. 사용자가 API 추론을 확정한 것은 아니다. 오프라인 모델 추론은 별도 요구다. 기존 기준 agent는 Claude Code, Codex, Prime Agent이며 이들을 모바일용으로 바꾼다고 가정하지 않았다.

표의 **지원**은 현재 vendor 문서나 배포 artifact로 확인된 제품 지원, **미지원**은 현재 공식 제품 host 대상으로 나오지 않는다는 뜻이다. 이는 기술적으로 port가 불가능하다는 주장이 아니다. **실험적**은 beta 또는 새 native 구현 경로, **미검증**은 문서·소스만으로 실제 동작을 확인할 수 없는 상태다.

## 현재 제품의 host 지원

| 기기 OS | Claude Code CLI | Codex CLI | Prime Agent |
|---|---|---|---|
| macOS | **지원.** macOS 13+, x64/ARM64, 4 GB RAM 이상, 인터넷 필요. [Claude Code 요구사항·설치](https://code.claude.com/docs/en/getting-started) | **지원.** CLI quickstart에 macOS 설치 경로가 있다. 로컬 프로젝트와 컴퓨터에 설치된 도구를 사용한다. [Codex CLI](https://developers.openai.com/codex/cli) | **지원.** 최신 확인 release v0.10.0에 Darwin x64·ARM64 artifact가 있다. README에 macOS 설치 스크립트가 있다. [Prime Agent release](https://github.com/PrimeIntellect-ai/prime-agent/releases/tag/v0.10.0), [repository](https://github.com/PrimeIntellect-ai/prime-agent) |
| Windows | **지원.** Windows 10 1809+부터 native 설치를 제공한다. Git for Windows는 Bash 도구용 선택 사항이며, WSL1/2도 지원된다. 문서상 command sandboxing은 WSL2에서만 지원된다. [설치·Windows 옵션](https://code.claude.com/docs/en/getting-started) | **지원.** Codex CLI 문서에 Windows 설치 옵션이 있고, Codex 앱은 PowerShell과 native Windows sandbox로 실행된다. [Codex CLI](https://developers.openai.com/codex/cli), [Codex changelog](https://learn.chatgpt.com/docs/changelog) | **지원, x64 한정.** PowerShell installer가 최신 Windows x64 build와 checksum을 확인한다. 현재 release 목록에는 Windows ARM64가 없다. [Prime Agent README](https://github.com/PrimeIntellect-ai/prime-agent), [v0.10.0 release API](https://api.github.com/repos/PrimeIntellect-ai/prime-agent/releases/latest) |
| iOS | **공식 host 지원 없음.** Claude의 iOS 앱과 desktop Remote Control은 별도 client다. | **공식 host 지원 없음.** ChatGPT iOS 앱은 연결된 Mac/Windows Codex host를 조종한다. | **공식 host 지원 없음.** 현재 release에 iOS artifact가 없다. |
| Android | **공식 host 지원 없음.** Claude의 Android 앱은 모바일 client다. | **공식 host 지원 없음.** ChatGPT Android 앱은 연결된 Mac/Windows Codex host를 조종한다. | **공식 host 지원 없음.** 현재 release에 Android artifact가 없다. Termux에서의 실행은 미검증이다. |

Prime Agent의 확인된 최신 release는 2026-10-09의 v0.10.0이며 Darwin x64/ARM64, Linux x64/ARM64, Windows x64용 artifact를 제공한다. release 목록에는 iOS 또는 Android target이 없다. 저장소는 Rust/Cargo workspace이고, README가 file·shell·tool 작업을 수행하는 persistent Python REPL을 명시한다. 저장소 license는 MIT다. Mac/Linux shell과 Windows PowerShell용 단일 installer가 있으며, 사용자용 첫 실행에서는 `/login`으로 provider를 선택해야 한다. [v0.10.0 release](https://github.com/PrimeIntellect-ai/prime-agent/releases/tag/v0.10.0), [latest release metadata](https://api.github.com/repos/PrimeIntellect-ai/prime-agent/releases/latest), [README](https://github.com/PrimeIntellect-ai/prime-agent/blob/main/README.md), [Cargo.toml](https://github.com/PrimeIntellect-ai/prime-agent/blob/main/Cargo.toml), [LICENSE](https://github.com/PrimeIntellect-ai/prime-agent/blob/main/LICENSE)

Prime의 소스는 Claude Pro/Max, ChatGPT Plus/Pro(Codex), GitHub Copilot, xAI Grok의 subscription login과 여러 provider의 API key 경로를 정의한다. 소스는 Claude subscription 인증이 Prime Agent를 Claude Code로 식별하며 Anthropic 약관 위반 가능성과 계정 제한 위험이 있다고 경고하고, Anthropic API key를 대안으로 안내한다. [provider login source](https://github.com/PrimeIntellect-ai/prime-agent/blob/main/crates/pa-cli/src/provider_login.rs)

Prime Agent는 `SKILL.md` 형태의 Agent Skills를 파싱하고 Python package 형태의 skill도 persistent Python kernel에 연결한다. Python-backed skills는 일반 문서형 skills와 실행 요구가 다르므로 그대로 이식된다고 보지 않아야 한다. [skill discovery source](https://github.com/PrimeIntellect-ai/prime-agent/blob/main/crates/pa-core/src/skills/discovery.rs), [skill model source](https://github.com/PrimeIntellect-ai/prime-agent/blob/main/crates/pa-core/src/skills/mod.rs)

## GUI가 host인지 remote client인지

| GUI | 실제 local 실행 경로 | 모바일 동작과 판정 |
|---|---|---|
| Claude | Claude Desktop의 Code 탭은 macOS와 Windows에서 local session을 실행한다. Linux desktop은 beta다. 매 session에서 Local, Cloud, SSH, Windows의 WSL 중 environment를 고른다. Cloud와 다른 기기로 연결하는 SSH는 원격 실행이다. WSL은 같은 Windows 기기 안의 별도 Linux runtime이므로 이 요구에서 로컬 host로 인정하되, native Windows와 프로젝트 경로·도구 호환성 시험을 나눈다. Desktop Code는 터미널 CLI와 별도 version의 CLI copy를 사용한다. [Claude Code Desktop](https://code.claude.com/docs/en/desktop) | Claude iOS/Android 앱의 Remote Control은 desktop/CLI에서 시작한 Claude Code 작업을 휴대폰에서 보내고 확인한다. 휴대폰 자체가 agent host가 되지는 않는다. [Claude Download·모바일 연결](https://claude.com/download) |
| Codex | ChatGPT desktop app의 Codex는 macOS와 Windows에서 local work를 지원한다. Codex CLI도 local repository를 직접 다룬다. [Codex CLI](https://developers.openai.com/codex/cli), [Codex changelog](https://learn.chatgpt.com/docs/changelog) | ChatGPT 모바일 앱은 QR pairing으로 연결한 Mac 또는 Windows host에서 Codex 작업을 시작·계속하고 진행을 확인한다. 실행은 연결된 host에서 이뤄진다. [Codex Remote release note](https://learn.chatgpt.com/docs/changelog) |
| Paseo | Paseo Desktop은 macOS, Windows, Linux에서 local daemon을 bundled package로 시작한다. 다만 agent CLI 자체를 대신 설치하지 않는다. 공식 시작 안내는 먼저 최소 한 provider CLI를 설치하고 인증하도록 요구한다. Native providers에는 Claude Code와 Codex가 있다. [Getting started](https://paseo.sh/docs), [supported providers](https://paseo.sh/docs/supported-providers) | Paseo iOS/Android 앱은 컴퓨터나 server의 daemon에 relay 또는 Tailscale로 연결한다. 앱 문서가 직접 이를 client-to-daemon 연결로 설명한다. 따라서 기본 mobile app은 mobile-local execution host가 아니다. [Paseo connectivity](https://paseo.sh/docs/connectivity), [Paseo security architecture](https://paseo.sh/docs/security) |

Prime Agent는 Paseo native provider 목록에 없지만, 두 쪽 source에 맞물릴 수 있는 interface가 있다. Paseo custom provider는 ACP over stdio를 허용하고, Prime Agent CLI는 현재 `acp` mode를 제공하며 해당 protocol mode가 stdin/stdout을 사용한다고 소스에 적혀 있다. 따라서 Paseo 설정에서 `extends: "acp"`와 Prime command를 지정하는 연결 경로는 **소스상 가능성이 높다**. 다만 공식 catalog entry가 아니고 이 조사에서는 설치·handshake 실행을 하지 않았으므로 실제 상호운용은 **미검증**이며, 자동 설치 흐름도 아니다. [Paseo custom providers](https://paseo.sh/docs/custom-providers), [Prime CLI arguments](https://github.com/PrimeIntellect-ai/prime-agent/blob/main/crates/pa-cli/src/args.rs), [Prime ACP runtime](https://github.com/PrimeIntellect-ai/prime-agent/blob/main/crates/pa-daemon/src/acp/mod.rs)

## iOS·Android에서 별도 local host를 만들 때

현존 3개 CLI를 그대로 설치하는 mobile 경로는 확인되지 않았다. 그래도 맞춤형 app 안에 tool loop를 구현하고, 프로젝트 파일과 허용된 도구만 앱에서 실행하며, 모델 요청만 API로 보내는 설계까지 불가능하다고 단정할 근거는 없다. 앱 안에 포함된 실행기와 사용자가 선택한 파일 권한을 쓰는 native host는 검토할 수 있다. 이 경로의 tool·권한·사용성 parity와 app-store 승인 여부는 아직 검증되지 않았으므로 **실험적**으로 분류한다.

**iOS.** App Store Guideline 2.5.2는 앱을 bundle/container 안에 두고, 앱 기능을 바꾸는 코드를 다운로드·설치·실행하는 것을 제한한다(교육 목적 예외는 좁게 규정). Guideline 2.5.4는 background service를 용도에 맞게만 쓰도록 한다. Apple은 짧은 refresh 작업과 시간이 걸리는 processing 작업을 구분하는 background task API를 제공하지만, 상시 실행 daemon 보장은 아니다. 따라서 foreground 실행과 저장·재개를 중심으로 설계하는 편이 문서와 맞는다. 프로젝트 전체 파일 권한은 앱 sandbox와 Files picker 범위 안에서 별도로 검토해야 한다. [App Review Guidelines 2.5.2/2.5.4](https://developer.apple.com/app-store/review/guidelines/), [Apple background tasks](https://developer.apple.com/documentation/uikit/using-background-tasks-to-update-your-app)

기존 iOS terminal app은 제한된 local 실행이 가능한 예다. iSH는 user-mode x86 emulation과 syscall translation을 사용한다. a-Shell은 앱에 포함된 명령과 WebAssembly 명령을 실행하지만, WebAssembly 명령은 socket과 fork를 지원하지 않는다고 프로젝트 문서가 설명한다. 이 사례들은 제한된 in-app runtime이 가능함을 보여 줄 뿐, Claude Code·Codex·Prime Agent의 mobile port나 앱 심사 가능성을 입증하지 않는다. [iSH source](https://github.com/ish-app/ish), [a-Shell source](https://github.com/holzschu/a-shell)

**Android.** Android app은 고유 UID/process를 가진 sandbox 안에서 실행되고 native code도 그 sandbox에 속한다. 맞춤형 native Android app host를 설계할 기반은 있다. 반면 Android 12+에서는 background 앱이 예외 없이 foreground service를 새로 시작할 수 없고, Android 14+는 service type별 권한을 요구한다. 장시간 실행 기능은 user-visible service와 OS 조건을 전제로 설계·검증해야 한다. [Android app sandbox](https://source.android.com/docs/security/features), [foreground service background-start limits](https://developer.android.com/develop/background-work/services/fgs/restrictions-bg-start)

Termux는 Android app 안에서 실행되는 별도 Linux 계열 환경이지만 desktop Linux와 ABI가 다르다. Termux package는 Android NDK로 빌드되고 Android Bionic에 연결되며, 자체 private app prefix를 쓴다. 따라서 Prime의 `linux-arm64` GNU artifact를 Termux 설치 경로에 넣는 것은 지원 사실로 간주할 수 없다. Android target artifact가 현재 Prime release에 없고, Termux 실행 여부도 조사 중 검증하지 않았으므로 상태는 **미검증**이다. Termux는 별도 앱 설치·package 관리·파일 접근·background 상태 확인이 들어가므로 비개발자용 한 번 설치 경로와도 거리가 있다. [Termux installation](https://github.com/termux/termux-app#installation), [Termux execution environment](https://github.com/termux/termux-packages/wiki/Termux-execution-environment)

## 설치·인증·skills에 미치는 영향

Desktop 제품은 기존 공식 installer를 감싸는 welcome flow를 만들 수 있지만, 첫 실행을 끝내려면 각 provider 계정 인증이 남는다. Claude Code는 Pro/Max/Team/Enterprise, Console API 계정 또는 지원 cloud provider를 받는다. Codex는 ChatGPT subscription 인증과 API key 인증을 제공하며, API key 사용은 Platform 계정 usage-based 과금이다. Prime Agent는 `/login`에서 subscription/API key provider를 고른다. [Claude Code quickstart](https://code.claude.com/docs/en/quickstart), [Codex authentication](https://learn.chatgpt.com/docs/auth), [Prime Agent provider login](https://github.com/PrimeIntellect-ai/prime-agent/blob/main/crates/pa-cli/src/provider_login.rs)

Skills는 표준 frontmatter와 `SKILL.md`를 공유할 수 있지만 discovery 위치와 확장 필드는 다르다. Codex는 repo의 `.agents/skills`와 user `.agents/skills`, Claude Code는 `.claude/skills` 계열 위치를 사용한다. Prime Agent는 표준 skill metadata를 읽는 source가 있으나 Python package skill은 Prime 고유 실행 경로다. 배포물에는 공통 instruction-only skill을 두고 각 host의 discovery 위치에 연결·복사하는 adapter 규칙을 따로 적어야 한다. 모든 skill 폴더가 모든 제품에서 자동 발견된다고 가정하지 않는다. [Codex skill format and paths](https://learn.chatgpt.com/docs/build-skills), [Claude Code skills](https://code.claude.com/docs/en/skills), [Prime skill source](https://github.com/PrimeIntellect-ai/prime-agent/blob/main/crates/pa-core/src/skills/discovery.rs)

## 주요 함의 5가지

1. **데스크톱은 현존 agent를 그대로 묶는 경로가 있다.** Claude Desktop Code, Codex desktop/CLI, Prime Agent installer가 Mac·Windows host를 제공한다. Linux에서는 Claude Desktop이 beta이고 Codex app GUI가 없으므로 CLI·Paseo 경로가 현실적이다.
2. **iOS와 Android를 mobile remote-control 설명으로 충족했다고 표시하면 안 된다.** 현재 Claude, Codex, Paseo의 mobile UI는 다른 host에 붙는다. strict device-local 요건을 만족시키려면 phone 안에 별도 native execution host가 필요하다.
3. **API 추론과 local execution은 서로 다른 요구다.** 잠정 해석이 유지되면 prompt·context를 모델 API로 보내고, 저장소 변경·tool execution은 phone 안에서 실행하는 형태가 가능하다. 오프라인 모델 추론을 기본 전제로 묶을 필요는 없다.
4. **Paseo는 desktop 시작점이 될 수 있고 Prime은 custom ACP 후보지만, setup 마찰이 남는다.** Paseo Desktop은 daemon을 제공하되 underlying agent CLI와 인증은 요구한다. Prime ACP 경로는 catalog에 없는 별도 설정이며 상호운용 확인이 필요하다. skill 위치도 제품별로 매핑해야 한다.
5. **Mobile host는 후속 실증이 필요한 별도 제품 범위다.** iOS는 App Store 코드 실행 규칙·sandbox·background task를, Android는 sandbox·foreground service·Termux ABI와 지속 실행 제한을 설계해야 한다. 현재 근거로는 맞춤형 구현 가능성은 열려 있지만, 기존 CLI의 phone 지원이나 desktop parity를 약속할 수 없다.

**검증 한계:** 공식 문서, Prime Agent의 현재 README/Cargo/source와 latest release metadata를 조사했다. Jev 1.13의 보조 분류는 desktop 지원 / 현존 mobile CLI 비지원을 같은 방향으로 반환했지만, 최종 상태는 위의 문서·artifact evidence에 따른다. 실제 설치, Prime–Paseo ACP handshake, iOS/Android prototype, App Store/Play Store 심사는 실행하지 않았다. 이 네 항목은 후속 검증 대상이다.
