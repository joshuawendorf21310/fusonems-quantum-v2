from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = Field("FusonEMS Quantum", env="PROJECT_NAME")
    DATABASE_URL: str = Field("postgresql://admin:securepass@localhost:5432/fusonems", env="DATABASE_URL")
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
