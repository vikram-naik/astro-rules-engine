# backend/app/core/analysis/correlation_analyzer.py
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from app.core.market.factories.provider_factory import get_market_provider
from app.core.common.config import settings
from app.core.common.logger import setup_logger

logger = setup_logger(settings.log_level)


def _compute_horizon_return_from_df(df: pd.DataFrame, entry_date: date, horizon: int) -> Optional[float]:
    """
    Given a DataFrame indexed by dates and an entry_date, return % change between entry row and row at horizon days later.
    If insufficient data, returns None.
    """
    if df is None or df.empty:
        return None

    # ensure index is datetime and sorted
    df = df.sort_index()
    # find first index >= entry_date
    idx = df.index
    # use string slice in case index contains times
    try:
        window = df.loc[str(entry_date):]
    except Exception:
        window = df[df.index >= pd.to_datetime(entry_date)]

    if window.empty:
        return None
    # entry price is first available on or after entry_date
    entry_price = window["Adj Close"].iloc[0]
    # need horizon-th subsequent row (horizon=1 => next trading day)
    if len(window) <= horizon:
        return None
    exit_price = window["Adj Close"].iloc[horizon]
    return (exit_price / entry_price) - 1.0


def analyze_correlation(events: List[Dict[str, Any]],
                        ticker: str,
                        lookahead_days: List[int] = [1, 3, 5],
                        market_provider_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Compute per-rule and aggregate statistics for each lookahead horizon.

    Returns:
      {
        "ticker": ticker,
        "lookahead_days": [...],
        "per_rule": { rule_id: { "name":..., "count":n, "stats": {h: {...}} } },
        "aggregate": { h: {...} }
      }
    """
    if market_provider_type is None:
        market_provider_type = settings.market_provider_type

    provider = get_market_provider(market_provider_type)

    # prepare dates span to fetch price series once (min start to max needed)
    # gather entry dates
    entry_dates = [datetime.fromisoformat(e["date"]).date() for e in events] if events else []
    if not entry_dates:
        return {"ticker": ticker, "lookahead_days": lookahead_days, "per_rule": {}, "aggregate": {}}

    min_date = min(entry_dates)
    max_date = max(entry_dates)
    max_h = max(lookahead_days)
    # fetch price data with a margin of some days
    try:
        prices_df = provider.fetch_data(ticker, min_date, max_date + timedelta(days=max_h + 10))
    except Exception as ex:
        logger.error(f"Failed to fetch market data for {ticker}: {ex}")
        raise

    # group events by rule_id
    per_rule_events: Dict[str, List[Dict[str, Any]]] = {}
    for ev in events:
        rid = ev.get("rule_id")
        per_rule_events.setdefault(rid, []).append(ev)

    per_rule_results: Dict[str, Any] = {}
    # Collect aggregate directional returns across all rules for each horizon
    aggregate_collection: Dict[int, List[float]] = {h: [] for h in lookahead_days}

    for rid, evs in per_rule_events.items():
        name = evs[0].get("name") or rid
        records = []
        for ev in evs:
            entry_date = datetime.fromisoformat(ev["date"]).date()
            direction = 1 if (ev.get("effect", "").lower() == "bullish") else -1
            weight = float(ev.get("weight", 1.0)) * float(ev.get("confidence", 1.0))
            rec = {"entry_date": entry_date, "direction": direction, "weight": weight}
            for h in lookahead_days:
                r = _compute_horizon_return_from_df(prices_df, entry_date, h)
                rec[f"ret_{h}d"] = r
                rec[f"dir_ret_{h}d"] = (r * direction) if r is not None else None
                if r is not None:
                    aggregate_collection[h].append(rec[f"dir_ret_{h}d"])
            records.append(rec)

        # compute stats for this rule, per horizon
        stats_for_rule = {}
        df = pd.DataFrame(records)
        for h in lookahead_days:
            col = f"dir_ret_{h}d"
            if col in df.columns:
                valid = df[col].dropna()
                count = int(valid.count())
                if count == 0:
                    stats_for_rule[h] = {"count": 0}
                else:
                    stats_for_rule[h] = {
                        "count": count,
                        "hit_rate": float((valid > 0).sum() / count),
                        "avg_return": float(valid.mean()),
                        "median_return": float(valid.median()),
                        "std_return": float(valid.std(ddof=0))
                    }
            else:
                stats_for_rule[h] = {"count": 0}
        per_rule_results[rid] = {"name": name, "count": len(records), "records": records, "stats": stats_for_rule}

    # aggregate stats across all rules
    aggregate_stats = {}
    for h in lookahead_days:
        arr = np.array(aggregate_collection.get(h, []), dtype=float)
        if arr.size == 0:
            aggregate_stats[h] = {"count": 0}
        else:
            aggregate_stats[h] = {
                "count": int(arr.size),
                "hit_rate": float((arr > 0).sum() / arr.size),
                "avg_return": float(arr.mean()),
                "median_return": float(np.median(arr)),
                "std_return": float(arr.std(ddof=0))
            }

    return {
        "ticker": ticker,
        "lookahead_days": lookahead_days,
        "per_rule": per_rule_results,
        "aggregate": aggregate_stats
    }
