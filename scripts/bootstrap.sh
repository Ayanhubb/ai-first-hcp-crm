#!/usr/bin/env bash
# Bootstrap local development environment (scaffold)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  cp config/.env.example .env
  echo "Created .env from config/.env.example — fill in secrets before starting services."
fi

echo "Scaffold bootstrap complete."
echo "Next: docker compose -f docker/docker-compose.yml --env-file .env up --build"
