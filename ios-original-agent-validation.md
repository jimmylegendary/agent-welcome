# iOS에서 기존 agent CLI를 그대로 실행할 경로

**기준일: 2026-10-17.** 범위는 Claude Code, Codex CLI, Prime Agent의 기존 native/Linux CLI와 release를 iOS 기기 안에서 실행하는 경우다. 원격 host, agent 재구현, 다른 agent로 교체하는 경로는 제외한다. 모델 inference API는 root의 잠정 허용 가정이며, 이 조사는 설치·실행·인증을 하지 않았다.

## 핵심 판정

| 경로 | 원본 CLI 변경 없이 | 상태 |
|---|---|---|
| iSH + Alpine | 현재 release binary는 실행 불가 | **미지원**: iSH는 i386/x86 user-mode emulation, 세 제품 release는 64-bit |
| a-Shell | 현재 CLI binary를 설치해 실행하는 경로 없음 | **미지원**: WebAssembly command layer는 socket/fork가 없고 Linux ELF 실행기가 아님 |
| UTM SE + x86_64 Linux guest | guest ABI가 맞으면 실행할 후보 | **실험적·미검증**: agent binary는 수정하지 않을 수 있으나 UTM SE 속도·network·VM 호환성을 실증하지 않음 |
| iSH용 i686 포트 | 기존 artifact로는 불가 | **재빌드/포트 필요**: Codex·Prime은 i386 target이 없고 Claude Code는 재빌드 가능한 원본 source가 없음 |

**최초 실험 추천:** UTM SE App Store 앱에 x86_64 Linux guest를 올리고, Codex의 x86_64-musl binary부터 `--version`만 확인한다. Codex와 Claude Code의 Alpine x86_64 target은 guest ABI가 가까우며, Prime Agent의 현재 Linux x64 artifact는 GNU target이라 Debian/Ubuntu x86_64 guest에서 별도로 시험하는 편이 낫다. 이것은 원본 agent를 바꾸지 않고 **기기 안의 VM에서** 실행하는 후보지만, 아직 성공 사실은 아니다.

## 근거로 확인한 target/runtime

