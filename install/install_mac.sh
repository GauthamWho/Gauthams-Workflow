#!/bin/sh
# Make this workflow yours (Mac / Linux):  sh install/install_mac.sh
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
for tool in git python3; do
  command -v "$tool" >/dev/null 2>&1 || { echo "Please install $tool first (Mac: xcode-select --install), then run this again."; exit 1; }
done
command -v claude >/dev/null 2>&1 || echo "Note: Claude Code was not found. Install it from https://claude.com/claude-code (the workflow still installs)."
python3 "$ROOT/install/setup_me.py"
