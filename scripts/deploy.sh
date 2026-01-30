#!/usr/bin/env bash
# FusionEMS Quantum – deploy locally (Docker Compose) or trigger DigitalOcean App Platform.
# Usage:
#   ./scripts/deploy.sh              # Build and start stack with docker-compose
#   ./scripts/deploy.sh digitalocean  # Trigger DO App Platform deploy (needs DO_API_TOKEN, DO_APP_ID)

set -e
REPO_DIR="${REPO_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$REPO_DIR"

case "${1:-}" in
  digitalocean)
    if [ -z "$DO_API_TOKEN" ] || [ -z "$DO_APP_ID" ]; then
      echo "DigitalOcean deploy requires DO_API_TOKEN and DO_APP_ID."
      echo "  export DO_API_TOKEN=your_token"
      echo "  export DO_APP_ID=your_app_id"
      exit 1
    fi
    exec "$REPO_DIR/infrastructure/digitalocean/redeploy.sh"
    ;;
  *)
    echo "Building and starting stack (db, redis, valhalla, backend, keycloak, frontend)..."
    if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
      docker compose up -d --build
      docker compose ps
    else
      docker-compose up -d --build
      docker-compose ps
    fi
    echo "Done. Backend: http://localhost:8000  Frontend: http://localhost:3000"
    ;;
esac
