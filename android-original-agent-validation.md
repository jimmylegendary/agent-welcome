# Android에서 원본 agent CLI 실행 경로 조사

**조사일:** 2026-10-17

**범위:** Termux native Bionic, PRoot-Distro OCI userland, Claude Code/Codex/Prime Agent 공식 Linux ARM64 artifact. Android 기기 설치·실행·로그인은 하지 않았고 별도 agent fork도 만들지 않았다.

## 결론

가장 넓은 원본 CLI 검증 후보는 **같은 휴대폰의 Termux 안에서 PRoot-Distro로 Ubuntu 24.04 또는 Debian 12 userland를 실행**하는 경로다. Prime Agent 공식 Linux ARM64 release는 glibc를 요구하고, Claude Code에도 Linux ARM64 variant가 있다. Codex는 공식 ARM64 musl artifact를 별도 시험할 수 있다. agent process와 파일은 같은 Android 기기에서 실행되므로 원격 PC/cloud host가 아니다.

PRoot-Distro는 VM이나 kernel container가 아니다. Android kernel과 Termux app UID를 공유하고 syscall을 ptrace로 번역한다. 최신 README는 cgroups/namespaces, real root, systemd/OpenRC, 중첩 proot가 지원되지 않으며 filesystem-heavy 작업이 느려질 수 있다고 명시한다. Codex 기본 Linux sandbox가 PRoot 안에서 동작한다고 가정할 수 없다. Sandbox 단계가 실패하면 첫 smoke를 멈춘다. Sandbox를 끄고 성공 처리하지 않는다. [PRoot-Distro README](https://github.com/termux/proot-distro/blob/master/README.md)

두 번째 후보는 **Termux native에서 Codex 공식 ARM64 musl artifact만 좁게 검증하는 것**이다. 공식 artifact는 있지만 Bionic target은 아니며, Codex 0.159.1 app-server가 Termux의 /tmp 부재 때문에 실패했다는 upstream issue가 있다. ChatGPT OAuth token exchange 실패도 별도로 보고됐다. 여기서는 version/ABI 및 임시 경로·sandbox gate까지만 확인한다.

Codux는 Debian PRoot에 Codex official Linux ARM64 musl artifact를 설치한다고 주장하는 community installer다. Upstream Codex fork라고 하지 않지만, current script는 latest/download를 사용하고 checksum 검사를 하지 않으며 기본값으로 Termux 전체 package upgrade를 실행한다. 참고 사례로 기록하되 그대로 실행할 기본 installer로 추천하지 않는다.

Claude Code용 Termux musl shim은 별도 경로다. Anthropic linux-arm64-musl binary를 받아 ELF interpreter 경로를 수정하고 DNS proxy 및 환경 조정을 추가한다고 설명한다. Claude Code 실행 logic을 fork하지 않는다고 주장하지만 결과 binary는 upstream 원본과 byte-identical하지 않고 Android는 vendor 지원 target이 아니다. 작성자 기기의 사례이며 여기서 재현하지 않았다.

우선 검증 순서는 1) PRoot-Distro에서 Claude Code와 Prime Agent version gate, 2) Codex standalone artifact integrity와 sandbox gate, 3) 별도 비교로 native Termux Codex version/temp-path gate다. Jev 1.13은 advisory ranking에서 PRoot 원본 artifact 경로를 앞에 두었지만, 실행 판단은 문서·artifact·device validation이 결정한다.

## Host ABI와 공식 artifact

