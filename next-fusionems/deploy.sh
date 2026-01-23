#!/bin/zsh
# ==========================================================
# 🚀 FusonEMS Quantum — DigitalOcean Auto Redeploy Script
# ==========================================================

# --- CONFIGURATION ---
export DO_APP_ID="26f349b5-bfb2-4727-9b5b-3f940709c4ae"   # your app ID

# --- EXECUTION ---
echo "🚀 Triggering DigitalOcean redeploy for app ID: ${DO_APP_ID} ..."
curl -X POST "https://api.digitalocean.com/v2/apps/${DO_APP_ID}/deployments" \
  -H "Authorization: Bearer ${DO_API_TOKEN}" \
  -H "Content-Type: application/json"

echo ""
echo "✅ Redeploy triggered successfully!"
echo "🌎 Watch deployment progress at: https://cloud.digitalocean.com/apps/${DO_APP_ID}"
echo "----------------------------------------------------------"
