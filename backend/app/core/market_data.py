import yfinance as yf
import pandas as pd
from datetime import date
import logging
import os

logger = logging.getLogger("astro.market")

class MarketDataProvider:
    def __init__(self, cache_dir: str = "./data_cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def fetch_sector_data(self, ticker: str, start: date, end: date) -> pd.DataFrame:
        """Fetch market data for a ticker from Yahoo Finance or cache."""
        cache_file = os.path.join(self.cache_dir, f"{ticker.replace('^','')}.csv")
        if os.path.exists(cache_file):
            df = pd.read_csv(cache_file, parse_dates=["Date"], index_col="Date")
            logger.info(f"Loaded cached market data: {ticker}")
        else:
            logger.info(f"Fetching {ticker} data from Yahoo Finance…")
            data = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)

            # Handle MultiIndex (e.g., NSE tickers)
            if isinstance(data.columns, pd.MultiIndex):
                close_col = ("Close", ticker)
                if close_col in data.columns:
                    df = data[[close_col]].copy()
                    df.columns = ["Adj Close"]
                elif ("Close", '') in data.columns:
                    df = data[[('Close', '')]].copy()
                    df.columns = ["Adj Close"]
                else:
                    df = data.xs("Close", axis=1, level=0, drop_level=False)
                    df.columns = ["Adj Close"]
            else:
                if "Adj Close" in data.columns:
                    df = data[["Adj Close"]].copy()
                elif "Close" in data.columns:
                    df = data[["Close"]].rename(columns={"Close": "Adj Close"})
                else:
                    raise KeyError(f"No valid price column found for {ticker}")

            df.to_csv(cache_file)

        # basic validation
        if df.empty or df.isna().all().values[0]:
            logger.warning(f"No valid price data returned for {ticker}")
        return df

    def compute_return_window(self, df: pd.DataFrame, start: date, end: date) -> float:
        """Compute % change between start and end."""
        if df.empty:
            return 0.0
        df = df.loc[str(start):str(end)]
        if len(df) < 2:
            return 0.0
        return (df["Adj Close"].iloc[-1] / df["Adj Close"].iloc[0]) - 1.0