#!/bin/sh
# Standalone bootstrap. Repository artifacts always stay beneath --state-dir.
# A global runtime is changed only after the separate, explicit
# --approve-runtime-install consent flag; no package manager is installed here.
set -eu

revision=ceb6d3803b12d41d429dc3188e9a20ac8f220780
archive_url="https://codeload.github.com/jimmylegendary/agent-welcome/zip/$revision"
archive_sha256=38d359aa0b05ae6bed5214a1b845e67477332c17cc291fc1727969aff648891d
archive_prefix="agent-welcome-$revision"
macos_version=3.13.5
macos_archive_url="https://www.python.org/ftp/python/3.13.5/python-3.13.5-macos11.pkg"
# This is the signed artifact's SHA2-256 value from its official CPython
# Sigstore bundle, not an unverified third-party checksum.
macos_archive_sha256=e754d6cae3f2810dd1818c1395a7ff50ce79ade3ec4887f7ce23ad581cc12e3a
state_dir="$PWD/.agent-welcome/bootstrap"
target=
approve_repository=false
approve_runtime_install=false
start_easy_install=false

usage() {
  cat <<'EOF'
Usage: easy-bootstrap.sh --target TARGET [--state-dir DIR]
       [--approve-repository-download] [--approve-runtime-install]
       [--start-easy-install]

The repository download is pinned and only writes under DIR. If Python 3.11+
is absent, the script prints the exact supported runtime command. It runs that
command only with --approve-runtime-install and rechecks the installed runtime.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --target) target=${2:?--target needs a value}; shift 2 ;;
    --state-dir) state_dir=${2:?--state-dir needs a value}; shift 2 ;;
    --approve-repository-download) approve_repository=true; shift ;;
    --approve-runtime-install) approve_runtime_install=true; shift ;;
    --start-easy-install) start_easy_install=true; shift ;;
    --help|-h) usage; exit 0 ;;
    *) echo "unknown bootstrap argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

[ -n "$target" ] || { echo '--target is required' >&2; exit 2; }

mkdir -p "$state_dir"
state_dir=$(CDPATH= cd -- "$state_dir" && pwd)
repository="$state_dir/repository"
marker="$repository/.agent-welcome-bootstrap.json"

sha256_file() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}'; return; fi
  if command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | awk '{print $1}'; return; fi
  echo 'a SHA-256 utility (sha256sum or shasum) is required' >&2
  return 127
}

write_state() {
  status=$1
  runtime=$2
  repository_status=$3
  temporary="$state_dir/.bootstrap-state-$$.tmp"
  printf '{"status":"%s","runtime":"%s","repository":"%s","revision":"%s"}\n' \
    "$status" "$runtime" "$repository_status" "$revision" > "$temporary"
  mv -f "$temporary" "$state_dir/bootstrap-state.json"
}

repository_ready() {
  [ -d "$repository" ] && [ -f "$marker" ] && \
    grep -F "\"revision\":\"$revision\"" "$marker" >/dev/null 2>&1 && \
    grep -F "\"archive_sha256\":\"$archive_sha256\"" "$marker" >/dev/null 2>&1
}

fetch_file() {
  url=$1
  destination=$2
  if command -v curl >/dev/null 2>&1; then
    curl --fail --location --retry 2 --output "$destination" "$url"
  elif command -v wget >/dev/null 2>&1; then
    wget --output-document="$destination" "$url"
  else
    echo 'curl or wget is required to download the pinned artifact' >&2
    return 127
  fi
}

probe_python() {
  candidate=$1
  if "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then
    python_cmd=$candidate
    return 0
  fi
  return 1
}

find_python() {
  python_cmd=
  for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 && probe_python "$candidate"; then return 0; fi
  done
  return 1
}

find_brew_python() {
  brew_prefix=$(brew --prefix python@3.13 2>/dev/null || true)
  for candidate in "$brew_prefix/bin/python3" "$brew_prefix/bin/python3.13"; do
    [ -n "$brew_prefix" ] && [ -x "$candidate" ] && probe_python "$candidate" && return 0
  done
  find_python
}

find_macos_installer_python() {
  for candidate in /usr/local/bin/python3 /Library/Frameworks/Python.framework/Versions/3.13/bin/python3; do
    [ -x "$candidate" ] && probe_python "$candidate" && return 0
  done
  find_python
}

