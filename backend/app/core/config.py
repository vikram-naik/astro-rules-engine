from pydantic import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./astro_rules.db"
    log_level: str = "INFO"
    default_sector_ticker: str = "^GSPC"  # S&P 500

    class Config:
        env_file = ".env"

settings = Settings()