# PR #1 review follow-up verification

Base reviewed revision: `f3c35a3573a84b7874f0e6b2fe59ede675e44c9d`.

This follow-up remains a **`binary_installation` reference**.  A passed
installation check does not claim provider authentication, Python-kernel setup,
model-task completion, or general runtime support.

## Review findings: reproduction, correction, and regression coverage

| Finding | Reproduction at the reviewed revision | Correction | Regression evidence |
|---|---|---|---|
| Retry exhaustion became `WAITING_USER` when resumed without an artifact. | Two digest failures consume `per_step: 2`; the next artifact-less resume took the wait branch before the retry check. | Evaluate the bounded budget before advertising an artifact wait. | `test_retry_budget_and_recipe_or_environment_drift_are_persisted` now requires `FAILED`, `retry_exhausted: true`, and not `WAITING_USER`. |
| A successful recovery retained current `failure_evidence`. | A bad digest followed by a valid fixture reached `SUCCEEDED` while the singular current failure record still described the bad archive. | Set `failure_evidence` to `null` on both direct and reconciled success; keep every record in `failure_history`. | `test_digest_failure_can_resume_with_correct_archive_without_stale_success_record`. |
| Managed installation removal preceded validation of a recovery attempt. | After an owned install was invalidated, a supplied nonexistent archive would be resolved only after removal. | Check the retry budget and resolve the supplied archive/download before deleting an owned invalid installation. | `test_invalid_recovery_input_preserves_owned_installation` and `test_exhausted_repair_budget_preserves_owned_installation`; invalid input and exhausted budget both leave the altered managed payload present. |
| Android was observed as `linux_userland`, though the two native Android Claude candidate routes require `native`; `platform.system() == "Android"` was not normalized. | Android API observations entered the Linux branch but received the generic Linux-userland runtime kind; direct Android system strings produced an unrecognized kernel value. | Normalize both direct Android and Android-API observations to `kernel_os: linux`, `host_os: android`, and `runtime_kind: native`.  The route nodes remain `runtime_tested: false`, and required checks are still required. | `test_android_system_and_api_observations_are_native_linux_kernel` and `test_native_android_observation_matches_claude_candidates_without_promotion`. |
| Cache reuse hashed an existing path using blocking `Path.open()`. | A FIFO placed at the state-local cache path can block before the existing external-archive snapshot guard runs. | Open cached entries with `O_NONBLOCK`/`O_NOFOLLOW` where available, verify the opened descriptor is a regular file, and reject cache-path changes before replacement. | `test_cached_fifo_is_rejected_without_blocking` runs in a subprocess with a two-second bound. |

## Commands and observed results

All temporary fixture state was created under a temporary directory; no user
agent installation, account, credential, or external service was changed.

| Environment | Command | Result |
|---|---|---|
| Windows 11, Python 3.13.5 | `python -m agent_welcome validate` | `VALID`; schema 0.2, 88 nodes, 145 links, 5 playbooks. |
| Windows 11, Python 3.13.5 | `python -m agent_welcome diagnose --recipe prime-agent-0.10.0-linux-arm64` | `NOT_APPLICABLE` (no ARM64/glibc recipe match). |
| Ubuntu 24.04 WSL2, Python 3.12.3, x86_64 | `python3 -m agent_welcome validate` | `VALID`; same catalog counts. |
| Ubuntu 24.04 WSL2, Python 3.12.3, x86_64 | `python3 -m agent_welcome diagnose --recipe prime-agent-0.10.0-linux-arm64` | `NOT_APPLICABLE` (x86_64, not the ARM64 recipe). |
| Ubuntu 24.04 WSL2, Python 3.12.3 | `python3 -m unittest discover -s tests -v` | `Ran 57 tests ... OK`, including the bounded FIFO-cache test. |
| Ubuntu 24.04 WSL2, temporary directory | `download_artifact(...)` for the pinned official URL | Downloaded 21,858,488 bytes and verified SHA-256 `f3cab3530a4d7ca43dbef8321bf13f260d1ba05d8b5dde057165a20bd4f675c4`; the temporary archive was then removed without execution. |

