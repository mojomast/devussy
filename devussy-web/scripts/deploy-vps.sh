#!/usr/bin/env bash
set -euo pipefail

# Deploy app on a VPS using docker-compose
# Usage: ./deploy-vps.sh [--restart]

RESTART=false
if [[ ${1:-} == "--restart" ]]; then
  RESTART=true
fi

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

echo "Building and starting services (docker-compose)..."

docker compose pull || true
docker compose build --pull
docker compose up -d --remove-orphans

if $RESTART; then
  docker compose restart
fi

echo "Deployment complete. Logs follow (tail 80 lines):"
docker compose logs --tail=80 --follow
