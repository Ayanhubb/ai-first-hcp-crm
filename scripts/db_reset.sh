#!/usr/bin/env bash
# Reset local Postgres volume (destructive — scaffold helper)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

docker compose -f docker/docker-compose.yml --env-file .env down -v
echo "Volumes removed. Rebuild with: docker compose -f docker/docker-compose.yml --env-file .env up --build"
