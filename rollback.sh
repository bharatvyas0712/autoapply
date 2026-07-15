#!/bin/bash
set -e

echo "======================================"
echo "⏪ Rolling Back AutoJobApply Deployment"
echo "======================================"

echo "WARNING: This will discard any uncommitted local changes and revert your git repository to the previous commit (HEAD~1)."
read -p "Are you sure you want to proceed? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Rollback cancelled."
    exit 1
fi

echo "[1/4] Reverting git repository to previous commit..."
git reset --hard HEAD~1

echo "[2/4] Rebuilding Docker images with previous code..."
docker compose build --no-cache

echo "[3/4] Restarting containers..."
docker compose up -d

echo "[4/4] Ensuring Playwright Chromium is installed (if needed)..."
docker compose exec -T automation bash -c "playwright install chromium" || echo "Chromium installation output above."

echo "======================================"
echo "✅ Rollback Successful!"
echo "Please run ./healthcheck.sh to verify that all endpoints are healthy."
echo "If you need to restore your database to an older state, use ./restore.sh <backup_file.sql>"
echo "======================================"
