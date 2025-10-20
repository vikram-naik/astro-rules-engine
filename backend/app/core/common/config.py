# backend/app/core/common/config.py
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict

class Settings(BaseSettings):
    """
    Global application configuration.
    Pydantic v2-compatible using ConfigDict instead of inner Config class.
    """

    # --- Database & Logging ---
    database_url: str = Field(default="sqlite:///./astro_rules.db", description="SQLAlchemy database URL")
    log_level: str = Field(default="INFO", description="Logging level")

    # --- Providers ---
    provider_type: str = Field(default="swisseph", description="Astrology provider type (stub|swisseph|skyfield)")
    market_provider_type: str = Field(default="yahoo", description="Market data provider type (yahoo|csv)")

    # --- Defaults ---
    default_sector_ticker: str = Field(default="^GSPC", description="Default market index ticker")

    # --- ConfigDict replaces old Config class ---
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

# singleton instance
settings = Settings()
