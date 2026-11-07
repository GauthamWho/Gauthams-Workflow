#!/bin/bash
# One-time Mac setup of this workflow. Safe to re-run; never deletes your files.
#   bash <repo>/_workflow/setup_mac.sh
set -e
# workspace = GW_HOME, else the clone this script is in (any folder)
HERE="$(cd "$(dirname "$0")/.." 2>/dev/null && pwd)"
if [ -n "$GW_HOME" ]; then GW="$GW_HOME"; else GW="$HERE"; fi
say() { printf "\n\033[1m== %s\033[0m\n" "$1"; }
gw() { if [ -f "$GW/_workflow/gw.py" ]; then python3 "$GW/_workflow/gw.py" "$@"; else echo "  (skipped: _workflow/gw.py not in this repo)"; fi; }

say "1/7 Homebrew tools"
command -v brew >/dev/null || { echo "Install Homebrew first (https://brew.sh), then re-run."; exit 1; }
brew install git gh python python@3.13 node >/dev/null || true
gh auth status >/dev/null 2>&1 || gh auth login --web

say "2/7 Workspace ($GW)"
cd "$GW" && git pull --ff-only -q || true
grep -q GW_HOME "$HOME/.zshrc" 2>/dev/null || echo "export GW_HOME=\"$GW\"" >> "$HOME/.zshrc"
export GW_HOME="$GW"

say "3/7 Python tools (.venv-gw on Python 3.13: every package has a ready-made Mac build)"
if [ -f "$GW/_workflow/requirements-gw.txt" ]; then
  PY313="$(brew --prefix python@3.13)/bin/python3.13"
  [ -x "$PY313" ] || PY313="$(command -v python3.13 || command -v python3)"
  # a venv made by an earlier, failed run with another Python is replaced (it only holds installed packages)
  if [ -x "$GW/.venv-gw/bin/python" ] && ! "$GW/.venv-gw/bin/python" -c "import sys; assert sys.version_info[:2] == (3, 13)" 2>/dev/null; then
    mv "$GW/.venv-gw" "$GW/.venv-gw.old-$(date +%s)"
  fi
  "$PY313" -m venv "$GW/.venv-gw"
  "$GW/.venv-gw/bin/pip" install -q --upgrade pip
  "$GW/.venv-gw/bin/pip" install -q --prefer-binary -r "$GW/_workflow/requirements-gw.txt"
else
  echo "  (no _workflow/requirements-gw.txt: nothing to install)"
fi

say "4/7 Links: skills, profile, memory (one copy, inside the repo)"
gw link

say "5/7 Installer-managed skills"
gw install-agent-skills

say "6/7 Settings, auto-sync hooks, commit guard"
gw settings
git -C "$GW" config core.hooksPath _workflow/hooks && chmod +x "$GW/_workflow/hooks/pre-commit"

say "7/7 Health check"
gw doctor || true

if [ -f "$GW/_workflow/secrets.vault" ]; then
  read -r -p "  Restore secrets from the vault? y/n " a; [ "$a" = y ] && python3 "$GW/_workflow/vault.py" unlock --env --files
fi

echo
echo "Done. Workspace: $GW"
echo "Every Claude session pulls at start and pushes at the end, automatically."
