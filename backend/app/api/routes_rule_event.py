from datetime import date
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.db.models_analysis import RuleEvent
from app.core.analysis.event_generator import EventGeneratorService
from app.core.db.models import Rule
from app.core.common.logger import setup_logger
from app.core.common.config import settings

router = APIRouter(prefix="/api/rules", tags=["rule-events"])

logger = setup_logger(settings.log_level)

@router.post("/{rule_id}/generate_events", response_model=List[dict])
def generate_events_for_rule(
    rule_id: str,
    start_date: date,
    end_date: date,
    provider: str = "swisseph",
    overwrite: bool = False,
    db: Session = Depends(get_db),
):
    logger.info(f"▶️  Generating events for rule_id={rule_id}, provider={provider}, "
                f"range=({start_date} → {end_date}), overwrite={overwrite}")
    try:
        rule = db.query(Rule).filter(Rule.rule_id == rule_id).one_or_none()
        if not rule:
            logger.warning(f"❌ Rule not found for rule_id={rule_id}")
            raise HTTPException(status_code=404, detail="Rule not found")

        service = EventGeneratorService(db, astro_provider_name=provider)
        events = service.generate_for_rule(
            rule_id=rule.id,
            start_date=start_date,
            end_date=end_date,
            provider=provider,
            overwrite=overwrite,
        )
        logger.info(f"✅ Generated {len(events)} events for rule_id={rule_id}")
        return [e.to_dict() for e in events]    
    except Exception as e:
        logger.exception(f"💥 Error generating events for rule_id={rule_id}: {e}")
        raise

@router.get("/{rule_id}/events", response_model=List[dict])
def list_events_for_rule(rule_id: str, db: Session = Depends(get_db)):
    logger.info(f"📥 Listing events for rule_id={rule_id}")
    rows = db.query(RuleEvent).filter(RuleEvent.rule_id == rule_id).order_by(RuleEvent.start_date).all()
    logger.info(f"📤 Found {len(rows)} events for rule_id={rule_id}")
    return [r.to_dict() for r in rows]
