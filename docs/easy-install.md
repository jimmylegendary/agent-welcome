# Easy Install

Easy Install is a resumable implementation for all 12 target combinations. It
does not claim those combinations have been run on physical devices. The catalog
tracks implementation, fixture, actual OS, upstream binary, authentication, and
first-task evidence independently.

## Start and resume

Use the repository entry point after obtaining the repository:

```sh
./easy-install.sh --target macos-codex
python3 -m agent_welcome easy-resume --state-dir .agent-welcome/easy --agent-executable /absolute/path/to/codex
```

On Windows:

```powershell
.\easy-install.ps1 -Target windows-codex
.\easy-resume.ps1 -StateDir .agent-welcome\easy -AgentExecutable C:\absolute\path\to\codex.exe
```

The launchers locate this checkout automatically, so they work from another
current directory and do not require a manual `PYTHONPATH` or `cd`.

### Standalone bootstrap

When Python or a checkout is absent, use the standalone bootstrap script first.
It records all work beneath the explicit bootstrap state directory and does not
start an agent installer, modify PATH, or sign in:

```powershell
& .\easy-bootstrap.ps1 -Target windows-codex -StateDir C:\agent-welcome-bootstrap
# Review the recorded plan, then explicitly allow only the needed downloads:
& .\easy-bootstrap.ps1 -Target windows-codex -StateDir C:\agent-welcome-bootstrap `
  -ApproveRuntimeDownload -ApproveRepositoryDownload
```

Windows first probes `py -3` and `python` for Python 3.11+. If neither is
suitable, the approved path downloads the pinned official CPython embeddable
archive and unpacks it under `StateDir\runtime`; it does not run a global
installer or edit PATH. The fixed repository ZIP is downloaded only with its
separate approval, SHA-256 verified, ZIP-slip/symlink checked, and atomically
placed at `StateDir\repository`. An unrelated existing runtime or repository
directory is preserved rather than overwritten.

On Unix:

```sh
./easy-bootstrap.sh --target macos-codex --state-dir "$HOME/.agent-welcome/bootstrap"
# After reviewing the pinned repository plan:
./easy-bootstrap.sh --target macos-codex --state-dir "$HOME/.agent-welcome/bootstrap" \
  --approve-repository-download
```

The Unix script probes `python3`/`python` for 3.11+. If none exists, it records
a supported `apt-get`, `dnf`, `pacman`, or `apk` command as a user-owned,
consented runtime plan. It intentionally does not execute that global
package-manager command: the product contract permits runtime writes only in
the declared state directory. After the user completes that external step,
rerun the same bootstrap state. The pinned archive details are committed in
[`bootstrap-manifest.json`](../bootstrap-manifest.json); network failure or a
bad hash leaves the existing repository untouched.

Use `easy-plan --target ID` to view an agent route without changing the
machine and `easy-status --state-dir DIR` to inspect durable agent progress.

## Consent-gated installer adapter

The state machine orders direct environment observation, prerequisites, agent
installation, a state-local launcher, provider authentication, and a minimal
first task. Before it runs a vendor installer, it records the official HTTPS
download URL, exact `shell=False` argv, expected scope, and recovery commands in
`WAITING_USER(installer_consent)`. Running again with `--approve-install`
downloads the script beneath `DIR/downloads`, records byte count and SHA-256, and
executes it as an argv list without a shell pipeline. It then requires a real
`--version` probe of the discovered or explicitly supplied absolute executable.

This consent is a product user action, not permission to change this connected
computer: this delivery does not pass `--approve-install`. The adapter does not
request elevation, disable security policy, overwrite an existing installation,
or alter a system PATH itself. A vendor installer may modify its documented
user-level paths; that possible scope is displayed before consent. A launcher is
always written only under `DIR/bin`.

If execution is interrupted after the installer starts, the durable state marks
the outcome unknown. Resume probes an explicitly supplied executable first and
never reruns the installer automatically. Download interruption, bad exit status,
wrong or missing version, permissions, low disk space, target drift, and retry
exhaustion become structured failure evidence/history.

On Android, when this launcher is running in directly observed Termux Linux
userland, the prerequisite plan is also executable rather than a manual-only
placeholder. After `--approve-prerequisites`, it runs the exact argv commands
`pkg install -y proot-distro` and `proot-distro install ubuntu` on that
same device, records hashed output, then waits for the user to enter that guest
before continuing. An interruption is never rerun automatically. iOS cannot
create/import/boot a UTM guest through an iOS guest API. The concrete iOS path
is to create a UTM Linux VM, attach an Ubuntu Server ARM64 installer ISO, boot
and install a glibc-based guest. After Python is available through its
user-owned guest package plan, copy the single standalone `easy-bootstrap.sh`
file into the guest through the UTM/user-approved transfer, then obtain the
fixed checkout with the same state-local bootstrap:

```sh
export AGENT_WELCOME_IOS_GUEST=1
./easy-bootstrap.sh --target ios-codex --state-dir "$HOME/.agent-welcome/bootstrap" \
  --approve-repository-download
# The resulting repository is fixed and verified under the bootstrap state:
PYTHONPATH="$HOME/.agent-welcome/bootstrap/repository" python3 -m agent_welcome easy-start \
  --target ios-codex --state-dir "$HOME/.agent-welcome/bootstrap/easy-state"
