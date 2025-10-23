import os
import importlib
from dotenv import load_dotenv

load_dotenv()

PROVIDER_MAP = {
    "stub": "app.core.astro.providers.stub_provider.StubProvider",
    "swisseph": "app.core.astro.providers.swisseph_provider.SwissEphemProvider",
    "skyfield": "app.core.astro.providers.skyfield_provider.SkyfieldProvider",
}


def get_provider(name: str = None):
    """Factory for astro provider based on .env or explicit name."""
    provider_name = (name or os.getenv("ASTRO_PROVIDER", "swisseph")).lower()
    if provider_name not in PROVIDER_MAP:
        raise ValueError(f"Unknown astro provider: {provider_name}")

    module_path, class_name = PROVIDER_MAP[provider_name].rsplit(".", 1)
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    return cls()  # always no-arg; provider reads .env itself
