#!/bin/bash
set -e

check_container_health() {
    CONTAINER=$1
    # Check if container exists
    if ! docker ps -a --format '{{.Names}}' | grep -Eq "^${CONTAINER}\$"; then
        echo "❌ $CONTAINER does not exist"
        return
    fi
    
    STATUS=$(docker inspect --format="{{if .State.Health}}{{.State.Health.Status}}{{else}}Running (No Healthcheck){{end}}" $CONTAINER)
    
    # If it's not a healthcheck, check if it's running
    if [ "$STATUS" == "Running (No Healthcheck)" ]; then
        STATE=$(docker inspect --format="{{.State.Status}}" $CONTAINER)
        if [ "$STATE" == "running" ]; then
            echo "✅ $CONTAINER is running"
        else
            echo "❌ $CONTAINER is not running ($STATE)"
        fi
    elif [ "$STATUS" == "healthy" ]; then
        echo "✅ $CONTAINER is healthy"
    else
        echo "❌ $CONTAINER health check failed ($STATUS)"
    fi
}

echo "=== Container Health Checks ==="
check_container_health autojobapply_mysql
check_container_health autojobapply_backend
check_container_health autojobapply_automation
check_container_health autojobapply_nginx

echo ""
echo "=== Endpoint Verification ==="
curl -s -f http://localhost/ > /dev/null && echo "✅ Frontend (/)" || echo "❌ Frontend (/) - Did not return 200 OK"
curl -s -f http://localhost/api/health > /dev/null && echo "✅ Backend (/api/health)" || echo "❌ Backend (/api/health) - Did not return 200 OK"
curl -s -X POST http://localhost/api/auth/login > /dev/null && echo "✅ Login Endpoint Responding" || echo "❌ Login Endpoint Failed"
curl -s -f http://localhost/automation/health > /dev/null && echo "✅ Automation (/automation/health)" || echo "❌ Automation (/automation/health) - Did not return 200 OK"

echo ""
echo "Health checks completed."