run_with_privilege() {
  if [ "$(id -u)" = 0 ]; then "$@"; return; fi
  if command -v sudo >/dev/null 2>&1; then sudo "$@"; return; fi
  echo 'administrator approval is required but sudo is unavailable' >&2
  return 127
}

select_runtime_plan() {
  runtime_action=blocked
  runtime_plan=
  os_name=$(uname -s)
  if [ "$os_name" = Darwin ]; then
    machine=$(uname -m)
    case "$machine" in
      arm64|x86_64) ;;
      *) runtime_plan="unsupported macOS architecture: $machine"; return ;;
    esac
    if command -v brew >/dev/null 2>&1; then
      runtime_action=brew
      runtime_plan='brew install python@3.13'
    else
      runtime_action=macos_pkg
      runtime_plan="download verified CPython $macos_version universal2 package, then request macOS administrator approval through installer"
    fi
    return
  fi
  if [ -n "${TERMUX_VERSION:-}" ] && command -v pkg >/dev/null 2>&1; then
    runtime_action=termux
    runtime_plan='pkg install -y python curl unzip'
  elif command -v apt-get >/dev/null 2>&1; then
    runtime_action=apt
    runtime_plan='sudo apt-get install -y python3 curl unzip'
  elif command -v dnf >/dev/null 2>&1; then
    runtime_action=dnf
    runtime_plan='sudo dnf install -y python3 curl unzip'
  elif command -v pacman >/dev/null 2>&1; then
    runtime_action=pacman
    runtime_plan='sudo pacman -S --needed python curl unzip'
  elif command -v apk >/dev/null 2>&1; then
    runtime_action=apk
    runtime_plan='sudo apk add python3 curl unzip'
  else
    runtime_plan="unsupported runtime route: $(uname -s) has no supported package manager (apt-get, dnf, pacman, apk, or Termux pkg)"
  fi
}

install_macos_package() {
  runtime_downloads="$state_dir/runtime-downloads"
  package="$runtime_downloads/python-$macos_version-macos11.pkg"
  mkdir -p "$runtime_downloads"
  if [ -f "$package" ]; then
    actual=$(sha256_file "$package")
    [ "$actual" = "$macos_archive_sha256" ] || { echo 'saved macOS Python package SHA-256 did not match the pinned official artifact' >&2; return 2; }
  else
    temporary="$runtime_downloads/.python-$macos_version-$$.pkg"
    trap 'rm -f "$temporary"' EXIT HUP INT TERM
    fetch_file "$macos_archive_url" "$temporary"
    actual=$(sha256_file "$temporary")
    [ "$actual" = "$macos_archive_sha256" ] || { echo 'macOS Python package SHA-256 did not match the pinned official artifact' >&2; return 2; }
    mv "$temporary" "$package"
    trap - EXIT HUP INT TERM
  fi
  command -v pkgutil >/dev/null 2>&1 || { echo 'macOS pkgutil is required to check the official Python package signature' >&2; return 127; }
  command -v installer >/dev/null 2>&1 || { echo 'macOS installer is required to request OS-approved installation' >&2; return 127; }
  pkgutil --check-signature "$package"
  # macOS presents the administrator/OS approval boundary here. There is no
  # privilege bypass and this only follows --approve-runtime-install.
  run_with_privilege installer -pkg "$package" -target /
}

install_runtime() {
  case "$runtime_action" in
    termux) pkg install -y python curl unzip ;;
    apt) run_with_privilege apt-get install -y python3 curl unzip ;;
    dnf) run_with_privilege dnf install -y python3 curl unzip ;;
    pacman) run_with_privilege pacman -S --needed python curl unzip ;;
    apk) run_with_privilege apk add python3 curl unzip ;;
    brew) brew install python@3.13 ;;
    macos_pkg) install_macos_package ;;
    *) echo "$runtime_plan" >&2; return 2 ;;
  esac
}

