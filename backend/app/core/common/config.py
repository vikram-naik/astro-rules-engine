# backend/app/core/common/config.py
import json
import logging
from typing import Any, Dict, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict, field_validator

logger = logging.getLogger(__name__)

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

    # New typed setting: user may provide JSON in .env or a dict programmatically
    astro_combust_orbs: Optional[Dict[str, float]] = None

    # --- ConfigDict replaces old Config class ---
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", extra='allow')    

    @field_validator("astro_combust_orbs", mode="before")
    def _parse_astro_combust_orbs(cls, v: Any) -> Dict[str, float]:
        """
        Accept:
          - None -> {}
          - dict -> normalize keys to lowercase and float values
          - JSON string -> parse then normalize
        Return: dict[str, float]
        """
        if v is None:
            return {}
        # already a dict -> normalize
        if isinstance(v, dict):
            out: Dict[str, float] = {}
            for k, val in v.items():
                try:
                    out[str(k).lower()] = float(val)
                except Exception:
                    logger.warning("Ignoring invalid combust orb value for %s: %r", k, val)
            return out

        # if it's a string: try JSON parse
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, dict):
                    out = {}
                    for k, val in parsed.items():
                        try:
                            out[str(k).lower()] = float(val)
                        except Exception:
                            logger.warning("Ignoring invalid combust orb JSON value for %s: %r", k, val)
                    return out
            except json.JSONDecodeError:
                logger.warning("astro_combust_orbs env var is not valid JSON: %r", v)
                return {}
            except Exception as exc:
                logger.exception("Error parsing astro_combust_orbs: %s", exc)
                return {}

        # otherwise return empty mapping
        logger.warning("astro_combust_orbs provided in unsupported format: %r", v)
        return {}


# singleton instance
settings = Settings()
