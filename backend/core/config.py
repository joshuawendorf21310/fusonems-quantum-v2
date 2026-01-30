from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Self-Hosted Mailu SMTP/IMAP
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    # Founder identity (person); used when founder sends from dashboard
    FOUNDER_EMAIL: str = "joshua.j.wendorf@fusionemsquantum.com"
    # Aliases (different addresses for different purposes)
    BILLING_FROM_EMAIL: Optional[str] = "billing@fusionemsquantum.com"  # Patient statements, billing correspondence
    SUPPORT_EMAIL: Optional[str] = "billing@fusionemsquantum.com"  # Contact/support (can be same as billing)
    NOREPLY_EMAIL: Optional[str] = None  # System notifications; if unset uses SMTP_USERNAME or FOUNDER_EMAIL
    SMTP_FROM_EMAIL: Optional[str] = None  # Generic override for From when no alias specified; defaults above used per flow

    IMAP_HOST: Optional[str] = None
    IMAP_PORT: int = 993
    IMAP_USERNAME: Optional[str] = None
    IMAP_PASSWORD: Optional[str] = None
    IMAP_USE_TLS: bool = True

    ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./app.db"
    JWT_SECRET_KEY: str = "dev-secret"
    STORAGE_ENCRYPTION_KEY: str = "dev-storage"
    DOCS_ENCRYPTION_KEY: str = "dev-docs"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    AUTH_RATE_LIMIT_PER_MIN: int = 20
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    SESSION_COOKIE_NAME: str = "session"
    CSRF_COOKIE_NAME: str = "csrf_token"

    # Stripe (patient payments, checkout, subscriptions, webhooks)
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_publishable_key: str = ""
    stripe_enforce_entitlements: bool = False
    BILLING_BRAND_NAME: str = "FusionEMS Quantum"

    stripe_price_id_cad: str = ""
    stripe_price_id_epcr: str = ""
    stripe_price_id_billing: str = ""
    stripe_price_id_comms: str = ""
    stripe_price_id_scheduling: str = ""
    stripe_price_id_fire: str = ""
    stripe_price_id_hems: str = ""
    stripe_price_id_inventory: str = ""
    stripe_price_id_training: str = ""
    stripe_price_id_qa_legal: str = ""
    
    # Office Ally Configuration
    OFFICEALLY_ENABLED: bool = False
    OFFICEALLY_INTERCHANGE_ID: str = "FUSIONEMS"
    OFFICEALLY_TRADING_PARTNER_ID: str = "FUSIONEMS001"
    OFFICEALLY_SUBMITTER_NAME: str = "FUSION EMS BILLING"
    OFFICEALLY_SUBMITTER_ID: str = "FUSIONEMS001"
    OFFICEALLY_CONTACT_PHONE: str = "555-555-5555"
    OFFICEALLY_DEFAULT_NPI: str = "1234567890"
    OFFICEALLY_FTP_HOST: str = "ftp10.officeally.com"
    OFFICEALLY_FTP_PORT: int = 22
    OFFICEALLY_FTP_USER: str = ""
    OFFICEALLY_FTP_PASSWORD: str = ""
    OFFICEALLY_SFTP_DIRECTORY: str = "inbound"  # Submissions go to "inbound" folder
    OFFICEALLY_SFTP_OUTBOUND_DIRECTORY: str = "outbound"  # Reports/ERA come from "outbound" folder
    
    # CAD Backend Socket.io Bridge
    CAD_BACKEND_URL: str = "http://localhost:3000"
    CAD_BACKEND_AUTH_TOKEN: str = "fastapi-bridge-secure-token-change-in-production"
    
    # Metriport Configuration
    METRIPORT_ENABLED: bool = False
    METRIPORT_API_KEY: str = ""
    METRIPORT_BASE_URL: str = "https://api.metriport.com/medical/v1"
    METRIPORT_FACILITY_ID: str = ""
    METRIPORT_WEBHOOK_SECRET: str = ""
    
    SPACES_ENDPOINT: Optional[str] = None
    SPACES_REGION: Optional[str] = None
    SPACES_BUCKET: Optional[str] = None
    SPACES_ACCESS_KEY: Optional[str] = None
    SPACES_SECRET_KEY: Optional[str] = None
    SPACES_CDN_ENDPOINT: Optional[str] = None
    
    # Telnyx Configuration (Phone + Fax)
    TELNYX_API_KEY: str = ""
    TELNYX_FROM_NUMBER: str = ""
    TELNYX_FAX_FROM_NUMBER: Optional[str] = None
    TELNYX_FAX_CONNECTION_ID: Optional[str] = None
    TELNYX_FAX_WEBHOOK_URL: Optional[str] = None
    TELNYX_MESSAGING_PROFILE_ID: Optional[str] = None
    TELNYX_PUBLIC_KEY: Optional[str] = None
    TELNYX_REQUIRE_SIGNATURE: bool = False
    TELNYX_ENABLED: bool = True
    TELNYX_TRANSFER_NUMBER: Optional[str] = None  # For IVR "speak to someone" (e.g. queue or main line)
    TELNYX_CONNECTION_ID: Optional[str] = None  # For voice/fax outbound (fallback if TELNYX_FAX_CONNECTION_ID not set)
    APP_BASE_URL: Optional[str] = None  # Used for TeXML action URLs and patient portal links

    # Facesheet request: optional URL to a PDF template sent when requesting facesheet from facility via fax
    FACESHEET_REQUEST_FAX_MEDIA_URL: Optional[str] = None
    # Optional TeXML/IVR URL when facility answers the facesheet request call (POST /api/billing/facesheet/place-call)
    FACESHEET_REQUEST_CALL_ANSWER_URL: Optional[str] = None

    # Ollama (AI biller helper, IVR voice agent, billing explain/chat)
    OLLAMA_SERVER_URL: str = "http://localhost:11434"
    OLLAMA_IVR_MODEL: str = "llama3.2"  # Conversational, human-like for phone
    OLLAMA_ENABLED: bool = True  # Solo biller: AI does as much as possible; set False to disable

    # Optional: secret for cron to trigger send-test without session (e.g. EMAIL_TEST_CRON_SECRET=your-secret)
    EMAIL_TEST_CRON_SECRET: Optional[str] = None

    # Terminology / reference datasets (builder health checks; set when loaded or API available)
    SNOMED_API_URL: Optional[str] = None
    SNOMED_DATASET_LOADED: bool = False
    ICD10_API_URL: Optional[str] = None
    ICD10_DATASET_LOADED: bool = False
    RXNORM_API_URL: Optional[str] = None
    RXNORM_DATASET_LOADED: bool = False

    # Billing: optional auto-create claim when ePCR finalized and ready-check passes (per-org config in DB later)
    AUTO_CLAIM_AFTER_FINALIZE: bool = False

    # NEMSIS state submission (Wisconsin-first for certification)
    NEMSIS_STATE_CODES: Optional[str] = "WI"  # Default WI; e.g. "WI,IL,MN"
    NEMSIS_STATE_ENDPOINTS: Optional[str] = None  # JSON: {"WI": "https://...", "IL": "https://..."}
    WISCONSIN_NEMSIS_ENDPOINT: Optional[str] = None  # Wisconsin EMS submission URL when provided

    # NEMSIS version watch: notify when NEMSIS standard is updated
    NEMSIS_CURRENT_VERSION: str = "3.5.1"  # Version we support; watch compares to this / fetched version
    NEMSIS_VERSION_CHECK_URL: Optional[str] = None  # If set, GET and parse for 3.x.y; default uses nemsis.org
    NEMSIS_WATCH_CRON_SECRET: Optional[str] = None  # Cron: POST /api/cron/nemsis-watch with X-Cron-Secret

    # Postmark (optional; primary email is SMTP/IMAP / Mailu)
    POSTMARK_SERVER_TOKEN: Optional[str] = None
    POSTMARK_ACCOUNT_TOKEN: Optional[str] = None
    POSTMARK_FROM_EMAIL: Optional[str] = None
    
    # Lob (Physical Mail - Paper Statements)
    LOB_API_KEY: Optional[str] = None
    LOB_FROM_ADDRESS_NAME: str = "Fusion EMS Billing"
    LOB_FROM_ADDRESS_LINE1: Optional[str] = None
    LOB_FROM_ADDRESS_CITY: Optional[str] = None
    LOB_FROM_ADDRESS_STATE: Optional[str] = None
    LOB_FROM_ADDRESS_ZIP: Optional[str] = None
    LOB_ENABLED: bool = False

    model_config = SettingsConfigDict(
        extra="allow",
        env_file=".env",
        env_file_encoding="utf-8"
    )

