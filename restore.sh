#!/bin/bash
set -e

if [ -z "$1" ]; then
  echo "Usage: ./restore.sh <backup_file.sql>"
  exit 1
fi

if [ ! -f "$1" ]; then
  echo "❌ File $1 does not exist!"
  exit 1
fi

echo "Restoring MySQL database from $1..."
cat "$1" | docker compose exec -T mysql mysql -u autojobapply -pautojobapply autojobapply
echo "✅ Restore completed successfully."
