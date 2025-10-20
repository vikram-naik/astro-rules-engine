import yfinance as yf
import pandas as pd
from datetime import date
import logging
import os
from app.core.market.interfaces.i_market_data_provider import IMarketDataProvider

logger = logging.getLogger("astro.market.yahoo")

class YahooMarketDataProvider(IMarketDataProvider):
    """Fetch market data using Yahoo Finance with caching support."""

    def __init__(self, cache_dir: str = "./data_cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def fetch_data(self, ticker: str, start: date, end: date) -> pd.DataFrame:
        cache_file = os.path.join(self.cache_dir, f"{ticker.replace('^','')}.csv")

        if os.path.exists(cache_file):
            df = pd.read_csv(cache_file, parse_dates=["Date"], index_col="Date")
            logger.info(f"Loaded cached market data: {ticker}")
        else:
            logger.info(f"Fetching {ticker} from Yahoo Finance...")
            data = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)

            if isinstance(data.columns, pd.MultiIndex):
                df = data.xs("Close", axis=1, level=0, drop_level=False)
                df.columns = ["Adj Close"]
            else:
                if "Adj Close" in data.columns:
                    df = data[["Adj Close"]].copy()
                elif "Close" in data.columns:
                    df = data[["Close"]].rename(columns={"Close": "Adj Close"})
                else:
                    raise KeyError("No valid price column found.")

            df.to_csv(cache_file)
        return df

    def compute_return(self, df: pd.DataFrame, start: date, end: date) -> float:
        df = df.loc[str(start):str(end)]
        if len(df) < 2:
            return 0.0
        return (df["Adj Close"].iloc[-1] / df["Adj Close"].iloc[0]) - 1.0
