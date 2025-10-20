from core.market_data import MarketDataProvider
from datetime import date

def test_market_data_fetch(monkeypatch):
    provider = MarketDataProvider()
    df = provider.fetch_sector_data("^NSEI", start=date(2024,1,1), end=date(2024,1,10))
    assert not df.empty