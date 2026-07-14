# Reset local Postgres volume (destructive — scaffold helper)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

docker compose -f docker/docker-compose.yml --env-file .env down -v
Write-Host "Volumes removed. Rebuild with: docker compose -f docker/docker-compose.yml --env-file .env up --build"
