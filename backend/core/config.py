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
    JWT_SECRET_KEY: str = ""  # REQUIRED in production
    STORAGE_ENCRYPTION_KEY: str = ""  # REQUIRED in production
    DOCS_ENCRYPTION_KEY: str = ""  # REQUIRED in production
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
    OFFICEALLY_FTP_HOST: str = ""
    OFFICEALLY_FTP_PORT: int = 22
    OFFICEALLY_FTP_USER: str = ""
    OFFICEALLY_FTP_PASSWORD: str = ""
    OFFICEALLY_SFTP_DIRECTORY: str = "/claims/inbox"
    
    # CAD Backend Socket.io Bridge
    CAD_BACKEND_URL: str = "http://localhost:3000"
    CAD_BACKEND_AUTH_TOKEN: str = ""  # REQUIRED: Set secure token in production
    
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

    # Jitsi Video (Telehealth)
    JITSI_DOMAIN: str = "jitsi.fusionems.com"
    JITSI_APP_ID: str = "fusionems_carefusion"
    JITSI_APP_SECRET: str = ""
    JITSI_JWT_ALGORITHM: str = "HS256"
    
    # Mapbox (Routing)
    MAPBOX_ACCESS_TOKEN: Optional[str] = None
    
    # Redis (Caching, Rate Limiting)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # AI Support
    SUPPORT_AI_ENABLED: bool = False
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama2"
    
    # FIPS 140-2 Compliance (FedRAMP SC-13)
    FIPS_MODE_ENABLED: bool = False  # Set to True to enable FIPS mode
    FIPS_MODE_REQUIRED: bool = False  # Set to True to require FIPS mode (will fail startup if not available)
    
    # Password Policy (FedRAMP IA-5)
    PASSWORD_MIN_LENGTH: int = 14  # Minimum password length
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGITS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    PASSWORD_MAX_AGE_DAYS: int = 90  # Maximum password age before rotation
    
    # Password Hashing
    PASSWORD_HASH_ALGORITHM: str = "auto"  # "auto", "bcrypt", "pbkdf2", "argon2"
    PBKDF2_ITERATIONS: int = 100000  # PBKDF2 iterations (minimum recommended: 100000)
    ARGON2_TIME_COST: int = 2
    ARGON2_MEMORY_COST: int = 65536  # KB
    ARGON2_PARALLELISM: int = 4
    
    # Key Management (FedRAMP SC-12)
    KEY_MANAGEMENT_MASTER_KEY: Optional[str] = None  # Master key for encrypting stored keys
    KEY_ESCROW_LOCATION: Optional[str] = None  # Location for key escrow
    KEY_ROTATION_INTERVAL_DAYS: int = 90  # Default key rotation interval

    model_config = SettingsConfigDict(
        extra="allow",
        env_file=".env",
        env_file_encoding="utf-8"
    )

settings = Settings()

def validate_settings_runtime(_settings: Optional[Settings] = None) -> None:
    s = _settings or settings
    if s.ENV == "production":
        missing = []
        weak = []
        for key in [
            "DATABASE_URL",
            "JWT_SECRET_KEY",
            "STORAGE_ENCRYPTION_KEY",
            "DOCS_ENCRYPTION_KEY",
        ]:
            value = getattr(s, key, None)
            if not value:
                missing.append(key)
            elif key in ["JWT_SECRET_KEY", "STORAGE_ENCRYPTION_KEY", "DOCS_ENCRYPTION_KEY"]:
                # Check for weak/default secrets
                if len(value) < 32 or value in ["dev-secret", "dev-storage", "dev-docs"]:
                    weak.append(f"{key} (must be at least 32 characters)")
        
        if missing:
            raise RuntimeError(f"Missing required production settings: {missing}")
        if weak:
            raise RuntimeError(f"Weak secrets in production: {weak}. Use strong random values.")
    
    # Always validate JWT secret length in any environment
    if settings.JWT_SECRET_KEY and len(settings.JWT_SECRET_KEY) < 16:
        raise RuntimeError("JWT_SECRET_KEY must be at least 16 characters")
