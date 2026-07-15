# Bootstrap local development environment (scaffold)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path ".env")) {
  Copy-Item "config\.env.example" ".env"
  Write-Host "Created .env from config/.env.example â€” fill in secrets before starting services."
}

Write-Host "Scaffold bootstrap complete."
Write-Host "Next: .\scripts\start-stack.ps1  (forces legacy builder; needed on Windows/OneDrive)"
