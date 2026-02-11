#!/bin/bash
# Run SQL migrations in order. Requires psql or Docker postgres.
# Usage:
#   With local psql: PGHOST=localhost PGUSER=api PGPASSWORD=api PGDATABASE=api ./run_migrations.sh
#   With Docker:    docker exec -i db psql -U api -d api < migrations/000_base.sql

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PGHOST=${PGHOST:-localhost}
PGPORT=${PGPORT:-5432}
PGUSER=${PGUSER:-api}
PGPASSWORD=${PGPASSWORD:-api}
PGDATABASE=${PGDATABASE:-api}
export PGPASSWORD

for f in migrations/000_base.sql migrations/001_device_events.sql; do
  [ -f "$f" ] || continue
  echo "Running $f ..."
  psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -f "$f" || true
done

echo "Migrations done."
