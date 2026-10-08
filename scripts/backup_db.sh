#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="$PROJECT_DIR/backups"
RETENTION_DAYS=183
DB_SERVICE="db"
DB_NAME="bipagen"

cd "$PROJECT_DIR"
mkdir -p "$BACKUP_DIR"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    . "$PROJECT_DIR/.env"
    set +a
fi
ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD:-bipagen_root_pass}"

DB_CONTAINER_ID="$(docker compose ps -q "$DB_SERVICE" 2>/dev/null || true)"
if [ -z "$DB_CONTAINER_ID" ]; then
    echo "ERROR: container for service '$DB_SERVICE' is not running." >&2
    exit 1
fi

STAMP="$(date +%Y-%m-%d)"
TARGET="$BACKUP_DIR/bipagen_$STAMP.sql.gz"
TMP="$TARGET.tmp"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting backup of '$DB_NAME' -> $TARGET"

docker exec -i -e MYSQL_PWD="$ROOT_PASSWORD" "$DB_CONTAINER_ID" \
    mysqldump -uroot --single-transaction --quick --routines --triggers "$DB_NAME" \
    | gzip -c > "$TMP"

mv "$TMP" "$TARGET"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup written: $TARGET ($(du -h "$TARGET" | cut -f1))"

PRUNED="$(find "$BACKUP_DIR" -maxdepth 1 -name 'bipagen_*.sql.gz' -mtime +"$RETENTION_DAYS" -print -delete)"
if [ -n "$PRUNED" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Pruned backups older than $RETENTION_DAYS days:"
    echo "$PRUNED"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup finished."
