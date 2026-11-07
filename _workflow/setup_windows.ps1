# One-time setup of this workflow on a Windows PC (a new PC, or to repair this one). Safe to re-run.
#   powershell -ExecutionPolicy Bypass -File <repo>\_workflow\setup_windows.ps1
# Needs: Git, GitHub CLI (gh), Python 3, Node (winget installs them if missing). Developer Mode ON (for file links).
# The repo is the folder this script sits in (its parent), wherever you cloned it; GW_HOME overrides that.
param([string]$GW = $(if ($env:GW_HOME) { $env:GW_HOME } else { (Resolve-Path (Join-Path $PSScriptRoot "..")).Path }))
$ErrorActionPreference = "Continue"
function Say($t) { Write-Host "`n== $t" -ForegroundColor Cyan }
$GWPY = "$GW\_workflow\gw.py"
function Gw($cmd) { if (Test-Path $GWPY) { python $GWPY $cmd } else { Write-Host "  (skipped: _workflow\gw.py not in this repo)" } }

Say "1/7 Tools"
foreach ($p in @(@("git", "Git.Git"), @("gh", "GitHub.cli"), @("python", "Python.Python.3.14"), @("node", "OpenJS.NodeJS"))) {
  if (-not (Get-Command $p[0] -ErrorAction SilentlyContinue)) { winget install --silent --accept-source-agreements --accept-package-agreements -e --id $p[1] }
}
gh auth status 2>$null; if ($LASTEXITCODE -ne 0) { gh auth login --web }

Say "2/7 Workspace ($GW)"
git -C $GW pull --ff-only -q
[Environment]::SetEnvironmentVariable("GW_HOME", $GW, "User"); $env:GW_HOME = $GW

Say "3/7 Python tools (pinned)"
if (Test-Path "$GW\_workflow\requirements-gw.txt") {
  python -m venv "$GW\.venv-gw"; & "$GW\.venv-gw\Scripts\python.exe" -m pip install -q -r "$GW\_workflow\requirements-gw.txt"
} else { Write-Host "  (no _workflow\requirements-gw.txt: nothing to install)" }

Say "4/7 Links: skills, profile, memory"
Gw "link"
Say "5/7 Installer-managed skills"
Gw "install-agent-skills"
Say "6/7 Settings, auto-sync hooks, commit guard"
Gw "settings"
git -C $GW config core.hooksPath _workflow/hooks
Say "7/7 Health check"
Gw "doctor"

if (Test-Path "$GW\_workflow\secrets.vault") {
  if ((Read-Host "  Restore secrets from the vault? y/n") -eq "y") { python "$GW\_workflow\vault.py" unlock --env --files }
}
Write-Host "`nDone. Every Claude session pulls at start and pushes at the end, automatically." -ForegroundColor Green
