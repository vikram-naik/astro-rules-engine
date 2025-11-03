# app/core/astro/providers/provider_factory.py
import importlib
import logging
from app.core.common.config import settings
from app.core.db.enums import AyanamsaMode

logger = logging.getLogger("astro.factory")

PROVIDER_MAP = {
    "stub": "app.core.astro.providers.stub_provider.StubProvider",
    "swisseph": "app.core.astro.providers.swisseph_provider.SwissEphemProvider",
    "skyfield": "app.core.astro.providers.skyfield_provider.SkyfieldProvider",
}

_provider_instances = {}


def get_provider(
    name: str | None = None,
    ayanamsa_mode: AyanamsaMode = AyanamsaMode.lahiri,
    fresh: bool = False,
    location: dict | None = None,
    tz_name: str | None = None,
):
    """
    Factory for astrology providers.
    - Uses defaults from config.py if not explicitly provided.
    - Providers are cached (singleton style) unless fresh=True.
    - Calls provider.configure() automatically with lon/lat/tz.
    """
    provider_name = (name or settings.provider_type).lower()

    if provider_name not in PROVIDER_MAP:
        raise ValueError(f"Unknown astro provider: {provider_name}")

    # Create or refresh provider instance
    if fresh or provider_name not in _provider_instances:
        module_path, class_name = PROVIDER_MAP[provider_name].rsplit(".", 1)
        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)

        # Instantiate provider (ayanamsa comes from settings if not overridden)
        ayanamsa_mode = ayanamsa_mode or AyanamsaMode(getattr(settings, "astro_ayanamsa_mode", "lahiri").lower())
        instance = cls(ayanamsa_mode=ayanamsa_mode)

        # Configure with location + timezone defaults or overrides
        loc = location or {
            "lon": float(getattr(settings, "ASTRO_LOCATION_LON", 72.8777)),
            "lat": float(getattr(settings, "ASTRO_LOCATION_LAT", 19.0760)),
            "alt": float(getattr(settings, "ASTRO_LOCATION_ALT", 0.0)),
        }
        tz = tz_name or getattr(settings, "ASTRO_TIMEZONE", "Asia/Kolkata")

        if hasattr(instance, "configure"):
            instance.configure(location=loc, tz_name=tz)
            logger.info(f"Configured {provider_name} with {loc} tz={tz}")

        _provider_instances[provider_name] = instance

    return _provider_instances[provider_name]


def clear_providers():
    """Forcefully clear cached provider instances (for testing or reload)."""
    _provider_instances.clear()
    logger.info("Cleared all provider instances.")
