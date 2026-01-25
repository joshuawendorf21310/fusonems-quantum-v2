from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from core.config import settings


if not settings.DATABASE_URL:
    raise RuntimeError("DATABASE_URL must be set to a PostgreSQL connection string.")


def _create_engine(database_url: str):
    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
    )


def _database_url_or_default(database_url: str) -> str:
    return database_url or settings.DATABASE_URL


engine = _create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

telehealth_engine = _create_engine(_database_url_or_default(settings.TELEHEALTH_DATABASE_URL))
TelehealthSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=telehealth_engine)
TelehealthBase = declarative_base()

fire_engine = _create_engine(_database_url_or_default(settings.FIRE_DATABASE_URL))
FireSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=fire_engine)
FireBase = declarative_base()

hems_engine = _create_engine(_database_url_or_default(settings.HEMS_DATABASE_URL))
HemsSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=hems_engine)
HemsBase = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_telehealth_db():
    db = TelehealthSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_fire_db():
    db = FireSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_hems_db():
    db = HemsSessionLocal()
    try:
        yield db
    finally:
        db.close()
