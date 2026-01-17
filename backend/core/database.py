from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool
import logging

from core.config import settings

logger = logging.getLogger("fusonems")


def _connect_args(database_url: str) -> dict:
    """Return connection arguments based on database type.
    SQLite requires check_same_thread=False for multi-threaded FastAPI."""
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


def _resolve_database_url(database_url: str) -> str:
    """Resolve the database URL with fallback to SQLite in development.
    In production, DATABASE_URL must be explicitly set; no fallback is allowed."""
    if database_url:
        return database_url
    if settings.ENV == "production":
        raise RuntimeError(
            "DATABASE_URL must be set in production environment. "
            "No fallback to SQLite is permitted."
        )
    # Development fallback to SQLite
    logger.warning("DATABASE_URL not set, falling back to sqlite:///./runtime.db")
    return "sqlite:///./runtime.db"


def _create_engine_with_pooling(database_url: str):
    """Create a SQLAlchemy engine with production-grade connection pooling.
    
    Pooling configuration:
    - pool_size: Number of connections to maintain in the pool (default: 5)
    - max_overflow: Additional connections to create beyond pool_size when needed (default: 10)
    - pool_timeout: Seconds to wait before giving up on getting a connection (default: 30)
    - pool_recycle: Recycle connections after N seconds to avoid stale connections (default: 1800)
    - pool_pre_ping: Test connections before using them to handle disconnects gracefully
    - echo: Log SQL statements (disabled in production for performance)
    
    If the database is unreachable at startup:
    - Production: Fail fast with RuntimeError
    - Development: Log warning and continue (allows local dev without DB)
    """
    resolved_url = _resolve_database_url(database_url)
    connect_args = _connect_args(resolved_url)
    
    engine = create_engine(
        resolved_url,
        poolclass=QueuePool,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_pre_ping=True,
        echo=(settings.ENV != "production"),
        connect_args=connect_args,
    )
    
    # Perform lightweight connectivity test
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            # Extract safe database identifier for logging (no credentials)
            db_name = "sqlite" if "sqlite" in resolved_url else resolved_url.split("@")[-1].split("/")[0] if "@" in resolved_url else "database"
            logger.info(f"Database connectivity verified for {db_name}")
    except Exception as e:
        if settings.ENV == "production":
            raise RuntimeError(
                f"Database connectivity test failed in production: {e}. "
                "Application cannot start without database connection."
            )
        else:
            logger.warning(f"Database connectivity test failed in development: {e}. Continuing anyway.")
    
    return engine


# Create engines using canonical pooling configuration
# All engines use the same hardened settings for consistency
engine = _create_engine_with_pooling(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

telehealth_engine = _create_engine_with_pooling(
    settings.TELEHEALTH_DATABASE_URL or settings.DATABASE_URL
)
TelehealthSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=telehealth_engine
)
TelehealthBase = declarative_base()

fire_engine = _create_engine_with_pooling(
    settings.FIRE_DATABASE_URL or settings.DATABASE_URL
)
FireSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=fire_engine)
FireBase = declarative_base()

hems_engine = _create_engine_with_pooling(settings.DATABASE_URL)
HemsSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=hems_engine)
HemsBase = declarative_base()


def get_db():
    """Dependency helper for main database session.
    Yields a session and ensures it's closed after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_telehealth_db():
    """Dependency helper for telehealth database session.
    Yields a session and ensures it's closed after use."""
    db = TelehealthSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_fire_db():
    """Dependency helper for fire database session.
    Yields a session and ensures it's closed after use."""
    db = FireSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_hems_db():
    """Dependency helper for HEMS database session.
    Yields a session and ensures it's closed after use."""
    db = HemsSessionLocal()
    try:
        yield db
    finally:
        db.close()
