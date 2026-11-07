# One-time setup: lets phones on your HOME Wi-Fi (Private network) open local dev pages from this PC.
# Run once: right-click this file > "Run with PowerShell" (it asks for admin). Public Wi-Fi stays blocked.
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
  Start-Process powershell -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
  exit
}
$name = "Claude dev pages for phone (home Wi-Fi only)"
Get-NetFirewallRule -DisplayName $name -ErrorAction SilentlyContinue | Remove-NetFirewallRule
New-NetFirewallRule -DisplayName $name -Direction Inbound -Protocol TCP -LocalPort "3000-5999", "8000-8999" -Action Allow -Profile Private | Out-Null
Write-Host "Done. Ports 3000-5999 and 8000-8999 are open to devices on your home (Private) Wi-Fi only." -ForegroundColor Green
Read-Host "Press Enter to close"
