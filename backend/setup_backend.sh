#!/bin/zsh
setopt NO_BANG_HIST
# ==========================================================
# 🚑 FusonEMS Quantum Backend Auto-Setup Script
# ==========================================================
# ⚠️  SCAFFOLDING ONLY - FOR INITIAL PROJECT SETUP
# This script generates a minimal backend structure for development.
# For runtime database engine behavior, use backend/core/database.py
# which contains the canonical, hardened pooling configuration.
# ==========================================================

echo "🔍 Initializing FusonEMS Quantum Backend Setup..."

cd "$(dirname "$0")" || exit
mkdir -p core db services/cad utils

# --- Virtual Environment ---
if [ ! -d "venv" ]; then
  echo "⚙️  Creating virtual environment..."
  python3 -m venv venv
fi
source venv/bin/activate

# --- Install Dependencies ---
echo "📦 Installing dependencies..."
cat <<'EOF' > requirements.txt
fastapi
uvicorn
sqlalchemy
python-jose
pydantic
pydantic-settings
psycopg2-binary
EOF
pip install -r requirements.txt

# --- Core Config ---
cat <<'EOF' > core/config.py
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = Field("FusonEMS Quantum", env="PROJECT_NAME")
    DATABASE_URL: str = Field("postgresql://admin:securepass@localhost:5432/fusonems", env="DATABASE_URL")
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
EOF

# --- Database ---
# NOTE: This is a minimal scaffolding version.
# For production runtime, use the canonical backend/core/database.py
# which includes hardened pooling, fail-fast connectivity checks, and tunable parameters.
cat <<'EOF' > core/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
EOF

# --- Logger ---
cat <<'EOF' > utils/logger.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("fusonems")
EOF

# --- CAD Router ---
mkdir -p services/cad
cat <<'EOF' > services/cad/cad_router.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from utils.logger import logger

router = APIRouter(prefix="/api/cad", tags=["CAD"])

@router.get("/units")
def get_units():
    return {"active_units": [
        {"unit_id": "A1", "status": "Available", "location": [44.9, -89.6]},
        {"unit_id": "M2", "status": "En Route", "location": [44.95, -89.63]},
    ]}

@router.post("/dispatch")
def dispatch_unit(data: dict):
    logger.info(f"🚑 Dispatching {data.get('unit_id')} to call {data.get('call_id')}")
    return {"status": "dispatched", "data": data}
EOF

# --- Main App ---
cat <<'EOF' > main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services.cad.cad_router import router as cad_router

app = FastAPI(title="FusonEMS Quantum", version="2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(cad_router)

@app.get("/")
def root():
    return {"status": "online", "system": "FusonEMS Quantum"}
EOF

# --- Run PostgreSQL and Server ---
echo "🔄 Checking PostgreSQL..."
if ! pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
  echo "🚀 Starting PostgreSQL..."
  brew services start postgresql@16
  sleep 3
fi

echo "🚀 Starting FusonEMS Quantum Backend..."
uvicorn main:app --reload --host 127.0.0.1 --port 8000