The Windows test runner can validate the catalog and Android observation
normalization, but it cannot execute the POSIX shell fixture used as the
synthetic Linux payload (`WinError 193`).  The full executable fixture suite was
therefore run in WSL instead.  The sandbox's default Windows `%TEMP%` was not
writable; the Windows checks used a workspace-local isolated temporary
directory instead.

## Four-OS / three-original-agent matrix

`M` means an environment-value mock or catalog/contract check; `F` means a
synthetic fixture; `I` means ISA emulation; `O` means execution on the named
target OS; `U` means a real upstream binary; `A` means authenticated first
task.  A dash is intentionally not a support claim.

| Target OS | Original agent | M | F | I | O | U | A | Result / blocker |
|---|---|---:|---:|---:|---:|---:|---:|---|
| macOS | Codex CLI | — | — | — | — | — | — | No macOS runner/device attached. |
| macOS | Prime Agent | — | — | — | — | — | — | No macOS runner/device attached. |
| macOS | Claude Code | — | — | — | — | — | — | No macOS runner/device attached. |
| Windows | Codex CLI | host observation only | — | — | reference CLI only | — | — | Windows ran catalog/diagnose, not the original Codex CLI. |
| Windows | Prime Agent | host observation only | — | — | reference CLI only | — | — | ARM64 Linux recipe is `NOT_APPLICABLE`; no Prime binary executed. |
| Windows | Claude Code | host observation only | — | — | reference CLI only | — | — | Reference code only; no Claude Code installation. |
| iOS | Codex CLI | — | — | — | — | — | — | No iOS device/simulator attached. |
| iOS | Prime Agent | — | — | — | — | — | — | No iOS device/simulator attached. |
| iOS | Claude Code | — | — | — | — | — | — | No iOS device/simulator attached. |
| Android | Codex CLI | ✓ gate fixture | — | — | — | — | — | Candidate retains integrity, sandbox/profile, auth, and read-only-task gates. |
| Android | Prime Agent | ✓ compatible observation | ✓ archive + exact-version fixture | — | — | ✓ download + SHA only | — | WSL full suite verifies a synthetic payload; the official ARM64 archive was verified but not executed on x86_64. |
| Android | Claude Code | ✓ native-route contract | — | — | — | — | — | Both native candidate routes remain untested and cannot pass without checks. |

## Available-environment assessment and remaining constraints

- Windows 11 was available and used for non-runtime validation.
- Ubuntu-24.04 WSL2 was available and used for the Linux full suite.  It is
  Linux x86_64, so it is not an ARM64 emulator or an Android device.
- Docker CLI 28.0.4 was present but the Docker Desktop Linux engine was not
  running.  QEMU user-mode and Android `adb` were absent.
- The official pinned archive was downloaded into an automatically cleaned
  temporary directory and verified against its 21,858,488-byte size and pinned
  SHA-256.  It was not installed or executed: an ARM64 execution environment
  is still required for runtime compatibility.  Enabling/installing QEMU,
  starting Docker, or adding an Android device would require separate approval.
- No account sign-in was attempted.  Authentication and a first task remain
  explicitly unverified for every target and are not implied by this reference.

### ARM64/Android emulation prerequisites (not performed)

- The available Ubuntu 24.04 WSL2 package metadata lists
  `qemu-user-static` 1:8.2.2+ds-0ubuntu1.18 as a 14,709,858-byte download and
  133,302 KiB installed.  It is not installed.  Installing it requires a WSL
  system-package change and administrator authority.
- That package alone is insufficient for this glibc ARM64 artifact: an ARM64
  glibc userland/rootfs and loader are also required.  No foreign architecture
  is configured in the current WSL and no suitable rootfs is cached, so its
  download size cannot be measured locally.  `binfmt_misc` is mounted read/write,
  but registering a handler is another system-level configuration change.
- The Docker alternative requires starting the stopped Docker Desktop Linux
  engine, then pulling an ARM64 image (image-dependent size) and confirming its
  emulation support.  This changes a local service and downloads an image.
- A full Android emulator alternative requires Android SDK platform tools,
  emulator binaries, and an ARM64 system image; none is installed.  Its image
  size is not available locally, and installing/starting it may require VM or
  acceleration configuration.  A physical Android device instead requires an
  attached device plus explicit USB-debugging authorization.
