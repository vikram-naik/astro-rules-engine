from app.core.market.factories.provider_factory import get_market_provider
from app.core.market.interfaces.i_market_data_provider import IMarketDataProvider
from datetime import date

def test_yahoo_provider_instantiation():
    provider = get_market_provider("yahoo")
    assert isinstance(provider, IMarketDataProvider)
    df = provider.fetch_data("^NSEI", start=date(2024,1,1), end=date(2024,1,10))
    assert isinstance(df, type(provider.fetch_data("^NSEI", start=date(2024,1,1), end=date(2024,1,10))))
    assert hasattr(provider, "compute_return")

def test_csv_provider_instantiation(tmp_path):
    provider = get_market_provider("csv")
    assert isinstance(provider, IMarketDataProvider)
