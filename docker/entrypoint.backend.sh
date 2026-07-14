#!/bin/sh
set -e
cd /app/backend
echo "Running Alembic migrations..."
alembic upgrade head
if [ "${SEED_DEMO:-false}" = "true" ]; then
  echo "Seeding demo data..."
  python /app/scripts/seed_demo.py || true
fi
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