settings = Settings()

# Known insecure default values that should NEVER be used in production
_INSECURE_DEFAULTS = {
    "JWT_SECRET_KEY": {"dev-secret", "secret", "change-me", "changeme", "your-secret-key"},
    "STORAGE_ENCRYPTION_KEY": {"dev-storage", "storage", "change-me", "changeme"},
    "DOCS_ENCRYPTION_KEY": {"dev-docs", "docs", "change-me", "changeme"},
    "CAD_BACKEND_AUTH_TOKEN": {"fastapi-bridge-secure-token-change-in-production", "change-me", "changeme"},
}

def validate_settings_runtime(_settings: Optional[Settings] = None) -> None:
    """
    Validate settings at runtime. In production, ensures:
    1. Required secrets are present
    2. Secrets are not using known insecure default values
    3. Secrets meet minimum length requirements
    """
    s = _settings or settings
    
    if s.ENV == "production":
        errors = []
        
        # Check required settings are present
        required_keys = [
            "DATABASE_URL",
            "JWT_SECRET_KEY",
            "STORAGE_ENCRYPTION_KEY",
            "DOCS_ENCRYPTION_KEY",
        ]
        
        for key in required_keys:
            value = getattr(s, key, None)
            if not value:
                errors.append(f"{key} is required in production")
                continue
            
            # Check for insecure defaults
            insecure_values = _INSECURE_DEFAULTS.get(key, set())
            if value.lower() in {v.lower() for v in insecure_values}:
                errors.append(f"{key} is using an insecure default value - please set a secure secret")
            
            # Check minimum length for secret keys (at least 32 characters recommended)
            if key in {"JWT_SECRET_KEY", "STORAGE_ENCRYPTION_KEY", "DOCS_ENCRYPTION_KEY"}:
                if len(value) < 32:
                    errors.append(f"{key} should be at least 32 characters for security (currently {len(value)})")
        
        # Check CAD_BACKEND_AUTH_TOKEN if CAD is being used
        if s.CAD_BACKEND_URL and s.CAD_BACKEND_URL != "http://localhost:3000":
            token = s.CAD_BACKEND_AUTH_TOKEN
            insecure_tokens = _INSECURE_DEFAULTS.get("CAD_BACKEND_AUTH_TOKEN", set())
            if token.lower() in {v.lower() for v in insecure_tokens}:
                errors.append("CAD_BACKEND_AUTH_TOKEN is using an insecure default value")
        
        # Check database URL isn't SQLite in production
        if s.DATABASE_URL.startswith("sqlite"):
            errors.append("SQLite is not recommended for production - use PostgreSQL")
        
        if errors:
            raise RuntimeError(
                f"Production configuration errors:\n" + 
                "\n".join(f"  - {e}" for e in errors)
            )
