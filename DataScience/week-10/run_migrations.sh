#!/bin/bash
# Run SQL migrations in order. Uses Docker postgres if psql not found.
# Usage:
#   With Docker (default): docker compose up -d postgres && ./run_migrations.sh
#   With local psql: PGHOST=localhost PGUSER=api PGPASSWORD=api PGDATABASE=api ./run_migrations.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PGHOST=${PGHOST:-localhost}
PGPORT=${PGPORT:-5432}
PGUSER=${PGUSER:-api}
PGPASSWORD=${PGPASSWORD:-api}
PGDATABASE=${PGDATABASE:-api}
CONTAINER=${PG_CONTAINER:-db}
export PGPASSWORD

run_migration() {
  local f="$1"
  if command -v psql >/dev/null 2>&1; then
    psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -f "$f" || true
  elif docker exec "$CONTAINER" psql --version >/dev/null 2>&1; then
    docker exec -i "$CONTAINER" psql -U "$PGUSER" -d "$PGDATABASE" -f - < "$f" || true
  else
    echo "Neither psql nor Docker container '$CONTAINER' available. Run: docker compose up -d postgres"
    exit 1
  fi
}

for f in migrations/000_base.sql migrations/001_device_events.sql migrations/002_drop_event_tables.sql; do
  [ -f "$f" ] || continue
  echo "Running $f ..."
  run_migration "$f"
done

echo "Migrations done."
