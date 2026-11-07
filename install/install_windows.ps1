# Make this workflow yours (Windows). Right-click > Run with PowerShell, or: powershell -ExecutionPolicy Bypass -File install\install_windows.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
foreach ($tool in @("git", "python")) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        Write-Host "Please install $tool first (git: https://git-scm.com, Python 3.10+: https://www.python.org), then run this again."
        exit 1
    }
}
if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
    Write-Host "Note: Claude Code was not found. Install it from https://claude.com/claude-code (the workflow still installs)."
}
# Windows links need Developer Mode or an admin shell for file symlinks; folder links (junctions) always work.
python "$root\install\setup_me.py"
