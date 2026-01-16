import os
import sys
from pathlib import Path

db_path = Path("test.db")
if db_path.exists():
    db_path.unlink()

backend_root = Path(__file__).resolve().parents[1]
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["TELEHEALTH_DATABASE_URL"] = "sqlite:///./test.db"
os.environ["FIRE_DATABASE_URL"] = "sqlite:///./test.db"
os.environ["HEMS_DATABASE_URL"] = "sqlite:///./test.db"
os.environ["JWT_SECRET_KEY"] = "test-secret"

from fastapi.testclient import TestClient

from core.database import Base, FireBase, HemsBase, TelehealthBase, engine
from main import app


def create_test_client():
    Base.metadata.create_all(bind=engine)
    FireBase.metadata.create_all(bind=engine)
    TelehealthBase.metadata.create_all(bind=engine)
    HemsBase.metadata.create_all(bind=engine)
    return TestClient(app)


def drop_test_db():
    Base.metadata.drop_all(bind=engine)


import pytest


@pytest.fixture()
def client():
    client = create_test_client()
    try:
        yield client
    finally:
        drop_test_db()
