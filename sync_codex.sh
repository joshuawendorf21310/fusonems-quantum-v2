#!/bin/zsh
# ======================================================
# 🤖 Codex Sync Setup for FusonEMS Quantum
# ======================================================

# --- Configurable Variables ---
REPO_URL="https://github.com/joshuawendorf21310/fusonems-quantum-v2.git"
PROJECT_NAME="fusonems-quantum-complete"
LOCAL_PATH="$HOME/Projects/$PROJECT_NAME"

# --- Ensure directory exists ---
if [ ! -d "$LOCAL_PATH" ]; then
  echo "📁 Creating project directory at $LOCAL_PATH ..."
  mkdir -p "$LOCAL_PATH"
  cd "$LOCAL_PATH" || exit
  git clone "$REPO_URL" .
else
  cd "$LOCAL_PATH" || exit
  echo "🔄 Pulling latest project updates..."
  git pull origin main
fi

# --- Notify Codex via metadata file ---
echo "🧠 Syncing with Codex context..."
mkdir -p .codex
cat <<EOF > .codex/context.json
{
  "project": "$PROJECT_NAME",
  "repo": "$REPO_URL",
  "linked_to": "ChatGPT main project assistant",
  "updated_at": "$(date)"
}
EOF

# --- Initialize environment ---
if [ -d "backend" ]; then
  cd backend || exit
  echo "✅ Setting up backend virtual environment..."
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  deactivate
  cd ..
fi

echo "✅ Codex Sync Complete!"
echo "💬 You can now use ChatGPT in VS Code and type:"
echo "     /sync project fusonems-quantum-v2"
echo "   ...to load the context from your GitHub + local repo."
echo "--------------------------------------------------------"
