from datetime import date
from app.core.analysis.correlation_analyzer import analyze_correlation

def test_analyze_correlation_basic(monkeypatch):
    """
    Validate correlation analysis using deterministic mock market data.
    """

    # ---- Mock Market Provider ----
    class DummyMarket:
        def fetch_data(self, ticker, start, end):
            import pandas as pd
            import numpy as np
            idx = pd.date_range(start=start, end=end, freq="D")
            # Simple upward trend + 1% per day
            df = pd.DataFrame({"Adj Close": 100 * (1.01) ** np.arange(len(idx))}, index=idx)
            return df

    monkeypatch.setattr("app.core.analysis.correlation_analyzer.get_market_provider", lambda t=None: DummyMarket())

    # ---- Mock Events ----
    events = [
        {
            "rule_id": "R001",
            "name": "Jupiter in Ketu Nakshatra",
            "date": "2025-01-01",
            "effect": "Bullish",
            "weight": 1.0,
            "confidence": 1.0,
        },
        {
            "rule_id": "R001",
            "name": "Jupiter in Ketu Nakshatra",
            "date": "2025-01-03",
            "effect": "Bearish",
            "weight": 1.0,
            "confidence": 1.0,
        },
    ]

    result = analyze_correlation(events, ticker="^DUMMY", lookahead_days=[1, 3])

    assert "per_rule" in result
    assert "aggregate" in result
    rule_data = result["per_rule"]["R001"]["stats"]

    assert rule_data[1]["count"] > 0
    # allow tiny floating-point rounding around zero
    assert rule_data[1]["avg_return"] > -1e-10
    assert result["aggregate"][1]["count"] == 2
