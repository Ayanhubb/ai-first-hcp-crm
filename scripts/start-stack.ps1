# Start the local Docker stack. On Windows/OneDrive, BuildKit often fails to
# read Dockerfiles ("invalid file request Dockerfile.*"); force the legacy builder.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$env:DOCKER_BUILDKIT = "0"
$env:COMPOSE_DOCKER_CLI_BUILD = "0"
$env:COMPOSE_BAKE = "false"

Write-Host "Starting stack with legacy Docker builder (DOCKER_BUILDKIT=0)..."
docker compose -f docker/docker-compose.yml --env-file .env up --build -d
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
docker compose -f docker/docker-compose.yml --env-file .env ps
Write-Host "Backend health: http://localhost:8000/health/live"
Write-Host "Frontend:       http://localhost/"
