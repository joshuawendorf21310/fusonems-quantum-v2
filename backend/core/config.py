from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = Field("FusonEMS Quantum")
    DATABASE_URL: Optional[str] = Field("")
    ALLOWED_ORIGINS: str = Field("http://localhost:5173")
    JWT_SECRET_KEY: str = Field("change-me")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(60)
    ENV: str = Field("development")
    DB_POOL_SIZE: int = Field(5)
    DB_MAX_OVERFLOW: int = Field(10)
    TELNYX_API_KEY: str = Field("")
    TELNYX_NUMBER: str = Field("")
    TELNYX_CONNECTION_ID: str = Field("")
    TELNYX_MESSAGING_PROFILE_ID: str = Field("")
    TELNYX_PUBLIC_KEY: str = Field("")
    TELNYX_REQUIRE_SIGNATURE: bool = Field(False)
    LOB_API_KEY: str = Field("")
    POSTMARK_SERVER_TOKEN: str = Field("")
    POSTMARK_DEFAULT_SENDER: str = Field("")
    POSTMARK_REQUIRE_SIGNATURE: bool = Field(False)
    POSTMARK_API_BASE: str = Field("https://api.postmarkapp.com")
    POSTMARK_SEND_DISABLED: bool = Field(False)
    OFFICEALLY_FTP_HOST: str = Field("")
    OFFICEALLY_FTP_USER: str = Field("")
    OFFICEALLY_FTP_PASSWORD: str = Field("")
    OFFICEALLY_FTP_PORT: int = Field(21)
    MPI_MATCH_WEIGHTS: str = Field('{"first_name": 0.25, "last_name": 0.25, "date_of_birth": 0.3, "phone": 0.1, "address": 0.1}')
    MPI_MATCH_THRESHOLD: float = Field(0.35)
    STORAGE_ENCRYPTION_KEY: str = Field("change-me")
    DOCS_STORAGE_BACKEND: str = Field("local")
    DOCS_STORAGE_LOCAL_DIR: str = Field("storage/documents")
    DOCS_S3_ENDPOINT: str = Field("")
    DOCS_S3_REGION: str = Field("")
    DOCS_S3_BUCKET: str = Field("")
    DOCS_S3_ACCESS_KEY: str = Field("")
    DOCS_S3_SECRET_KEY: str = Field("")
    DOCS_ENCRYPTION_KEY: str = Field("change-me")
    TELEHEALTH_DATABASE_URL: str = Field("")
    TELEHEALTH_API_KEY: str = Field("")
    OPENID_CLIENT_ID: str = Field("")
    OPENID_SECRET: str = Field("")
    FIRE_DATABASE_URL: str = Field("")
    OIDC_ENABLED: bool = Field(False)
    OIDC_ISSUER_URL: str = Field("")
    OIDC_CLIENT_ID: str = Field("")
    OIDC_CLIENT_SECRET: str = Field("")
    OIDC_REDIRECT_URI: str = Field("")
    OIDC_POST_LOGOUT_REDIRECT_URI: str = Field("")
    OIDC_SCOPES: str = Field("openid profile email")
    LOCAL_AUTH_ENABLED: bool = Field(True)
    SESSION_COOKIE_NAME: str = Field("session")
    CSRF_COOKIE_NAME: str = Field("csrf_token")
    AUTH_RATE_LIMIT_PER_MIN: int = Field(20)
    STRIPE_SECRET_KEY: str = Field("")
    STRIPE_WEBHOOK_SECRET: str = Field("")
    STRIPE_PUBLISHABLE_KEY: str = Field("")
    STRIPE_ENV: str = Field("test")
    BILLING_BRAND_NAME: str = Field("FusonEMS Quantum")
    STRIPE_PRICE_ID_CORE_MONTHLY: str = Field("")
    STRIPE_PRICE_ID_CAD: str = Field("")
    STRIPE_PRICE_ID_EPCR: str = Field("")
    STRIPE_PRICE_ID_BILLING: str = Field("")
    STRIPE_PRICE_ID_COMMS: str = Field("")
    STRIPE_PRICE_ID_SCHEDULING: str = Field("")
    STRIPE_PRICE_ID_FIRE: str = Field("")
    STRIPE_PRICE_ID_HEMS: str = Field("")
    STRIPE_PRICE_ID_INVENTORY: str = Field("")
    STRIPE_PRICE_ID_TRAINING: str = Field("")
    STRIPE_PRICE_ID_QA_LEGAL: str = Field("")
    STRIPE_ENFORCE_ENTITLEMENTS: bool = Field(False)
    SMART_MODE: bool = Field(True)
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

def validate_settings_runtime(settings: Settings) -> None:
    if settings.ENV != "production":
        return
    if not settings.DATABASE_URL:
        raise RuntimeError("DATABASE_URL must be set for production.")
    if not settings.JWT_SECRET_KEY or settings.JWT_SECRET_KEY == "change-me":
        raise RuntimeError("JWT_SECRET_KEY must be set for production.")
    if not settings.STORAGE_ENCRYPTION_KEY or settings.STORAGE_ENCRYPTION_KEY == "change-me":
        raise RuntimeError("STORAGE_ENCRYPTION_KEY must be set for production.")
    if not settings.DOCS_ENCRYPTION_KEY or settings.DOCS_ENCRYPTION_KEY == "change-me":
        raise RuntimeError("DOCS_ENCRYPTION_KEY must be set for production.")
    if settings.DOCS_STORAGE_BACKEND not in {"local", "s3"}:
        raise RuntimeError("DOCS_STORAGE_BACKEND must be 'local' or 's3'.")
    if settings.DOCS_STORAGE_BACKEND == "s3":
        if not settings.DOCS_S3_BUCKET:
            raise RuntimeError("DOCS_S3_BUCKET must be set for S3 storage.")
        if not settings.DOCS_S3_ACCESS_KEY or not settings.DOCS_S3_SECRET_KEY:
            raise RuntimeError("DOCS_S3_ACCESS_KEY and DOCS_S3_SECRET_KEY are required for S3 storage.")
    if settings.OIDC_ENABLED:
        if not settings.OIDC_ISSUER_URL:
            raise RuntimeError("OIDC_ISSUER_URL must be set when OIDC is enabled.")
        if not settings.OIDC_CLIENT_ID:
            raise RuntimeError("OIDC_CLIENT_ID must be set when OIDC is enabled.")
        if not settings.OIDC_REDIRECT_URI:
            raise RuntimeError("OIDC_REDIRECT_URI must be set when OIDC is enabled.")
    if settings.TELNYX_REQUIRE_SIGNATURE and not settings.TELNYX_PUBLIC_KEY:
        raise RuntimeError("TELNYX_PUBLIC_KEY must be set when signature verification is enabled.")
    if settings.POSTMARK_REQUIRE_SIGNATURE and not settings.POSTMARK_SERVER_TOKEN:
        raise RuntimeError("POSTMARK_SERVER_TOKEN must be set when signature verification is enabled.")
    if settings.STRIPE_SECRET_KEY and settings.STRIPE_ENV not in {"test", "live"}:
        raise RuntimeError("STRIPE_ENV must be 'test' or 'live'.")
    if settings.STRIPE_SECRET_KEY and settings.STRIPE_WEBHOOK_SECRET == "":
        raise RuntimeError("STRIPE_WEBHOOK_SECRET must be set when Stripe is enabled.")