| Agent | Official artifact, 버전, checksum | ABI/runtime 사실 | Android 판단 |
|---|---|---|---|
| Codex | **rust-v0.159.1**, **codex-aarch64-unknown-linux-musl.tar.gz**, 96.3 MB, SHA-256 **84e7be7c58ef9b6e1609d9c5f14a8e92506fbf276dc35c76a8f121e83620af95**. [Release](https://github.com/openai/codex/releases/tag/rust-v0.159.1), [assets/checksum](https://github.com/openai/codex/releases/expanded_assets/rust-v0.159.1), [direct asset](https://github.com/openai/codex/releases/download/rust-v0.159.1/codex-aarch64-unknown-linux-musl.tar.gz). | Official target map은 aarch64-unknown-linux-musl을 표시하고 Android target은 없다. Musl target은 확인했으나 binary를 내려받아 PT_INTERP, static/dynamic status, DT_NEEDED를 읽지는 않았다. Standalone Rust artifact는 Codex npm wrapper와 다른 설치 경로다. Linux sandbox는 bubblewrap/user namespaces를 사용한다. [target map](https://github.com/openai/codex/blob/main/scripts/codex_package/targets.py), [sandbox design](https://github.com/openai/codex/blob/main/codex-rs/linux-sandbox/README.md) | Native Termux에서 시작했다는 issue가 있으나 Bionic 호환 보증은 아니다. Full CLI/sandbox 미검증. |
| Claude Code | 2026-10-17에 조회한 official stable은 **2.1.292**. linux-arm64: 250,798,072 bytes, SHA-256 **24caa9e6ff13bf227049a2626f1c816fc895023050f0ec3b12dbf14d897367e0** ([artifact](https://storage.googleapis.com/claude-code-dist-86c565f3-f756-42ad-8dfa-d59b1c096819/claude-code-releases/2.1.292/linux-arm64/claude)); linux-arm64-musl은 243,152,704 bytes, SHA-256 **a17c919b13df206371a55de716ab81e3dcd7c039f66b79003ed87b7665fdc15f** ([artifact](https://storage.googleapis.com/claude-code-dist-86c565f3-f756-42ad-8dfa-d59b1c096819/claude-code-releases/2.1.292/linux-arm64-musl/claude)). [manifest](https://storage.googleapis.com/claude-code-dist-86c565f3-f756-42ad-8dfa-d59b1c096819/claude-code-releases/2.1.292/manifest.json) | Official setup은 Linux ARM64와 musl variant를 나눈다. npm 설치는 Node.js 22+와 optional platform dependency/postinstall을 쓰며 결과 native binary는 runtime에서 Node를 호출하지 않는다고 문서화한다. Android/Bionic target은 지원 목록에 없다. Bun runtime 포함 주장은 upstream issue reporter의 관측이며 공식 Android 지원 근거가 아니다. [setup](https://code.claude.com/docs/en/setup) | Termux Bionic은 glibc도 musl도 아니다. PRoot 안의 matching Linux userland에서만 시험한다. |
| Prime Agent | **v0.10.0**, **prime-agent-0.10.0-linux-arm64.tar.gz**, 20.8 MB, SHA-256 **f3cab3530a4d7ca43dbef8321bf13f260d1ba05d8b5dde057165a20bd4f675c4**. [Release](https://github.com/PrimeIntellect-ai/prime-agent/releases/tag/v0.10.0), [official installer](https://github.com/PrimeIntellect-ai/prime-agent/blob/763094e1b6a7c17450ee8399b06cda1853847ca5/install-rust.sh) | Official installer는 Linux ARM64를 GNU/glibc로 처리하며 glibc >= 2.35를 요구하고 musl을 거부한다. Rust CLI는 uv로 Python kernel을 bootstrap하며 첫 실행에 runtime package/network가 필요할 수 있다. 기본 Rust release에는 Node/Bun이 필요하지 않다. | Termux Bionic과 맞지 않는다. Ubuntu 24.04/Debian 12 PRoot가 ABI fit 후보이나 Python bootstrap, subprocess, TUI는 미검증이다. [RLM runtime](https://github.com/PrimeIntellect-ai/prime-agent/blob/main/packages/coding-agent/docs/rlm-runtime.md) |

**Artifact validation limit:** SHA-256은 공급자 release manifest/release listing에서 읽었다. Binary를 내려받아 SHA를 재계산하거나 ELF header를 분석하지 않았다. Codex와 Claude의 정확한 ELF interpreter 및 symbol floor는 미확인이다. Prime glibc floor는 binary analysis가 아니라 official installer 사전 검사에서 확인했다.

## Android paths

| Path | 확인된 내용 | 남은 위험·미확인 | 평가 |
|---|---|---|---|
| Termux native Bionic | Termux native package는 Android NDK/Bionic을 사용하고 Android host kernel을 공유한다. [Termux execution environment](https://github.com/termux/termux-packages/wiki/Termux-execution-environment) | 이 세 agent의 official Android target은 없다. Codex musl은 Bionic이 아니고 Claude에 glibc/musl Linux build만 있으며 Prime은 glibc다. | Codex version/temp-path probe만. 전체 host 경로로 보지 않는다. |
| PRoot-Distro Debian/Ubuntu | Current OCI flow 예시는 **proot-distro install ubuntu:24.04**, **proot-distro login ubuntu**. 같은 Android 기기에서 실행한다. [Current README](https://github.com/termux/proot-distro/blob/master/README.md) | Namespaces/cgroups/seccomp, real root, systemd/OpenRC, nested proot가 없고 ptrace overhead가 있다. Codex bwrap sandbox가 PRoot에서 동작하는지 미검증이다. | Claude/Prime 원본 Linux artifact의 가장 넓은 후보; Codex sandbox는 별도 gate. |
| Codux community installer | README는 OpenAI Codex Linux ARM64 musl release를 Debian PRoot에서 사용하는 경로와 설치 화면을 제시한다. 특정 기기 모델의 성공은 이번에 확인한 본문에서 입증하지 못했다. [README](https://github.com/Clock-Skew/Codux/blob/bf85202aebffed078b6835413d7e651ec274bd9c/README.md), [installer script](https://github.com/Clock-Skew/Codux/blob/bf85202aebffed078b6835413d7e651ec274bd9c/codux.sh) | Script는 latest/download, checksum 검사 미발견, default pkg upgrade -y다. Script는 bubblewrap을 설치하고 PRoot/Android 제약 가능성을 안내한다. Device-code login helper도 script에서 확인했으나 실행하지 않았다. | 유용한 community guide; official installer도 다운로드 무결성을 직접 검증한 경로도 아니다. |
| Claude Termux musl shim | [Aarstad guide](https://github.com/Aarstad/claude-code-termux-musl)는 official musl binary와 Termux 실행 경로를 주장한다. | ELF interpreter 변경, loader, DNS proxy, child 환경 조정이 필요하며 단일 기기 보고다. | User가 patched binary를 허용할 때의 별도 advanced route. 기본 경로가 아니다. |

PRoot-Distro는 container-security boundary가 아니다. Android kernel 및 Termux app UID를 공유하므로 보호 기능을 제공한다고 광고하지 않는다. ([PRoot limitations](https://github.com/termux/proot-distro/blob/master/README.md#limitations))

## Known error → condition → diagnostic → recovery → verify

| KG ID / confidence | Condition → symptom | Diagnostic | Candidate recovery | Verification / source |
|---|---|---|---|---|
| ANDROID-ABI-01 / high | Termux native Bionic에서 glibc Linux binary 실행 시 loader/library error. | Device uname/SDK와 file/readelf ABI, PT_INTERP, DT_NEEDED 기록. | Official glibc artifact는 matching Linux userland 안에서만 시험. | Official ELF inspection 후 성공 여부. [Termux ABI](https://github.com/termux/termux-packages/wiki/Termux-execution-environment). Binary 미검사. |
| CODEX-TERMUX-TMP-01 / medium, version-specific | Termux native + Codex 0.156.1/0.159.1 + Android ARM64 non-root: app-server Unix socket에서 No such file or directory; reporter는 /tmp 부재, / read-only를 기록. | Version, listen mode, /tmp 존재·쓰기, Termux TMPDIR 기록. 다른 CLI operation까지 모두 실패한다고 일반화하지 않음. | PRoot 표준 /tmp에서 같은 pinned version 확인은 가설. | Socket listener 및 같은 app-server command가 성공해야 한다. [Codex #49402](https://github.com/openai/codex/issues/49402), 2026-09-29. |
| CODEX-TERMUX-OAUTH-01 / low-medium | Termux ChatGPT OAuth: browser callback localhost:1455 후 auth.openai.com/oauth/token failure 보고. | Browser callback과 HTTPS/DNS/TLS token exchange를 분리. Credential은 로그에 남기지 않음. | Foreground Termux에서 한 번 재현하고 실패 시 version/network 상태 기록. 사용자 보유 API key는 별도 선택이지 OAuth 복구가 아님. | codex login 완료 뒤 read-only prompt로 검증. [Codex #36318](https://github.com/openai/codex/issues/36318), version unset, fix 미확인. |
| CODEX-PROOT-SANDBOX-01 / PRoot limit high, combo failure inferred | PRoot에 real namespace 없음; Codex Linux sandbox는 bubblewrap/user namespaces를 씀. | Future probe codex sandbox -- /bin/true 결과, bwrap path/version, userns error. | 지원되는 PRoot recovery 미확인. Sandbox를 bypass하지 말고 strict constraint에서 멈춘다. | Sandbox command 성공이 기준. [PRoot limits](https://github.com/termux/proot-distro/blob/master/README.md#limitations), [Codex sandbox](https://github.com/openai/codex/blob/main/codex-rs/linux-sandbox/README.md). |
| CLAUDE-BUN-NPM-01 / medium, package-manager-specific | Claude 2.1.113 + Bun 1.3.11에서 Bun으로 global package를 설치할 때 postinstall 차단 뒤 binary missing이 보고됨. | Blocked 1 postinstall/native binary missing과 platform version 기록. | 지원 Linux에서는 official native installer 또는 해당 package의 postinstall/optional dependency 설정 확인. Android 지원으로 일반화하지 않음. | claude --version. [Claude #50203](https://github.com/anthropics/claude-code/issues/50203), [official setup](https://code.claude.com/docs/en/setup). |
| PRIME-GLIBC-01 / high | Termux Bionic/musl vs Prime Linux ARM64 release: glibc mismatch. | PRoot 내부 ldd --version과 prime-agent version 기록. aarch64 일치만으로 ABI fit 판단 금지. | Ubuntu 24.04/Debian 12 PRoot glibc >=2.35 후보. | SHA → prime-agent --version → doctor → Python kernel → read-only task. [Prime release](https://github.com/PrimeIntellect-ai/prime-agent/releases/tag/v0.10.0), [installer](https://github.com/PrimeIntellect-ai/prime-agent/blob/763094e1b6a7c17450ee8399b06cda1853847ca5/install-rust.sh). |
| TERMUX-URL-FOREGROUND-01 / low, historical scope | Termux background 중 Android ACTION_VIEW: Android 10/Termux API 0.50.1 issue에서 chooser가 안 열렸다고 보고. | SDK, Termux/API version, foreground state, browser open/callback을 기록. | First login 때 Termux foreground 유지. URL open 검증은 OAuth token exchange를 증명하지 않음. | Browser open 및 local callback 별도 확인. [termux-open-url](https://github.com/termux/termux-tools/blob/master/scripts/termux-open-url.in), [issue #509](https://github.com/termux/termux-api/issues/509). |
| CLAUDE-TERMUX-MUSL-SHIM-01 / low, community single-device | Stock Claude Linux artifact in Bionic: loader/DNS/LD_PRELOAD issue라고 community guide 주장. | Upstream/patched hash 분리, readelf interpreter, proxy/DNS/login 확인. | Guide는 musl loader relocation, Termux preload drop, DNS proxy 제안. | Patched file integrity, version, auth 통과 필요. [Aarstad guide](https://github.com/Aarstad/claude-code-termux-musl), 독립 재현 없음. |
| CODUX-INSTALLER-01 / low, community source | Codux 0.1.4는 Android ARM64/Termux + Debian PRoot에서 official Codex musl latest와 device-auth helper를 쓴다고 주장. | Release URL, checksum, image pin, package side effect, bwrap 확인. | Latest URL 대신 pin/checksum이 필요. Script는 checksum code 미발견, default pkg upgrade -y. | 확인한 README revision에서는 특정 휴대폰 모델의 성공을 입증하지 못했다. [README](https://github.com/Clock-Skew/Codux/blob/bf85202aebffed078b6835413d7e651ec274bd9c/README.md), [script](https://github.com/Clock-Skew/Codux/blob/bf85202aebffed078b6835413d7e651ec274bd9c/codux.sh). 실행 안 함. |

## First smoke gate와 follow-up command 후보

아래는 설치기 구현 단계에서 사용할 검증 절차 후보다. 이번에는 guide·배포 metadata·소스를 조사했으며, 이 command들을 Android 기기에서 실행하지 않았다.

**0. Device/tool inventory**

- **uname -m**
- **getprop ro.build.version.sdk**
- **command -v file readelf sha256sum tar git rg node bun python termux-open-url**

Host architecture, Android SDK, Termux app/API version을 기록한다. 실제 출력은 아직 없다.

**1. Artifact integrity/ELF inspection**

- **sha256sum ARTIFACT**를 official checksum과 대조.
- **tar -tzf ARTIFACT**로 archive members만 목록 확인.
- **tar -xzf ARTIFACT -C STAGING_DIR**로 해당 시험에 지정한 별도 staging path에 추출.
- **file BINARY**, **readelf -h -l BINARY**, **readelf -d BINARY**로 machine, PT_INTERP, DT_NEEDED 확인.

Artifact는 hash 대조 전에 실행하지 않는다. Claude manifest 값은 official metadata에서 읽었지만 다운로드 binary와 재대조하지 않았다.

**2. CLI surface gate, auth 전**

- **claude --version**, **claude doctor**
- **codex --version**, **codex sandbox -- /bin/true**
- **prime-agent --version**, **prime-agent doctor**

이 probe는 rust-v0.159.1의 host backend parser를 기준으로 한다. 실제 보안 검증에는 선택한 permission profile을 별도로 기록해야 하며, profile이 미정이면 sandbox check 완료로 취급하지 않는다. [고정 parser](https://github.com/openai/codex/blob/8e68a98ef03cdde76d2e6800791ebdf1b3b95b24/codex-rs/cli/src/lib.rs#L106-L147).

Codex sandbox probe가 실패하면 sandbox를 비활성화하지 말고 멈춘다. Version check는 executable startup만 보여주며 auth, Python kernel, file tools, browser, background behavior를 증명하지 않는다.

**3. Login/read-only tool smoke, 사용자 auth 범위가 정해진 다음**

- Claude: TUI 시작 후 **/login**, provider/model API를 기록.
- Codex: **codex login**; browser callback과 token exchange를 분리 기록. **codex login --device-auth**는 공식 문서에 있는 device code 인증(beta)이며 계정/조직에서 사용을 허용해야 한다. Codux는 이를 호출하는 community helper를 제공한다. Android에서의 인증 성공은 미검증이며 token exchange 실패 전체를 해결한다고 가정하지 않는다. [공식 headless/device code 인증](https://learn.chatgpt.com/docs/auth#login-on-headless-devices)
- Prime: TUI에서 **/login**, provider 선택과 Python kernel startup 기록.
- 각 host를 app-private scratch folder에서 열고 “현재 폴더의 파일명만 읽고 반환해. 아무것도 바꾸지 마.”를 요청. Process/path가 같은 휴대폰인지 확인.

초기 smoke에서는 Playwright/Chromium, screenshot/image/PDF/media, MCP, subagents, schedule을 제외한다. Android는 background app에서 foreground service 시작이 제한되고 OS가 process를 관리하므로 Termux/PRoot 상시 실행을 약속하지 않는다. [Android FGS rules](https://developer.android.com/develop/background-work/services/fgs/restrictions-bg-start)

## Evidence status

- 공식 release·manifest·소스에서 artifact 이름, ABI target, 배포자가 게시한 checksum을 확인했다. binary를 다운로드해 자체 hash를 계산하거나 ELF를 분석한 결과는 아니다.

- upstream issue와 커뮤니티 guide는 작성자가 보고한 환경·version의 근거다. 현재 모든 Android 기기의 실행 성공이나 재현된 복구로 표시하지 않는다.

- 이 조사에서 세 agent의 설치, 실행, 로그인, model/API 요청, PRoot container 생성은 수행하지 않았다. 제시한 command는 후속 시험 후보이며 실행 기록이 아니다.

- KG에는 source·version·적용 조건과 진단·복구·성공 확인을 분리해서 저장한다. 문서상 후보를 자동 실행 가능한 검증된 recipe로 승격하려면 해당 검증 기록이 필요하다.