download_repository() {
  [ "$approve_repository" = true ] || return 1
  [ ! -L "$repository" ] || { echo 'bootstrap repository path must not be a symbolic link' >&2; return 2; }
  if [ -e "$repository" ]; then
    echo 'existing repository directory is not this pinned bootstrap; preserving it' >&2
    return 2
  fi
  command -v unzip >/dev/null 2>&1 || { echo 'unzip is required to prepare the pinned repository archive' >&2; return 2; }
  stage=$(mktemp -d "$state_dir/.bootstrap-stage.XXXXXX")
  cleanup() { rm -rf "$stage"; }
  trap cleanup EXIT HUP INT TERM
  archive="$stage/repository.zip"
  fetch_file "$archive_url" "$archive"
  actual=$(sha256_file "$archive")
  [ "$actual" = "$archive_sha256" ] || { echo 'repository archive SHA-256 did not match pinned revision' >&2; return 2; }
  # Reject traversal, absolute, backslash, and unexpected-root entries before
  # moving any extracted content into the durable repository directory.
  members_file="$stage/members.txt"
  unzip -Z1 "$archive" > "$members_file"
  while IFS= read -r member; do
    case "$member" in
      "$archive_prefix/"|"$archive_prefix/"*) ;;
      *) echo "archive member outside pinned root: $member" >&2; return 2 ;;
    esac
    relative=${member#"$archive_prefix/"}
    case "$member" in /*|*'\'*|*'//'*) echo "unsafe archive member: $member" >&2; return 2 ;; esac
    case "/$relative/" in *'/../'*|*/'./'*) echo "unsafe archive member: $member" >&2; return 2 ;; esac
  done < "$members_file"
  extracted="$stage/extracted"
  mkdir "$extracted"
  unzip -q "$archive" -d "$extracted"
  [ -z "$(find "$extracted" -type l -print -quit)" ] || { echo 'archive symbolic links are not allowed' >&2; return 2; }
  payload="$extracted/$archive_prefix"
  [ -d "$payload" ] || { echo 'repository archive is missing pinned root' >&2; return 2; }
  printf '{"revision":"%s","archive_sha256":"%s"}\n' "$revision" "$archive_sha256" > "$payload/.agent-welcome-bootstrap.json"
  mv "$payload" "$repository"
  trap - EXIT HUP INT TERM
  cleanup
  return 0
}

if find_python; then
  runtime_status=existing
else
  runtime_status=missing
  select_runtime_plan
  if [ "$runtime_action" = blocked ]; then
    echo "Python 3.11+ is required. $runtime_plan" >&2
    write_state BLOCKED unsupported_runtime not_attempted
    exit 2
  fi
  if [ "$approve_runtime_install" = false ]; then
    echo "Python 3.11+ is required. Planned approved command: $runtime_plan" >&2
    echo 'Re-run with --approve-runtime-install to run exactly this runtime operation.' >&2
    write_state WAITING_USER waiting_runtime_consent not_attempted
    exit 0
  fi
  install_runtime
  case "$runtime_action" in
    brew) find_brew_python || true ;;
    macos_pkg) find_macos_installer_python || true ;;
    *) find_python || true ;;
  esac
  if [ -z "${python_cmd:-}" ]; then
    echo 'approved runtime operation completed, but Python 3.11+ was not found on this shell path' >&2
    write_state FAILED runtime_recheck_failed not_attempted
    exit 2
  fi
  runtime_status="installed_$runtime_action"
fi

if repository_ready; then
  repository_status=reused
elif download_repository; then
  repository_status=prepared
elif [ "$approve_repository" = false ]; then
  repository_status=waiting_repository_consent
  echo "Pinned repository plan: $archive_url (SHA-256 $archive_sha256). Re-run with --approve-repository-download." >&2
else
  exit 2
fi

if [ "$repository_status" = waiting_repository_consent ]; then
  write_state WAITING_USER "$runtime_status" "$repository_status"
  exit 0
fi

write_state READY "$runtime_status" "$repository_status"
next="PYTHONPATH='$repository' '$python_cmd' -m agent_welcome easy-start --target '$target' --state-dir '$state_dir/easy-state'"
printf '{"status":"READY","repository":"%s","next_command":"%s"}\n' "$repository" "$next"
if [ "$start_easy_install" = true ]; then
  PYTHONPATH="$repository${PYTHONPATH:+:$PYTHONPATH}" exec "$python_cmd" -m agent_welcome easy-start --target "$target" --state-dir "$state_dir/easy-state"
fi
