from abc import ABC, abstractmethod
from datetime import date
import pandas as pd

class IMarketDataProvider(ABC):
    """Interface defining how market data providers fetch and return sector data."""

    @abstractmethod
    def fetch_data(self, ticker: str, start: date, end: date) -> pd.DataFrame:
        """Return daily market data (at least 'Adj Close' column)."""
        raise NotImplementedError

    @abstractmethod
    def compute_return(self, df: pd.DataFrame, start: date, end: date) -> float:
        """Compute % return between two dates."""
        raise NotImplementedError
