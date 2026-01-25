from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = Field("FusonEMS Quantum", env="PROJECT_NAME")
    DATABASE_URL: Optional[str] = Field("", env="DATABASE_URL")
    ALLOWED_ORIGINS: str = Field("http://localhost:5173", env="ALLOWED_ORIGINS")
    JWT_SECRET_KEY: str = Field("change-me", env=["JWT_SECRET_KEY", "JWT_SECRET"])
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(60, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    ENV: str = Field("development", env="ENV")
    DB_POOL_SIZE: int = Field(5, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(10, env="DB_MAX_OVERFLOW")
    TELNYX_API_KEY: str = Field("", env="TELNYX_API_KEY")
    TELNYX_NUMBER: str = Field("", env="TELNYX_NUMBER")
    TELNYX_CONNECTION_ID: str = Field("", env="TELNYX_CONNECTION_ID")
    TELNYX_MESSAGING_PROFILE_ID: str = Field("", env="TELNYX_MESSAGING_PROFILE_ID")
    TELNYX_PUBLIC_KEY: str = Field("", env="TELNYX_PUBLIC_KEY")
    TELNYX_REQUIRE_SIGNATURE: bool = Field(False, env="TELNYX_REQUIRE_SIGNATURE")
    LOB_API_KEY: str = Field("", env="LOB_API_KEY")
    POSTMARK_SERVER_TOKEN: str = Field("", env="POSTMARK_SERVER_TOKEN")
    POSTMARK_DEFAULT_SENDER: str = Field("", env="POSTMARK_DEFAULT_SENDER")
    POSTMARK_REQUIRE_SIGNATURE: bool = Field(False, env="POSTMARK_REQUIRE_SIGNATURE")
    POSTMARK_API_BASE: str = Field("https://api.postmarkapp.com", env="POSTMARK_API_BASE")
    POSTMARK_SEND_DISABLED: bool = Field(False, env="POSTMARK_SEND_DISABLED")
    OFFICEALLY_FTP_HOST: str = Field("", env="OFFICEALLY_FTP_HOST")
    OFFICEALLY_FTP_USER: str = Field("", env="OFFICEALLY_FTP_USER")
    OFFICEALLY_FTP_PASSWORD: str = Field("", env="OFFICEALLY_FTP_PASSWORD")
    OFFICEALLY_FTP_PORT: int = Field(21, env="OFFICEALLY_FTP_PORT")
    APP_BASE_URL: str = Field("", env="APP_BASE_URL")
    FUSIONEMS_CORE_URL: str = Field("", env="FUSIONEMS_CORE_URL")
    STORAGE_ENCRYPTION_KEY: str = Field("change-me", env="STORAGE_ENCRYPTION_KEY")
    DOCS_STORAGE_BACKEND: str = Field("local", env="DOCS_STORAGE_BACKEND")
    DOCS_STORAGE_LOCAL_DIR: str = Field("storage/documents", env="DOCS_STORAGE_LOCAL_DIR")
    DOCS_S3_ENDPOINT: str = Field("", env="DOCS_S3_ENDPOINT")
    DOCS_S3_REGION: str = Field("", env="DOCS_S3_REGION")
    DOCS_S3_BUCKET: str = Field("", env="DOCS_S3_BUCKET")
    DOCS_S3_ACCESS_KEY: str = Field("", env="DOCS_S3_ACCESS_KEY")
    DOCS_S3_SECRET_KEY: str = Field("", env="DOCS_S3_SECRET_KEY")
    DOCS_ENCRYPTION_KEY: str = Field("change-me", env="DOCS_ENCRYPTION_KEY")
    TELEHEALTH_DATABASE_URL: str = Field("", env="TELEHEALTH_DATABASE_URL")
    HEMS_DATABASE_URL: str = Field("", env="HEMS_DATABASE_URL")
    TELEHEALTH_API_KEY: str = Field("", env="TELEHEALTH_API_KEY")
    OPENID_CLIENT_ID: str = Field("", env="OPENID_CLIENT_ID")
    OPENID_SECRET: str = Field("", env="OPENID_SECRET")
    FIRE_DATABASE_URL: str = Field("", env="FIRE_DATABASE_URL")
    OIDC_ENABLED: bool = Field(False, env="OIDC_ENABLED")
    OIDC_ISSUER_URL: str = Field("", env="OIDC_ISSUER_URL")
    OIDC_CLIENT_ID: str = Field("", env="OIDC_CLIENT_ID")
    OIDC_CLIENT_SECRET: str = Field("", env="OIDC_CLIENT_SECRET")
    OIDC_REDIRECT_URI: str = Field("", env="OIDC_REDIRECT_URI")
    OIDC_POST_LOGOUT_REDIRECT_URI: str = Field("", env="OIDC_POST_LOGOUT_REDIRECT_URI")
    OIDC_SCOPES: str = Field("openid profile email", env="OIDC_SCOPES")
    LOCAL_AUTH_ENABLED: bool = Field(True, env="LOCAL_AUTH_ENABLED")
    SESSION_COOKIE_NAME: str = Field("session", env="SESSION_COOKIE_NAME")
    CSRF_COOKIE_NAME: str = Field("csrf_token", env="CSRF_COOKIE_NAME")
    AUTH_RATE_LIMIT_PER_MIN: int = Field(20, env="AUTH_RATE_LIMIT_PER_MIN")
    STRIPE_SECRET_KEY: str = Field("", env="STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET: str = Field("", env="STRIPE_WEBHOOK_SECRET")
    STRIPE_PUBLISHABLE_KEY: str = Field("", env="STRIPE_PUBLISHABLE_KEY")
    STRIPE_ENV: str = Field("test", env="STRIPE_ENV")
    BILLING_BRAND_NAME: str = Field("FusonEMS Quantum", env="BILLING_BRAND_NAME")
    STRIPE_PRICE_ID_CORE_MONTHLY: str = Field("", env="STRIPE_PRICE_ID_CORE_MONTHLY")
    STRIPE_PRICE_ID_CAD: str = Field("", env="STRIPE_PRICE_ID_CAD")
    STRIPE_PRICE_ID_EPCR: str = Field("", env="STRIPE_PRICE_ID_EPCR")
    STRIPE_PRICE_ID_BILLING: str = Field("", env="STRIPE_PRICE_ID_BILLING")
    STRIPE_PRICE_ID_COMMS: str = Field("", env="STRIPE_PRICE_ID_COMMS")
    STRIPE_PRICE_ID_SCHEDULING: str = Field("", env="STRIPE_PRICE_ID_SCHEDULING")
    STRIPE_PRICE_ID_FIRE: str = Field("", env="STRIPE_PRICE_ID_FIRE")
    STRIPE_PRICE_ID_HEMS: str = Field("", env="STRIPE_PRICE_ID_HEMS")
    STRIPE_PRICE_ID_INVENTORY: str = Field("", env="STRIPE_PRICE_ID_INVENTORY")
    STRIPE_PRICE_ID_TRAINING: str = Field("", env="STRIPE_PRICE_ID_TRAINING")
    STRIPE_PRICE_ID_QA_LEGAL: str = Field("", env="STRIPE_PRICE_ID_QA_LEGAL")
    STRIPE_ENFORCE_ENTITLEMENTS: bool = Field(False, env="STRIPE_ENFORCE_ENTITLEMENTS")
    SMART_MODE: bool = Field(True, env="SMART_MODE")
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
