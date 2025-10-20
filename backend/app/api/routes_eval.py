from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
import json
from sqlmodel import select

# --- Common imports
from app.core.common.db import get_session
from app.core.common.config import settings
from app.core.common.logger import setup_logger

# --- ORM Models
from app.core.common.models import RuleModel

# --- Astro & Rules Engine
from app.core.astro.factories.provider_factory import get_provider as get_astro_provider
from app.core.rules.engine.rules_engine_impl import RulesEngineImpl

# --- Market Data
from app.core.market.factories.provider_factory import get_market_provider

# --- Schemas
from app.core.common.schemas import EvaluateRequest, Condition, Outcome, RuleCreate

logger = setup_logger(settings.log_level)

router = APIRouter()

@router.post("/")
def evaluate(req: EvaluateRequest):
    """Run all enabled astro rules for a date range and augment with market returns."""
    try:
        start = datetime.fromisoformat(req.start_date).date()
        end = datetime.fromisoformat(req.end_date).date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    if end < start:
        raise HTTPException(status_code=400, detail="end_date must be >= start_date")

    # --- Load rules from DB
    with get_session() as session:
        models = session.exec(select(RuleModel).where(RuleModel.enabled == True)).all()

    if not models:
        return {"message": "No enabled rules found."}

    # --- Initialize providers
    astro_provider = get_astro_provider(settings.provider_type)
    rules_engine = RulesEngineImpl(astro_provider)
    market_provider = get_market_provider(settings.market_provider_type)

    events = []
    current_date = start
    while current_date <= end:
        dt = datetime.combine(current_date, datetime.min.time())
        for model in models:
            conds = [Condition(**c) for c in json.loads(model.conditions_json or "[]")]
            outs = [Outcome(**o) for o in json.loads(model.outcomes_json or "[]")]
            rule = RuleCreate(
                rule_id=model.rule_id,
                name=model.name,
                description=model.description,
                conditions=conds,
                outcomes=outs,
                enabled=model.enabled,
                confidence=model.confidence
            )
            evs = rules_engine.evaluate_rule(rule, dt)
            events.extend(evs)
        current_date += timedelta(days=1)

    # --- Market data overlay
    try:
        market_df = market_provider.fetch_data(settings.default_sector_ticker, start, end)
        market_return = market_provider.compute_return(market_df, start, end)
    except Exception as e:
        logger.error(f"Market data fetch failed: {e}")
        market_return = None

    logger.info(f"Evaluated {len(events)} events between {start} and {end}")

    return {
        "count": len(events),
        "events": events,
        "market": {
            "ticker": settings.default_sector_ticker,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "return_pct": round(market_return * 100, 2) if market_return is not None else None
        }
    }
