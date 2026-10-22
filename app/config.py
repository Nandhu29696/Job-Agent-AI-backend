from pydantic_settings import BaseSettings
from functools import lru_cache
from urllib.parse import quote_plus
import logging

logger = logging.getLogger("job_agent")


class Settings(BaseSettings):
    # App
    app_env: str = "development"  # development | production
    frontend_url: str = "http://localhost:5173"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    # Promoted to super_admin on startup if no super admin exists yet
    super_admin_email: str = ""

    # Database — individual components
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "job_agent"
    db_user: str = "postgres"
    db_password: str = "1234"
    db_type: str = "postgresql"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:latest"
    ollama_timeout_seconds: int = 120

    # Security / JWT
    secret_key: str = "change-this-secret-key-in-production"
    algorithm: str = "HS256"
    jwt_access_minutes: int = 15
    jwt_refresh_minutes: int = 60 * 24 * 7
    cookie_secure: bool = False  # set True behind HTTPS
    max_failed_logins: int = 5
    lockout_minutes: int = 15

    # Google OAuth2 (the .env uses GMAIL_* names)
    gmail_client_id: str = ""
    gmail_client_secret: str = ""
    gmail_redirect_uri: str = "http://localhost:8000/api/integrations/gmail/callback"

    # Email (SMTP)
    email_host: str = ""
    email_port: int = 587
    email_host_user: str = ""
    email_host_password: str = ""
    email_use_tls: bool = True
    default_from_email: str = ""

    # OTP
    otp_expiry_seconds: int = 300
    otp_length: int = 6
    otp_max_attempts: int = 5
    otp_resend_cooldown_seconds: int = 60

    # Razorpay
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""
    currency: str = "INR"

    # Monetisation defaults (super admin can override at runtime via app_settings)
    pro_plan_price_paise: int = 29900
    pro_plan_days: int = 30
    free_daily_ai_limit: int = 15

    # Job scraping (optional)
    serpapi_key: str = ""

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def google_enabled(self) -> bool:
        return bool(self.gmail_client_id and self.gmail_client_secret)

    @property
    def razorpay_enabled(self) -> bool:
        return bool(self.razorpay_key_id and self.razorpay_key_secret)

    @property
    def smtp_enabled(self) -> bool:
        return bool(self.email_host and self.email_host_user and self.email_host_password)

    @property
    def database_url(self) -> str:
        db_type = (self.db_type or "postgresql").strip().lower()
        user = quote_plus(self.db_user)
        password = quote_plus(self.db_password)

        if db_type in ("postgres", "postgresql"):
            return (
                f"postgresql+asyncpg://{user}:{password}@"
                f"{self.db_host}:{self.db_port}/{self.db_name}"
            )

        if db_type in ("mysql", "mariadb"):
            return (
                f"mysql+asyncmy://{user}:{password}@"
                f"{self.db_host}:{self.db_port}/{self.db_name}"
            )

        raise ValueError(
            "Unsupported DB_TYPE. Use one of: postgresql, postgres, mysql, mariadb"
        )

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    s = Settings()
    if s.secret_key.startswith("change-this") or len(s.secret_key) < 32:
        msg = "SECRET_KEY is weak or default — set a long random value in .env"
        if s.is_production:
            raise RuntimeError(msg)
        logger.warning(msg)
    return s


settings = get_settings()
