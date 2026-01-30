#!/usr/bin/env bash
# Run this ON THE SERVER (e.g. 157.245.6.217) to apply production nginx and ensure root = marketing.
# Usage: sudo bash scripts/deploy_production_nginx.sh

set -e
REPO_DIR="${REPO_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
NGINX_AVAILABLE="/etc/nginx/sites-available/fusionemsquantum"
NGINX_ENABLED="/etc/nginx/sites-enabled/fusionemsquantum"

echo "Using repo dir: $REPO_DIR"
cp "$REPO_DIR/infrastructure/nginx/fusionemsquantum.conf" "$NGINX_AVAILABLE"
ln -sf "$NGINX_AVAILABLE" "$NGINX_ENABLED"
nginx -t
systemctl reload nginx
echo "Nginx reloaded. Root (/) -> port 3000, /api/ -> port 8000."