- **iSH:** project는 Linux shell을 iOS에서 실행하기 위한 user-mode x86 emulator와 syscall translation이라고 설명하며, README의 test rootfs는 Alpine **i386**이다. 따라서 iSH는 64-bit Linux VM이 아니다. `uname -m`/`getconf LONG_BIT` 결과는 설치 후 확인할 진단값으로만 취급한다. [iSH README](https://github.com/ish-app/ish)
- **Codex CLI:** OpenAI package target source는 Linux `x86_64-unknown-linux-musl`과 `aarch64-unknown-linux-musl`을 나열하고 i386 target은 없다. x86_64-musl ELF는 iSH의 32-bit process 안에서 실행되지 않는다. [Codex target table](https://github.com/openai/codex/blob/main/scripts/codex_package/targets.py)
- **Claude Code:** 공식 지원 표에는 Linux x64/ARM64와 Alpine 3.19+가 있다. npm 설치에는 Node 22+가 필요하지만 npm 경로도 native binary를 받는다. 따라서 Node가 iSH에서 동작해도 unsupported i386 Claude binary를 해결하지 않는다. [Claude Code setup](https://code.claude.com/docs/en/getting-started)
- **Prime Agent:** 2026-10-17에 조회한 latest release는 v0.10.0(2026-10-09)이며 Linux x64·ARM64 tarball과 `x86_64-unknown-linux-gnu` / `aarch64-unknown-linux-gnu` SBOM만 있다. 저장소는 Rust/Cargo workspace이고 README는 persistent Python REPL을 tool runtime으로 설명한다. i386 artifact는 없다. [latest release metadata](https://api.github.com/repos/PrimeIntellect-ai/prime-agent/releases/latest), [Prime Agent repository](https://github.com/PrimeIntellect-ai/prime-agent)
- **Node/Bun:** Node 22.22.0의 공식 Linux binary 표는 x64, ARMv7, ARM64, ppc64le, s390x 등을 제공하고 Linux i386는 없다. Bun의 Linux binaries는 x64·ARM64의 glibc/musl variant다. Alpine `apk`에 Node package가 있는지는 별도 사실이지만, 설치 성공은 agent native binary bitness를 바꾸지 않는다. [Node.js v22.22.0 archive](https://nodejs.org/en/download/archive/v22.22.0), [Bun installation targets](https://bun.sh/docs/installation)
- **a-Shell:** README는 자체 packaged native commands와 WebAssembly command 설치를 설명하지만 WASM에 socket/fork가 없다고 명시한다. 따라서 stock Codex/Claude/Prime Linux CLI를 WASM으로 바로 넣을 수 있다는 근거는 없다. WASI/iOS port는 별도 구현으로 분류해야 한다. [a-Shell README](https://github.com/holzschu/a-shell)

## UTM SE: stock binary 후보와 제한

UTM SE는 App Store에서 받을 수 있고 JIT 없이 threaded interpreter로 emulation한다. UTM project 문서는 SE에 x86 32-bit·64-bit variants가 포함된다고 적고, iOS installation 문서는 Alpine 같은 stripped-down OS를 실행 예로 든다. 그 조합은 x86_64 Linux guest의 가능성을 만든다. guest boot 또는 agent launch가 성공했다고 직접 재현한 것은 아니다. [UTM iOS installation](https://docs.getutm.app/installation/ios/), [UTM README / architectures](https://github.com/utmapp/UTM)

UTM SE throughput은 vendor 문서상 JIT보다 느리다는 정성 정보뿐이다. iOS UTM SE 문서만으로 guest networking 설정·동작을 확정할 수 없다. API inference를 쓰려면 guest network, DNS, TLS가 우선 preflight다.

**Community report (재현 아님):** UTM issue #7722는 2026-05-24에 Bun 1.3.14가 UTM SE의 Alpine aarch64/musl guest에서 file/path API 오류를 낸다고 보고한다. 제보자는 같은 guest와 Bun binary를 JIT UTM에서 비교해 문제가 없었다고 적었다. 이는 한 Bun/aarch64 환경의 사용자 보고일 뿐, x86_64 guest 또는 세 agent의 일반 실패 근거가 아니다. [UTM issue #7722](https://github.com/utmapp/UTM/issues/7722)

iOS App Store의 Guideline 2.5.2는 app feature를 바꾸는 코드를 download/install/execute하는 일을 제한하고, 2.5.4는 background service를 목적에 맞게 제한한다. Apple background APIs는 refresh와 processing 작업을 구분하지만 항상 실행되는 daemon을 약속하지 않는다. UTM SE 앱을 foreground에서 실행하는 VM 경로와, 별도 app에 agent code를 bundle/execute하는 경로는 심사 질문이 다르다. VM이 background에서 계속 돈다고 가정하지 말고 세션 복구를 설계한다. [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/), [Apple background tasks](https://developer.apple.com/documentation/uikit/using-background-tasks-to-update-your-app)

## 예외 자동 대응용 guide records

| Condition | Diagnostic candidate | Recovery candidate | Verify candidate |
|---|---|---|---|
| `Exec format error`, `wrong ELF class`, 즉시 종료 | `uname -m`; `getconf LONG_BIT`; `apk --print-arch`; `file <binary>`; `readelf -h <binary>` | iSH에서 재설치를 반복하지 않는다. i386 guest와 x86_64/ARM64 binary가 다르면 UTM SE x86_64 guest를 다음 시험 후보로 제시한다. | guest 결과가 x86_64/64-bit이고 ELF `Class`/`Machine`도 맞는지 비교한다. 이 통과만으로 agent 실행 성공을 판정하지 않는다. |
| 파일은 있는데 loader `not found` | `readelf -l <binary>`로 실제 PT_INTERP 존재·경로 확인; 해당 loader 파일과 guest `/etc/os-release` 확인 | 실제 ELF와 요구 library에 맞는 userland를 선택한다. Prime의 확인된 GNU/glibc 요구는 Debian/Ubuntu 후보와 연결한다. Codex는 musl target 이름만으로 동적 loader가 필요하거나 Alpine만 가능하다고 가정하지 않는다. | ELF의 정적/동적 상태와 필요한 interpreter/library를 확인한 뒤 `--version`을 별도로 시험한다. |
| `SIGILL`, `ENOSYS`, `Operation not permitted` | 가능하면 `strace <binary> --version`; iSH의 syscall trace; 동일 guest/binary를 UTM SE에서 비교 | emulated instruction/syscall 문제가 있으면 iSH를 중단하고 x86_64 VM 후보로 전환한다. source rebuild는 original CLI 성공과 별도 포트로 기록한다. | `--version` 통과 후 read-only 프로젝트 조회, 마지막에 scratch repo의 파일 하나만 수정하는 단계로 올린다. |
| Node/Bun 설치는 되지만 agent 실행 실패 | `node --version`; `bun --version`; `apk --print-arch`; `file <agent-binary>` | Node/Bun 설치 성공과 agent binary 호환성을 분리한다. i386 Alpine에서 64-bit binary를 실행할 수 없으면 UTM x86_64 guest를 다음 후보로 검토한다. | wrapper version과 하위 native binary의 ELF machine을 각각 기록한다. |
| VM에서 API host/DNS 실패 | `ip route`; `getent hosts api.openai.com`; `curl -I https://api.openai.com/` (credential 없이) | UTM SE network option이 노출되는지 확인한다. guest networking/DNS가 해결되지 않으면 현재 API-inference 가정으로는 이 경로를 중단한다. | 인증 전에 DNS/TLS 연결만 검증한다. 이후 인증은 사용자의 공식 로그인 또는 전용 key 입력 흐름으로 진행한다. |
| app 전환 뒤 agent/VM이 멈춤 | UTM foreground 복귀 후 guest console·저장 상태 확인 | UTM SE를 상시 background daemon으로 취급하지 않는다. foreground 작업과 guest disk의 resumable session을 우선한다. | VM을 다시 열어 저장된 repo와 agent session이 복구되는지 확인한다. |

## Patch 경계와 검증 계획

- **원본 binary 유지 후보:** UTM SE 안의 x86_64 Linux guest에서 Codex/Claude/Prime의 기존 Linux x64 package를 실행한다. OS image, ABI, network, UTM SE speed만 바꾸는 접근이다. Linux x86_64 guest 자체와 agent 실행은 미검증이다.
- **재빌드/patch 후보:** iSH에서 Codex/Prime i686 target을 새로 빌드하고 syscall/Python runtime을 포팅한다. Codex/Prime source가 열려 있어도 현재 official packages에 없는 target이며, 성공을 보장하지 않는다. Claude Code는 공개 source가 없어 공식 i386 recompile 경로가 없다.
- **Root가 이후 실행할 정확한 command 후보(이번 조사에서는 실행하지 않음):**

```sh
# iSH identity only
uname -m
getconf LONG_BIT
apk --print-arch
apk search nodejs

# UTM guest identity, libc and no-credential network preflight
uname -m
getconf LONG_BIT
cat /etc/os-release
ldd --version
ip route
getent hosts api.openai.com

# After the chosen official installer has been run inside the guest
file "$(command -v codex)"
readelf -h "$(command -v codex)" | grep -E 'Class|Machine'
readelf -l "$(command -v codex)" | grep interpreter
codex --version
claude --version
prime-agent --version
```

Claude x86_64 Alpine guest candidate: install documented Alpine prerequisites (`bash`, `curl`, `libgcc`, `libstdc++`, `ripgrep`), set `USE_BUILTIN_RIPGREP=0` per Claude docs, then use `curl -fsSL https://claude.ai/install.sh | bash`. Codex x86_64-musl guest candidate: `curl -fsSL https://chatgpt.com/codex/install.sh | sh`. Prime GNU guest candidate: `curl -fsSL https://app.primeintellect.ai/prime-agent/install.sh | sh`. These are future commands, not run results. Prime should start in a glibc guest; Claude docs specifically list Alpine 3.19+; Codex package target is musl.

**Evidence class:** official docs/source establish architecture targets, UTM SE's no-JIT design, and iOS background rules. The Bun/UTM issue is a community report. UTM x86_64 guest running the three CLIs is an inference and proposed experiment; no device, VM, installer, binary, API credential, or agent was exercised here.
