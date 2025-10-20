from pydantic import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./astro_rules.db"
    log_level: str = "INFO"
    provider_type: str = "swisseph"
    market_provider_type: str = "yahoo"
    default_sector_ticker: str = "^GSPC"

    class Config:
        env_file = ".env"

settings = Settings()
