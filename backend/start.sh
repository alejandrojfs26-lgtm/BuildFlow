#!/usr/bin/env bash
set -e

echo "=== BuildFlow Startup ==="

echo "→ Applying Alembic migrations..."
alembic upgrade head

echo "→ Starting uvicorn on 0.0.0.0:${PORT:-8000}"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers "${UVICORN_WORKERS:-2}"
