import importlib
import logging
from typing import Type
from app.core.market.interfaces.i_market_data_provider import IMarketDataProvider

logger = logging.getLogger("astro.market.factory")

PROVIDER_MAP = {
    "yahoo": "app.core.market.providers.yahoo_provider.YahooMarketDataProvider",
    "csv": "app.core.market.providers.csv_provider.CSVMarketDataProvider",
}

def get_market_provider(provider_type: str = "yahoo") -> IMarketDataProvider:
    provider_type = (provider_type or "yahoo").lower()
    if provider_type not in PROVIDER_MAP:
        raise ValueError(f"Unknown market provider type: {provider_type}")

    fqcn = PROVIDER_MAP[provider_type]
    module_name, class_name = fqcn.rsplit(".", 1)

    try:
        module = importlib.import_module(module_name)
        cls: Type[IMarketDataProvider] = getattr(module, class_name)
        instance = cls()
        logger.info(f"✅ Loaded market provider: {fqcn}")
        return instance
    except Exception as e:
        logger.exception(f"Failed to load market provider {fqcn}: {e}")
        raise
