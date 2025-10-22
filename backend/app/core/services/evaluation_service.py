# backend/app/core/services/evaluation_service.py
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json
from sqlmodel import select

from app.core.db.db import get_db
from app.core.db.models import RuleModel
from app.core.common.schemas import ConditionRead, OutcomeRead, RuleCreate
from app.core.astro.factories.provider_factory import get_provider as get_astro_provider
from app.core.rules.engine.rules_engine_impl import RulesEngineImpl
from app.core.common.config import settings
from app.core.common.logger import setup_logger

logger = setup_logger(settings.log_level)


def evaluate_rules_for_range(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    Evaluate all enabled rules for each date between start_date and end_date (inclusive)
    and return a list of events.

    Each event is a dict:
      { "rule_id", "name", "date", "sector", "effect", "weight", "confidence" }
    """
    try:
        start = datetime.fromisoformat(start_date).date()
        end = datetime.fromisoformat(end_date).date()
    except Exception as e:
        raise ValueError(f"Invalid date format: {e}")

    if end < start:
        raise ValueError("end_date must be >= start_date")

    # load rules from DB
    with get_db() as session:
        rows = session.exec(select(RuleModel).where(RuleModel.enabled == True)).all()

    if not rows:
        logger.info("No enabled rules found.")
        return []

    # init provider + engine
    astro_provider = get_astro_provider(settings.provider_type)
    engine = RulesEngineImpl(astro_provider)

    events: List[Dict[str, Any]] = []
    current = start
    while current <= end:
        dt = datetime.combine(current, datetime.min.time())
        for r in rows:
            conds = [ConditionRead(**c) for c in json.loads(r.conditions or "[]")]
            outs = [OutcomeRead(**o) for o in json.loads(r.outcomes or "[]")]
            rule = RuleCreate(
                rule_id=r.rule_id,
                name=r.name,
                description=r.description,
                conditions=conds,
                outcomes=outs,
                enabled=r.enabled,
                confidence=r.confidence
            )
            evs = engine.evaluate_rule(rule, dt)
            # engine events already include rule_id, date, sector, effect, weight, confidence
            # attach rule name for readability
            for e in evs:
                e["name"] = rule.name
            events.extend(evs)
        current = current + timedelta(days=1)

    logger.info(f"Evaluation produced {len(events)} events between {start} and {end}")
    return events
