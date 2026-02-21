"""
AMAN ERP - Configuration Settings
"""

from pydantic_settings import BaseSettings
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
