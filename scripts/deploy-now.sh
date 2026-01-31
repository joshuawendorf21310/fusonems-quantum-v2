#!/usr/bin/env bash
# Deploy directly from this machine (bypasses GitHub Actions).
# Uses ~/.ssh/id_ed25519. Run from repo root.
set -e
HOST="${DEPLOY_HOST:-157.245.6.217}"
USER="${DEPLOY_USER:-deploy}"
PATH_REMOTE="${DEPLOY_PATH:-/var/www/fusionems}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== Deploying to $USER@$HOST:$PATH_REMOTE ==="
rsync -avz --delete \
  -e "ssh -i ~/.ssh/id_ed25519 -o StrictHostKeyChecking=no" \
  --exclude 'backend/.env' \
  --exclude '.env' --exclude '.env.local' --exclude '.env.production' \
  --exclude 'node_modules' --exclude '.next' --exclude '.git' \
  ./ "$USER@$HOST:$PATH_REMOTE/"

ssh -i ~/.ssh/id_ed25519 -o StrictHostKeyChecking=no "$USER@$HOST" "docker compose -p fusonems-quantum-v2 down 2>/dev/null || true; cd $PATH_REMOTE && docker compose down 2>/dev/null || true; [ ! -f backend/.env ] && cp backend/.env.example backend/.env 2>/dev/null || true; sleep 2; docker compose up -d --build"
echo "=== Done ==="
