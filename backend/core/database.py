from __future__ import annotations

from functools import lru_cache
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from core.config import settings
from core.logger import logger


def _connect_args(database_url: str) -> dict[str, object]:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


def _resolve_database_url(database_url: Optional[str]) -> str:
    if database_url:
        return database_url
    return "sqlite:///./runtime.db"


def _engine_kwargs(database_url: str) -> dict[str, object]:
    kwargs: dict[str, object] = {
        "pool_pre_ping": True,
        "connect_args": _connect_args(database_url),
    }
    if database_url.startswith("sqlite"):
        kwargs["poolclass"] = StaticPool
    else:
        kwargs.update(
            {
                "pool_size": settings.DB_POOL_SIZE,
                "max_overflow": settings.DB_MAX_OVERFLOW,
            }
        )
    return kwargs


def _primary_database_url() -> str:
    return _resolve_database_url(settings.DATABASE_URL)


def _telehealth_database_url() -> str:
    return _resolve_database_url(
        getattr(settings, "TELEHEALTH_DATABASE_URL", None) or settings.DATABASE_URL
    )


def _fire_database_url() -> str:
    return _resolve_database_url(
        getattr(settings, "FIRE_DATABASE_URL", None) or settings.DATABASE_URL
    )


def _hems_database_url() -> str:
    return _resolve_database_url(
        getattr(settings, "HEMS_DATABASE_URL", None) or settings.DATABASE_URL
    )


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    database_url = _primary_database_url()
    return create_engine(database_url, **_engine_kwargs(database_url))


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker:
    return sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


@lru_cache(maxsize=1)
def get_telehealth_engine() -> Engine:
    database_url = _telehealth_database_url()
    return create_engine(database_url, **_engine_kwargs(database_url))


@lru_cache(maxsize=1)
def get_telehealth_session_factory() -> sessionmaker:
    return sessionmaker(autocommit=False, autoflush=False, bind=get_telehealth_engine())


@lru_cache(maxsize=1)
def get_fire_engine() -> Engine:
    database_url = _fire_database_url()
    return create_engine(database_url, **_engine_kwargs(database_url))


@lru_cache(maxsize=1)
def get_fire_session_factory() -> sessionmaker:
    return sessionmaker(autocommit=False, autoflush=False, bind=get_fire_engine())


@lru_cache(maxsize=1)
def get_hems_engine() -> Engine:
    database_url = _hems_database_url()
    return create_engine(database_url, **_engine_kwargs(database_url))


@lru_cache(maxsize=1)
def get_hems_session_factory() -> sessionmaker:
    return sessionmaker(autocommit=False, autoflush=False, bind=get_hems_engine())


Base = declarative_base()
FireBase = declarative_base()
TelehealthBase = declarative_base()
HemsBase = declarative_base()


SessionLocal = get_session_factory()
TelehealthSessionLocal = get_telehealth_session_factory()
FireSessionLocal = get_fire_session_factory()
HemsSessionLocal = get_hems_session_factory()


def get_db():
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


def get_telehealth_db():
    session_factory = get_telehealth_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


def get_fire_db():
    session_factory = get_fire_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


def get_hems_db():
    session_factory = get_hems_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


def create_session() -> Session:
    return get_session_factory()()


def create_telehealth_session() -> Session:
    return get_telehealth_session_factory()()


def create_fire_session() -> Session:
    return get_fire_session_factory()()


def create_hems_session() -> Session:
    return get_hems_session_factory()()
