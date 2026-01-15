import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["JWT_SECRET_KEY"] = "test-secret"

from fastapi.testclient import TestClient

from core.database import Base, engine
from main import app


def create_test_client():
    Base.metadata.create_all(bind=engine)
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
