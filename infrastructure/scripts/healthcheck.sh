#!/bin/zsh
set -e

BACKEND_URL=${BACKEND_URL:-http://127.0.0.1:8000}
FRONTEND_URL=${FRONTEND_URL:-http://127.0.0.1:3000}

curl -fsS "${BACKEND_URL}/" >/dev/null
curl -fsS "${FRONTEND_URL}/" >/dev/null

echo "Healthcheck OK"
