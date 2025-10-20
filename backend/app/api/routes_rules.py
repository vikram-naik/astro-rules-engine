from typing import List
from fastapi import APIRouter, HTTPException
from app.core.common.db import get_session
from app.core.common.models import RuleModel, Sector
from app.core.common.schemas import RuleCreate, RuleRead
import json


router = APIRouter()


@router.post("/", response_model=RuleRead)
def create_rule(rule_in: RuleCreate):
    with get_session() as session:
        existing = session.exec(select(RuleModel).where(RuleModel.rule_id == rule_in.rule_id)).first()
        if existing:
            raise HTTPException(status_code=400, detail="rule_id already exists")
        rm = RuleModel(rule_id=rule_in.rule_id, name=rule_in.name, description=rule_in.description,
        enabled=rule_in.enabled, confidence=rule_in.confidence,
        conditions_json=json.dumps([c.dict() for c in rule_in.conditions]),
        outcomes_json=json.dumps([o.dict() for o in rule_in.outcomes]))
        session.add(rm)
        session.commit()
        session.refresh(rm)

        return RuleRead(rule_id=rm.rule_id, name=rm.name, description=rm.description,
        conditions=[c for c in rule_in.conditions], outcomes=[o for o in rule_in.outcomes],
        enabled=rm.enabled, confidence=rm.confidence)


@router.get("/", response_model=List[RuleRead])
def list_rules():
    with get_session() as session:
        rows = session.exec(select(RuleModel)).all()
        out = []
        for r in rows:
            conds = json.loads(r.conditions_json or "[]")
            outs = json.loads(r.outcomes_json or "[]")
            out.append(RuleRead(rule_id=r.rule_id, name=r.name, description=r.description,
            conditions=conds, outcomes=outs, enabled=r.enabled, confidence=r.confidence))
        return out


@router.delete("/{rule_id}")
def delete_rule(rule_id: str):
    with get_session() as session:
        r = session.exec(select(RuleModel).where(RuleModel.rule_id == rule_id)).first()
        if not r:
            raise HTTPException(status_code=404, detail="Rule not found")
        session.delete(r)
        session.commit()
    return {"deleted": rule_id}