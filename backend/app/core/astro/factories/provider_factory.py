import importlib
import logging
from typing import Type
from app.core.astro.interfaces.i_astro_provider import IAstroProvider

logger = logging.getLogger("astro.factory")

# Mapping of short names to fully qualified provider classes
PROVIDER_MAP = {
    "stub": "app.core.astro.providers.stub_provider.StubProvider",
    "swisseph": "app.core.astro.providers.swisseph_provider.SwissEphemProvider",
    # add others like "skyfield": "core.providers.skyfield_provider.SkyfieldProvider"
}

def get_provider(provider_type: str = "stub") -> IAstroProvider:
    """
    Dynamically import and instantiate an astro provider class.

    Args:
        provider_type: key defined in PROVIDER_MAP (default: "stub")

    Returns:
        IAstroProvider instance

    Raises:
        ImportError, AttributeError, ValueError
    """
    provider_type = (provider_type or "stub").lower()
    if provider_type not in PROVIDER_MAP:
        raise ValueError(f"Unknown provider type: {provider_type}. "
                         f"Must be one of {list(PROVIDER_MAP.keys())}")

    fqcn = PROVIDER_MAP[provider_type]
    module_name, class_name = fqcn.rsplit(".", 1)

    try:
        module = importlib.import_module(module_name)
        cls: Type[IAstroProvider] = getattr(module, class_name)
        instance = cls()
        logger.info(f"✅ Loaded provider: {fqcn}")
        return instance
    except Exception as e:
        logger.exception(f"Failed to load provider {fqcn}: {e}")
        raise
