"""
AMAN ERP - Configuration Settings
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """إعدادات النظام"""
    
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "aman"
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = "postgres"
    
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"
    
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Admin password hash (bcrypt). Generate with: python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('your_password'))"
    ADMIN_PASSWORD_HASH: Optional[str] = None
    
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    FRONTEND_URL: str = "http://localhost:5173"
    FRONTEND_URL_PRODUCTION: str = ""
    # Comma-separated list of allowed origins for production (overrides FRONTEND_URL_PRODUCTION)
    # e.g. "https://erp.mycompany.com,https://app.mycompany.com"
    ALLOWED_ORIGINS: str = ""
    
    SYSTEM_EMAIL: str = "admin@aman-erp.com"
    MAX_COMPANIES_PER_INSTANCE: int = 1000
    COMPANY_ID_LENGTH: int = 8

    # ── Observability ──────────────────────────────────────────
    APP_ENV: str = "development"          # development | staging | production
    SENTRY_DSN: str = ""                  # Leave empty to disable Sentry
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1

    # ── SEC-008: Validate SECRET_KEY strength ─────────────────
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters long. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        # Check entropy — reject keys that are all the same repeated character or trivially guessable
        unique_chars = len(set(v))
        if unique_chars < 8:
            raise ValueError(
                "SECRET_KEY has insufficient entropy (too many repeated characters). "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        return v
    
    @property
    def DATABASE_URL(self) -> str:
        import urllib.parse
        encoded_password = urllib.parse.quote_plus(self.POSTGRES_PASSWORD)
        return f"postgresql://{self.POSTGRES_USER}:{encoded_password}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    def get_company_database_url(self, company_id: str) -> str:
        import urllib.parse
        encoded_password = urllib.parse.quote_plus(self.POSTGRES_PASSWORD)
        return f"postgresql://{self.POSTGRES_USER}:{encoded_password}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/aman_{company_id}"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


def setup_pgpass():
    """
    SEC-006: Write a .pgpass file so that CLI tools (psql, pg_dump, etc.)
    never need PGPASSWORD in the environment.  File is chmod 0600.
    """
    import os, stat
    pgpass_path = os.path.expanduser("~/.pgpass")
    line = f"{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}:*:{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    
    # Read existing content to avoid duplicates
    existing = ""
    if os.path.exists(pgpass_path):
        with open(pgpass_path, "r") as f:
            existing = f.read()
    
    if line not in existing:
        with open(pgpass_path, "a") as f:
            f.write(line + "\n")
    
    os.chmod(pgpass_path, stat.S_IRUSR | stat.S_IWUSR)  # 0600

    # Remove PGPASSWORD from environment if set (defense-in-depth)
    os.environ.pop("PGPASSWORD", None)


# Run on import
setup_pgpass()
