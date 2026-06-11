#!/usr/bin/env sh
set -e

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting API process..."
exec "$@"
