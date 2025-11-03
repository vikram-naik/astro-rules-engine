# backend/app/core/common/config.py
import json
import logging
from typing import Any, Dict, Optional
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict, field_validator

logger = logging.getLogger(__name__)

# --- Default ORB values for planetary pairings ---
DEFAULT_ORB_OVERRIDES = {
    "sun-moon": 12.0,
    "moon-mercury": 9.0,
    "moon-venus": 8.0,
    "moon-mars": 8.0,
    "moon-jupiter": 10.0,
    "moon-saturn": 9.0,
    "mercury-venus": 7.0,
    "mercury-mars": 6.0,
    "venus-mars": 6.0,
    "mars-jupiter": 7.0,
    "jupiter-saturn": 6.0,
    "mars-saturn": 5.0,
    "mars-ketu": 4.0,
    "mars-rahu": 5.0,
    "saturn-ketu": 5.0,
    "saturn-rahu": 6.0,
    "rahu-ketu": 5.0,
    "sun-mercury": 10.0,
    "sun-venus": 10.0,
}


class Settings(BaseSettings):
    """
    Global application configuration.
    """

    # --- Database & Logging ---
    database_url: str = Field(default="sqlite:///./astro_rules.db", description="SQLAlchemy database URL")
    log_level: str = Field(default="INFO", description="Logging level")

    # --- Providers ---
    provider_type: str = Field(default="swisseph", description="Astrology provider type (stub|swisseph|skyfield)")
    market_provider_type: str = Field(default="yahoo", description="Market data provider type (yahoo|csv)")

    # --- Defaults ---
    default_sector_ticker: str = Field(default="^GSPC", description="Default market index ticker")

    # --- Orbs ---
    orb_default: float = Field(default=7.0, description="Default degree orb for aspects and conjunctions")
    orb_overrides: Optional[Dict[str, float]] = None
    orb_overrides_file: Optional[str] = Field(default=None, description="Path to external orb overrides JSON file")

    # --- Combust configuration ---
    astro_combust_orbs: Optional[Dict[str, float]] = None

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")


    # --- Validators ---
    @field_validator("astro_combust_orbs", mode="before")
    def _parse_astro_combust_orbs(cls, v: Any) -> Dict[str, float]:
        """
        Accepts dict or JSON string; skips invalid entries instead of failing validation.
        """
        if v is None:
            return {}

        # Case 1: dict
        if isinstance(v, dict):
            out: Dict[str, float] = {}
            for k, val in v.items():
                try:
                    out[str(k).lower()] = float(val)
                except Exception:
                    logger.warning("Ignoring invalid combust orb value for %s: %r", k, val)
            return out

        # Case 2: JSON string
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, dict):
                    out: Dict[str, float] = {}
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

        # Case 3: unsupported type
        logger.warning("astro_combust_orbs provided in unsupported format: %r", v)
        return {}


    @field_validator("orb_overrides", mode="before")
    def _parse_orb_overrides(cls, v: Any) -> Dict[str, float]:
        if v is None:
            return {}
        if isinstance(v, dict):
            return {k.lower(): float(val) for k, val in v.items()}
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                return {k.lower(): float(val) for k, val in parsed.items()}
            except Exception as exc:
                logger.warning("Invalid orb_overrides JSON: %s (%s)", v, exc)
                return {}
        return {}


# --- Singleton instance and loader ---
settings = Settings()

# --- Astro default reference time ---
DEFAULT_REFERENCE_TIME = getattr(settings, "ASTRO_DEFAULT_REFERENCE_TIME", "00:00:00")

# Handle external orb JSON if defined
if settings.orb_overrides_file:
    orb_path = Path(settings.orb_overrides_file).expanduser()
    if orb_path.exists():
        try:
            with open(orb_path, "r", encoding="utf-8") as fh:
                file_data = json.load(fh)
                if isinstance(file_data, dict):
                    logger.info("Loaded ORB overrides from file: %s", orb_path)
                    settings.orb_overrides = {k.lower(): float(v) for k, v in file_data.items()}
        except Exception as exc:
            logger.error("Failed to load orb overrides file %s: %s", orb_path, exc)
    else:
        logger.warning("orb_overrides_file specified but not found: %s", orb_path)

# Fallback to defaults if nothing provided
if not settings.orb_overrides:
    settings.orb_overrides = DEFAULT_ORB_OVERRIDES

