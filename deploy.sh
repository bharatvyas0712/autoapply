#!/bin/bash
set -e

echo "======================================"
echo "🚀 Deploying AutoJobApply in Production"
echo "======================================"

# Ensure scripts are executable
chmod +x healthcheck.sh backup.sh restore.sh || true

echo "[1/4] Building Docker images..."
docker compose build --no-cache

echo "[2/4] Starting containers..."
docker compose up -d

echo "[3/4] Ensuring Playwright Chromium is installed..."
docker compose exec -T automation bash -c "playwright install chromium" || echo "Chromium installation output above."

echo "[4/4] Running health checks..."
sleep 5
./healthcheck.sh

echo "======================================"
echo "✅ Deployment Successful!"
echo "Server should be accessible at: http://$(hostname -I | awk '{print $1}')"
echo "Ensure Azure NSG (Firewall) allows Port 80 and Port 443 inbound."
echo "======================================"
