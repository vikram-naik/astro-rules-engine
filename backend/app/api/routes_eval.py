from fastapi import APIRouter
from backend.app.core.config import Settings
from backend.app.core.market_data import MarketDataProvider
from core.db import get_session
from core.models import RuleModel
from core.schemas import EvaluateRequest, RuleCreate, Condition, Outcome
import json
from datetime import datetime, timedelta
from core.astro_provider import AstroProvider
from core.rules_engine import AstroRulesEngine


router = APIRouter()
mdp = MarketDataProvider()



@router.post("/")
def evaluate(req: EvaluateRequest):
    start = datetime.fromisoformat(req.start_date).date()
    end = datetime.fromisoformat(req.end_date).date()
    if end < start:
        return {"error": "end_date must be >= start_date"}
    with get_session() as session:
        models = session.exec(select(RuleModel).where(RuleModel.enabled == True)).all()
    rules = []
    for m in models:
        conds = [Condition(**c) for c in json.loads(m.conditions_json or "[]")]
        outs = [Outcome(**o) for o in json.loads(m.outcomes_json or "[]")]
        rules.append(RuleCreate(rule_id=m.rule_id, name=m.name, description=m.description,
        conditions=conds, outcomes=outs, enabled=m.enabled, confidence=m.confidence))


        provider = AstroProvider()
        engine = AstroRulesEngine(provider)
        events = []
        d = start
        while d <= end:
            dt = datetime.combine(d, datetime.min.time())
            for r in rules:
                evs = engine.evaluate_rule(r, dt)
                events.extend(evs)
                d = d + timedelta(days=1)

    market_df = mdp.fetch_sector_data(Settings.default_sector_ticker, start, end)
    overall_return = mdp.compute_return_window(market_df, start, end)
    return {
        "count": len(events),
        "events": events,
        "market_return": round(overall_return * 100, 2)
    }