#!/usr/bin/env bash
# install.sh <owner/repo> <path-to-skill-folder-in-repo | .> [local-name]
# Downloads ONE skill folder from GitHub into ~/.claude/skills/<name>.
set -euo pipefail
repo="$1"; sub="${2:-.}"; name="${3:-}"
dest_root="$HOME/.claude/skills"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT

git clone -q --depth 1 --filter=blob:none --sparse "https://github.com/$repo.git" "$tmp/r"
if [ "$sub" != "." ]; then git -C "$tmp/r" sparse-checkout set "$sub" >/dev/null; fi
src="$tmp/r/$sub"
[ -f "$src/SKILL.md" ] || { echo "ERROR: no SKILL.md at $repo/$sub"; exit 2; }

[ -n "$name" ] || name="$(sed -n 's/^name:[[:space:]]*//p' "$src/SKILL.md" | head -1 | tr -d '"'\''\r')"
[ -n "$name" ] || name="$(basename "$sub")"
if [ -e "$dest_root/$name" ]; then echo "SKIP: $name already installed"; exit 0; fi

rm -rf "$src/.git"
cp -r "$src" "$dest_root/$name"
sha="$(git -C "$tmp/r" rev-parse --short HEAD)"
echo "$(date +%F) $name <- github.com/$repo/$sub @ $sha" >> "$dest_root/.installed-from-github.log"

echo "INSTALLED: $name  ($repo/$sub @ $sha)"
echo "Files:"; (cd "$dest_root/$name" && find . -type f | head -40)
scripts="$(cd "$dest_root/$name" && find . -type f \( -name '*.sh' -o -name '*.ps1' -o -name '*.py' -o -name '*.js' -o -name '*.ts' -o -name '*.bat' \) | head -20)"
[ -z "$scripts" ] || { echo "NOTE: contains scripts (not run):"; echo "$scripts"; }
