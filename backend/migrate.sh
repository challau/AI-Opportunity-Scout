#!/bin/sh
# migrate.sh — Run Alembic migrations before server start
# This runs as the Railway release/start command prefix.

set -e

echo "=== Running Alembic migrations ==="
alembic upgrade head
echo "=== Migrations complete ==="
