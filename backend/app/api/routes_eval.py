# backend/app/api/routes_eval.py
"""
Evaluation API
--------------
Evaluate all active rules over a date range and return triggered events.
"""

from fastapi import APIRouter, HTTPException
from app.core.services.evaluation_service import evaluate_rules_for_range
from app.core.common.schemas import EvaluateRequest
from app.core.common.logger import setup_logger
from app.core.common.config import settings

logger = setup_logger(settings.log_level)

router = APIRouter(prefix="/evaluate", tags=["evaluation"])


@router.post("/", summary="Evaluate all active rules over a date range")
def evaluate(req: EvaluateRequest):
    """
    Evaluate all enabled astrological rules between start_date and end_date.
    Returns a list of triggered events per rule per date.
    """
    try:
        events = evaluate_rules_for_range(req.start_date, req.end_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Evaluation failed")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {e}")

    if not events:
        return {"message": "No events found for given date range", "count": 0, "events": []}

    logger.info(f"Evaluated {len(events)} events from {req.start_date} to {req.end_date}")
    return {"count": len(events), "events": events}
