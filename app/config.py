from pydantic_settings import BaseSettings
from functools import lru_cache
from urllib.parse import quote_plus


class Settings(BaseSettings):
    # Database — individual components
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "job_agent"
    db_user: str = "postgres"
    db_password: str = "1234"
    db_type: str = "postgresql"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    # App
    secret_key: str = "change-this-secret-key-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Job scraping (optional)
    serpapi_key: str = ""

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
    return Settings()


settings = get_settings()
