# backend/app/api/routes_rules.py
"""
Rules Management API
--------------------
CRUD endpoints for astrological rules.
"""

from fastapi import APIRouter, HTTPException
from sqlmodel import select
from typing import List
import json

from app.core.common.db import get_session
from app.core.common.models import RuleModel
from app.core.common.schemas import RuleCreate, RuleRead, RuleUpdate
from app.core.common.logger import setup_logger
from app.core.common.config import settings

logger = setup_logger(settings.log_level)

router = APIRouter(prefix="/rules", tags=["rules"])


@router.get("/", response_model=List[RuleRead])
def get_all_rules():
    """Fetch all stored rules."""
    with get_session() as session:
        rules = session.exec(select(RuleModel)).all()
        return [RuleRead(**r.model_dump()) for r in rules]


@router.get("/{rule_id}", response_model=RuleRead)
def get_rule(rule_id: str):
    """Fetch a single rule by rule_id."""
    with get_session() as session:
        rule = session.exec(select(RuleModel).where(RuleModel.rule_id == rule_id)).first()
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        return RuleRead(**rule.model_dump())


@router.post("/", response_model=RuleRead)
def create_rule(payload: RuleCreate):
    """Create a new astrological rule."""
    with get_session() as session:
        if session.exec(select(RuleModel).where(RuleModel.name == payload.name)).first():
            raise HTTPException(status_code=400, detail="Rule with this name already exists")

        rule = RuleModel(
            rule_id=payload.rule_id or f"R_{payload.name.replace(' ', '_')}",
            name=payload.name,
            description=payload.description,
            confidence=payload.confidence,
            enabled=payload.enabled,
            conditions_json=json.dumps([c.model_dump() for c in payload.conditions]),
            outcomes_json=json.dumps([o.model_dump() for o in payload.outcomes]),
        )
        session.add(rule)
        session.commit()
        session.refresh(rule)
        logger.info(f"Created rule: {rule.name}")
        return RuleRead(**rule.model_dump())

@router.put("/{rule_id}", response_model=RuleRead)
def update_rule(rule_id: str, payload: RuleUpdate):
    """Update an existing rule."""
    with get_session() as session:
        rule = session.exec(select(RuleModel).where(RuleModel.rule_id == rule_id)).first()
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")

        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key in ("conditions", "outcomes") and value is not None:
                value = json.dumps([v.model_dump() for v in value])
                setattr(rule, f"{key}_json", value)
            elif hasattr(rule, key):
                setattr(rule, key, value)

        session.add(rule)
        session.commit()
        session.refresh(rule)
        logger.info(f"Updated rule: {rule.name}")
        return RuleRead(**rule.model_dump())


@router.delete("/{rule_id}")
def delete_rule(rule_id: str):
    """Delete a rule by ID."""
    with get_session() as session:
        rule = session.exec(select(RuleModel).where(RuleModel.rule_id == rule_id)).first()
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")

        session.delete(rule)
        session.commit()
        logger.info(f"Deleted rule: {rule.name}")
        return {"message": f"Rule {rule_id} deleted successfully"}
