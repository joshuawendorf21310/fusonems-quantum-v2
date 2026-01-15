#!/bin/zsh
# ==========================================================
# 🚑 FusonEMS Quantum Startup Script
# ==========================================================

echo "🔍 Checking project environment..."

# Navigate to project backend directory
cd "$(dirname "$0")" || exit

# Activate virtual environment
if [ -d "venv" ]; then
  echo "✅ Activating virtual environment..."
  source venv/bin/activate
else
  echo "⚠️  Virtual environment not found — creating one..."
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
fi

# Check if PostgreSQL is running
echo "🔄 Checking PostgreSQL service..."
if ! pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
  echo "🚀 Starting PostgreSQL via Homebrew..."
  brew services start postgresql@16
  sleep 3
fi

# Kill any existing uvicorn instances
echo "🧹 Killing old backend instances..."
pkill -f uvicorn 2>/dev/null || true

# Launch the backend
echo "🚀 Starting FusonEMS Quantum Backend..."
uvicorn main:app --reload --host 127.0.0.1 --port 8000
