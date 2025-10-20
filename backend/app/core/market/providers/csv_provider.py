import pandas as pd
from datetime import date
import os
import logging
from core.market.interfaces.i_market_data_provider import IMarketDataProvider

logger = logging.getLogger("astro.market.csv")

class CSVMarketDataProvider(IMarketDataProvider):
    """Local CSV-based market data provider."""

    def __init__(self, data_dir: str = "./data_cache"):
        self.data_dir = data_dir

    def fetch_data(self, ticker: str, start: date, end: date) -> pd.DataFrame:
        file_path = os.path.join(self.data_dir, f"{ticker.replace('^','')}.csv")
        if not os.path.exists(file_path):
            logger.warning(f"No CSV found for {ticker}")
            return pd.DataFrame()
        df = pd.read_csv(file_path, parse_dates=["Date"], index_col="Date")
        return df.loc[str(start):str(end)]

    def compute_return(self, df: pd.DataFrame, start: date, end: date) -> float:
        if df.empty or len(df) < 2:
            return 0.0
        return (df["Adj Close"].iloc[-1] / df["Adj Close"].iloc[0]) - 1.0
