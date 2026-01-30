#!/usr/bin/env bash
# Run this ON YOUR PRODUCTION SERVER (e.g. droplet 157.245.6.217) to deploy live.
# Prereqs: git, Docker, docker compose v2. Repo cloned at REPO_DIR.
#
# Usage:
#   REPO_DIR=/path/to/fusonems-quantum-v2 ./scripts/deploy_live.sh
#   SKIP_PULL=1 ./scripts/deploy_live.sh   # skip git pull (e.g. already pulled)
#   NO_NGINX=1 ./scripts/deploy_live.sh    # skip nginx reload
#
set -e
REPO_DIR="${REPO_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$REPO_DIR"

echo "=== Deploying live from $REPO_DIR ==="

if [ -z "$SKIP_PULL" ]; then
  echo "Pulling latest..."
  git pull --rebase
fi

echo "Building and starting stack (backend + frontend + db + redis)..."
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  docker compose up -d --build
else
  docker-compose up -d --build
fi

echo "Waiting for backend to be up..."
for i in 1 2 3 4 5 6 7 8 9 10; do
  if curl -sS -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health 2>/dev/null | grep -q 200; then
    echo "Backend healthy."
    break
  fi
  sleep 2
done

if [ -z "$NO_NGINX" ] && command -v nginx >/dev/null 2>&1; then
  echo "Reloading nginx..."
  sudo nginx -t && sudo nginx -s reload
fi

echo "=== Live deploy done. https://fusionemsquantum.com ==="
