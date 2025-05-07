import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class Settings:
    PROJECT_NAME: str = "WNBA Fantasy League"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey")
    AUTH_MODE: str = os.getenv("AUTH_MODE", "jwt")  # "jwt" or "cookie"

    # 30 days * 24 hours * 60 minutes * 60 seconds
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 30 * 24 * 60 * 60

    # Database
    SQLALCHEMY_DATABASE_URI: Optional[str] = os.getenv("DATABASE_URL", "sqlite:///./prod.db")
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://")


settings = Settings()
