import os
import importlib
from dotenv import load_dotenv

from app.core.db.enums import AyanamsaMode

load_dotenv()

PROVIDER_MAP = {
    "stub": "app.core.astro.providers.stub_provider.StubProvider",
    "swisseph": "app.core.astro.providers.swisseph_provider.SwissEphemProvider",
    "skyfield": "app.core.astro.providers.skyfield_provider.SkyfieldProvider",
}

_provider_instances = {}

def get_provider(name: str = None, ayanamsa_mode: AyanamsaMode = AyanamsaMode.lahiri, fresh: bool = False):
    """Factory for astro provider based on .env or explicit name."""
    provider_name = (name or os.getenv("ASTRO_PROVIDER", "swisseph")).lower()
    if provider_name not in PROVIDER_MAP:
        raise ValueError(f"Unknown astro provider: {provider_name}")
    if fresh or provider_name not in _provider_instances:
        module_path, class_name = PROVIDER_MAP[provider_name].rsplit(".", 1)
        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)
        _provider_instances[provider_name] = cls(ayanamsa_mode=ayanamsa_mode)
    return _provider_instances[provider_name]
