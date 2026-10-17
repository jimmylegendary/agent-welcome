#!/bin/sh
# Standalone, state-local bootstrap.  It deliberately avoids global PATH or
# package-manager writes; users without Python receive a concrete, consented
# package-manager plan instead.  The repository archive itself is pinned by
# revision and SHA-256 before extraction.
set -eu

revision=ceb6d3803b12d41d429dc3188e9a20ac8f220780
archive_url="https://codeload.github.com/jimmylegendary/agent-welcome/zip/$revision"
archive_sha256=38d359aa0b05ae6bed5214a1b845e67477332c17cc291fc1727969aff648891d
archive_prefix="agent-welcome-$revision"
state_dir="$PWD/.agent-welcome/bootstrap"
target=
approve_repository=false
approve_runtime_plan=false
start_easy_install=false

usage() {
  cat <<'EOF'
Usage: easy-bootstrap.sh --target TARGET [--state-dir DIR]
       [--approve-repository-download] [--approve-runtime-plan]
       [--start-easy-install]

The repository download is pinned and only writes under DIR.  A missing Unix
Python 3.11+ runtime produces a supported package-manager plan; this script
never invokes that global package manager itself.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --target) target=${2:?--target needs a value}; shift 2 ;;
    --state-dir) state_dir=${2:?--state-dir needs a value}; shift 2 ;;
    --approve-repository-download) approve_repository=true; shift ;;
    --approve-runtime-plan) approve_runtime_plan=true; shift ;;
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
  if command -v curl >/dev/null 2>&1; then
    curl --fail --location --retry 2 --output "$archive" "$archive_url"
  elif command -v wget >/dev/null 2>&1; then
    wget --output-document="$archive" "$archive_url"
  else
    echo 'curl or wget is required to download the pinned repository archive' >&2
    return 2
  fi
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

python_cmd=
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then
    python_cmd=$(command -v "$candidate")
    break
  fi
done

runtime_status=existing
if [ -z "$python_cmd" ]; then
  runtime_status=missing
  package_plan=
  if command -v apt-get >/dev/null 2>&1; then package_plan='sudo apt-get install -y python3'; fi
  if command -v dnf >/dev/null 2>&1; then package_plan='sudo dnf install -y python3'; fi
  if command -v pacman >/dev/null 2>&1; then package_plan='sudo pacman -S --needed python'; fi
  if command -v apk >/dev/null 2>&1; then package_plan='sudo apk add python3'; fi
  [ -n "$package_plan" ] || package_plan='No supported package manager was observed; provide Python 3.11+ manually.'
  if [ "$approve_runtime_plan" = true ]; then
    echo "Runtime plan acknowledged: $package_plan" >&2
  else
    echo "Python 3.11+ is required. Planned user-owned command: $package_plan" >&2
  fi
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

if [ "$runtime_status" = missing ] || [ "$repository_status" = waiting_repository_consent ]; then
  write_state WAITING_USER "$runtime_status" "$repository_status"
  exit 0
fi

write_state READY "$runtime_status" "$repository_status"
next="PYTHONPATH='$repository' '$python_cmd' -m agent_welcome easy-start --target '$target' --state-dir '$state_dir/easy-state'"
printf '{"status":"READY","repository":"%s","next_command":"%s"}\n' "$repository" "$next"
if [ "$start_easy_install" = true ]; then
  PYTHONPATH="$repository${PYTHONPATH:+:$PYTHONPATH}" exec "$python_cmd" -m agent_welcome easy-start --target "$target" --state-dir "$state_dir/easy-state"
fi
