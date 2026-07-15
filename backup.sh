#!/bin/bash
set -e

mkdir -p backups
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="backups/db_backup_$TIMESTAMP.sql"

echo "Backing up MySQL database..."
docker compose exec -T mysql mysqldump -u autojobapply -pautojobapply autojobapply > $BACKUP_FILE

echo "✅ Backup successfully saved to $BACKUP_FILE"
