#!/bin/zsh
# ==========================================================
# 🚑 FusonEMS Quantum Full Automatic Dev Environment
# ==========================================================

set -e

echo "🔍 Starting full automatic dev environment..."

# Move to project root
cd "$(dirname "$0")" || exit

# Stop any existing backend/frontend instances
echo "🧹 Stopping existing services on ports 8000/8080..."
lsof -ti tcp:8000 | xargs kill -9 2>/dev/null || true
lsof -ti tcp:8080 | xargs kill -9 2>/dev/null || true

# --- Backend Setup ---
echo "🖤 Setting up backend..."
cd backend || exit

# Create Python venv if missing
if [ ! -d "venv" ]; then
  echo "⚠️  Creating Python virtual environment..."
  python3 -m venv venv
fi

echo "✅ Activating Python virtual environment..."
source venv/bin/activate

# Install backend dependencies
echo "🔄 Installing backend dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# Check PostgreSQL service
echo "🔄 Checking PostgreSQL..."
if ! pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
  echo "🚀 Starting PostgreSQL via Homebrew..."
  brew services start postgresql@16
  sleep 3
fi

# Run backend tests
echo "🧪 Running backend tests..."
python3 -m pytest --maxfail=1 --disable-warnings -q

cd ..

# --- Frontend Setup ---
echo "🧡 Setting up frontend..."
cd next-fusionems || exit

# Install frontend dependencies
echo "🔄 Installing frontend dependencies..."
npm install
echo "🧪 Running frontend tests..."
npm test

echo "✅ Frontend dependencies installed."

cd ..

# Launch backend and frontend in split terminals
echo "🚀 Launching backend and frontend in split terminals..."
osascript <<'APPLESCRIPT'
tell application "Terminal"
  do script "cd /Users/joshuawendorf/fusonems-quantum-v2/backend && source venv/bin/activate && uvicorn main:app --reload --host 127.0.0.1 --port 8000"
  do script "cd /Users/joshuawendorf/fusonems-quantum-v2/next-fusionems && npm install && npm run dev"
  activate
end tell
APPLESCRIPT

# --- Done ---
echo "✅ FusonEMS Quantum dev environment is live!"
echo "🌎 Backend: http://127.0.0.1:8000"
echo "🌎 Frontend: http://localhost:8080"
