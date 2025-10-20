# backend/app/api/routes_correlation.py
"""
Correlation Analysis API
------------------------
Runs statistical correlation checks between evaluated astro-rule events
and subsequent market movements.
"""

from fastapi import APIRouter, HTTPException
from app.core.services.evaluation_service import evaluate_rules_for_range
from app.core.analysis.correlation_analyzer import analyze_correlation
from app.core.common.schemas import CorrelationResult
from pydantic import BaseModel, Field
from typing import List, Optional
from app.core.common.logger import setup_logger
from app.core.common.config import settings

logger = setup_logger(settings.log_level)

router = APIRouter(prefix="/correlation", tags=["correlation"])


class CorrelationRequest(BaseModel):
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    ticker: Optional[str] = Field(default=settings.default_sector_ticker)
    lookahead_days: List[int] = Field(default=[1, 3, 5])

    model_config = {"extra": "ignore"}


@router.post("/run", response_model=CorrelationResult)
def run_correlation(req: CorrelationRequest):
    """
    Execute correlation analysis:
    - Evaluate rules for given date range
    - Fetch market data for ticker
    - Compute per-rule and aggregate post-event returns
    """
    try:
        events = evaluate_rules_for_range(req.start_date, req.end_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Rule evaluation failed")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {e}")

    if not events:
        return CorrelationResult(
            ticker=req.ticker,
            lookahead_days=req.lookahead_days,
            per_rule={},
            aggregate={}
        )

    try:
        result = analyze_correlation(events, ticker=req.ticker, lookahead_days=req.lookahead_days)
    except Exception as e:
        logger.exception("Correlation computation failed")
        raise HTTPException(status_code=500, detail=f"Correlation computation failed: {e}")

    return CorrelationResult(**result)
