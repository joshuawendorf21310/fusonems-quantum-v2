from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = Field("FusonEMS Quantum", env="PROJECT_NAME")
    DATABASE_URL: str = Field("postgresql://admin:securepass@localhost:5432/fusonems", env="DATABASE_URL")
    ALLOWED_ORIGINS: str = Field("http://localhost:5173", env="ALLOWED_ORIGINS")
    JWT_SECRET_KEY: str = Field("change-me", env="JWT_SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(60, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    ENV: str = Field("development", env="ENV")
    DB_POOL_SIZE: int = Field(5, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(10, env="DB_MAX_OVERFLOW")
    TELNYX_API_KEY: str = Field("", env="TELNYX_API_KEY")
    TELNYX_NUMBER: str = Field("", env="TELNYX_NUMBER")
    TELNYX_CONNECTION_ID: str = Field("", env="TELNYX_CONNECTION_ID")
    TELNYX_MESSAGING_PROFILE_ID: str = Field("", env="TELNYX_MESSAGING_PROFILE_ID")
    LOB_API_KEY: str = Field("", env="test_70d390fbc9629f40ff55bcb47369fde2b18")
    OFFICEALLY_FTP_HOST: str = Field("", env="OFFICEALLY_FTP_HOST")
    OFFICEALLY_FTP_USER: str = Field("", env="OFFICEALLY_FTP_USER")
    OFFICEALLY_FTP_PASSWORD: str = Field("", env="OFFICEALLY_FTP_PASSWORD")
    OFFICEALLY_FTP_PORT: int = Field(21, env="OFFICEALLY_FTP_PORT")
    STORAGE_ENCRYPTION_KEY: str = Field("change-me", env="STORAGE_ENCRYPTION_KEY")
    TELEHEALTH_DATABASE_URL: str = Field("", env="TELEHEALTH_DATABASE_URL")
    TELEHEALTH_API_KEY: str = Field("", env="TELEHEALTH_API_KEY")
    OPENID_CLIENT_ID: str = Field("", env="OPENID_CLIENT_ID")
    OPENID_SECRET: str = Field("", env="OPENID_SECRET")
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
