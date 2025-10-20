# backend/app/api/routes_correlation.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
import logging

from app.core.services.evaluation_service import evaluate_rules_for_range
from app.core.analysis.correlation_analyzer import analyze_correlation
from app.core.common.config import settings
from app.core.common.logger import setup_logger

logger = setup_logger(settings.log_level)

router = APIRouter(prefix="/correlation", tags=["correlation"])


class CorrelationRequest(BaseModel):
    start_date: str
    end_date: str
    ticker: Optional[str] = settings.default_sector_ticker
    lookahead_days: Optional[List[int]] = [1, 3, 5]


@router.post("/run")
def run_correlation(req: CorrelationRequest):
    # validate dates (basic)
    try:
        # evaluate_rules_for_range will validate dates as well
        events = evaluate_rules_for_range(req.start_date, req.end_date)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception("Failed to evaluate rules")
        raise HTTPException(status_code=500, detail="Evaluation failed")

    if not events:
        return {"message": "No events produced in the date range", "per_rule": {}, "aggregate": {}}

    try:
        res = analyze_correlation(events, ticker=req.ticker, lookahead_days=req.lookahead_days)
    except Exception as ex:
        logger.exception("Correlation analysis failed")
        raise HTTPException(status_code=500, detail=f"Correlation analysis failed: {ex}")

    return res