# After a user checkpoint, resume the same durable state:
PYTHONPATH="$HOME/.agent-welcome/bootstrap/repository" python3 -m agent_welcome easy-resume \
  --state-dir "$HOME/.agent-welcome/bootstrap/easy-state"
```

The UTM app-owned steps and the bootstrap prerequisite above remain manual
checkpoints; setup resumes only inside the observed UTM guest.

## Login and first work

Login/MFA/authorization input is never persisted and there is no manual JSON
attestation path. After the user completes login outside Agent Welcome, the
user must explicitly pass `--approve-first-task`. The program then runs a
fixed, per-agent adapter with a fresh nonce and requires both exact response
text and a state-local proof file. It never accepts an arbitrary argv, or a
`--help`, `--version`, or no-op command as a first task. It runs with a
120-second timeout, `stdin` closed, and captured stdout. The per-agent commands
have the following deliberately narrow write capability:

- Claude Code uses `-p --tools Write --allowedTools Write --permission-prompts
  none`; it preserves the browser/OAuth or keychain login completed in the
  stated login step. It does not select `--bare` or API-key mode. Unresolved
  permissions fail rather than opening an interactive or broad-permission flow.
- Codex uses `exec --sandbox workspace-write --ask-for-approval never`; it does
  not use any sandbox or approval bypass.
- Prime Agent uses `--print`, so it cannot select its interactive TTY mode.

The prompt confines the write to the current state-local proof workspace. The
Claude adapter exposes only `Write`; Codex relies on its workspace-write
sandbox; and the Prime adapter is only asserted to be noninteractive. A mock
runner is recorded only as fixture evidence, not proof of provider-agent tool
isolation. `SUCCEEDED` additionally requires a direct process observation and a
direct official-installer-to-binary provenance chain; otherwise the terminal
result is `COMPLETED_UNVERIFIED_PROVENANCE`.

## 12-target implementation matrix

| Target | State-machine route | Official installer / remaining user step | Current evidence |
|---|---|---|---|
| macOS × Claude Code | Native macOS | `claude.ai/install.sh`; browser login and state-local proof task | implementation only |
| macOS × Codex | Native macOS | `chatgpt.com/codex/install.sh`; login and state-local proof task | implementation only |
| macOS × Prime Agent | Native macOS | Prime `install.sh`; `/login` and state-local proof task | implementation only |
| Windows × Claude Code | Native Windows | `claude.ai/install.ps1`; browser login and state-local proof task | implementation only |
| Windows × Codex | Native Windows | `chatgpt.com/codex/install.ps1`; login and state-local proof task | implementation only |
| Windows × Prime Agent | Native Windows | Prime `install.ps1`; `/login` and state-local proof task | implementation only |
| Android × Claude Code | Same-device Termux + PRoot Linux userland | prepare and enter guest, then Linux installer; login/task in guest | implementation only |
| Android × Codex | Same-device Termux + PRoot Linux userland | prepare and enter guest, then Linux installer; login/task in guest | implementation only |
| Android × Prime Agent | Same-device Termux + glibc >= 2.35 PRoot guest | prepare guest, Linux installer, `/login`, task | implementation only |
| iOS × Claude Code | Same-device UTM Linux guest | install/open UTM, import/boot guest, Linux installer, login/task | implementation only |
| iOS × Codex | Same-device UTM Linux guest | install/open UTM, import/boot guest, Linux installer, login/task | implementation only |
| iOS × Prime Agent | Same-device UTM glibc >= 2.35 guest | import/boot guest, Linux installer, `/login`, task | implementation only |

For Windows Codex, the adapter uses the canonical
`releases.openai.com/codex/install.ps1` endpoint; the catalog's ChatGPT command
is retained only as the vendor's documented manual-command equivalent.

Android requires a directly observed `TERMUX_VERSION` plus a Linux-userland or
PRoot runtime. iOS requires the same-device Linux guest to run with
`AGENT_WELCOME_IOS_GUEST=1`; that marker is recorded as a user assertion, not as
native iOS support. Android process-killing and UTM SE/JIT constraints are resume
conditions, not success. No remote PC or cloud run is accepted as mobile evidence.

## Official source basis

- [Claude Code setup](https://code.claude.com/docs/en/setup) and [quickstart](https://code.claude.com/docs/en/quickstart)
- [Claude Code CLI reference](https://code.claude.com/docs/en/cli-reference), [headless mode](https://code.claude.com/docs/en/headless), and [official user-local launcher layout report](https://github.com/anthropics/claude-code/issues/101084)
- [Codex CLI quickstart](https://learn.chatgpt.com/docs/codex/cli), [developer commands](https://learn.chatgpt.com/docs/developer-commands), and [Windows installer source](https://releases.openai.com/codex/install.ps1)
- [CPython 3.13.5 release files](https://www.python.org/downloads/release/python-3135/), used only for the state-local Windows embeddable-runtime pin
- [Prime Agent README](https://github.com/PrimeIntellect-ai/prime-agent) and [installer](https://app.primeintellect.ai/prime-agent/install.sh)
- [Termux](https://github.com/termux/termux-app), [PRoot-Distro](https://github.com/termux/proot-distro), and [UTM iOS](https://docs.getutm.app/installation/ios/)

Claude/Codex official documentation does not list Android/iOS native targets.
Prime's Linux release path requires GNU/glibc >= 2.35. Fixture or implementation
success therefore never changes `runtime_verified` for any target.
