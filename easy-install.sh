#!/bin/sh
# Small, non-installing entry point.  It never changes global PATH or invokes
# a vendor installer; all Agent Welcome files stay beneath --state-dir.
set -eu

# Resolve the checked-out module from this script, while keeping the caller's
# current directory as the default state-directory base.
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
export PYTHONPATH="$script_dir${PYTHONPATH:+:$PYTHONPATH}"

if command -v python3 >/dev/null 2>&1; then
  python_cmd=python3
elif command -v python >/dev/null 2>&1; then
  python_cmd=python
else
  echo "Python 3.11+ is required. Install it using your OS package source, then rerun this script." >&2
  exit 2
fi

state_dir=${AGENT_WELCOME_STATE_DIR:-"$PWD/.agent-welcome/easy"}
exec "$python_cmd" -m agent_welcome easy-start --state-dir "$state_dir" "$@"
