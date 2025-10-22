# app/api/routes_rules.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.db import get_db
from app.core.db.models import Rule, Condition, Outcome, Sector

router = APIRouter(prefix="/api/rules", tags=["rules"])


# -----------------------------
# CREATE
# -----------------------------
@router.post("/")
def create_rule(payload: dict, db: Session = Depends(get_db)):
    print(payload)
    rule_id = payload.get("rule_id")
    if not rule_id:
        rule_id=f"R_{payload.get('name').replace(' ', '_')}"
    print(rule_id)
    existing = db.scalar(select(Rule).where(Rule.rule_id == rule_id))
    if existing:
        raise HTTPException(status_code=400, detail=f"Rule '{rule_id}' already exists")

    rule = Rule(
        rule_id=rule_id,
        name=payload.get("name"),
        description=payload.get("description"),
        confidence=payload.get("confidence", 1.0),
        enabled=payload.get("enabled", True),
    )

    for cond_data in payload.get("conditions", []):
        rule.conditions.append(Condition(**cond_data))

    for out_data in payload.get("outcomes", []):
        # Outcome references sector via sector_id (optional)
        print(out_data)
        sector_id = out_data.get("sector_id")
        if sector_id:
            sector = db.scalar(select(Sector).where(Sector.id == sector_id))
            if not sector:
                raise HTTPException(status_code=400, detail=f"Invalid sector_id {sector_id}")
            out_data["sector_id"] = sector.id
        rule.outcomes.append(Outcome(**out_data))
    print(rule)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return {"id": rule.id, "rule_id": rule.rule_id}


# -----------------------------
# READ
# -----------------------------
@router.get("/")
def list_rules(db: Session = Depends(get_db)):
    """List all rules with nested conditions and outcomes."""
    rules = db.execute(select(Rule)).unique().scalars().all()  # ✅ fix here
    return [
        {
            "id": r.id,
            "rule_id": r.rule_id,
            "name": r.name,
            "description": r.description,
            "confidence": r.confidence,
            "enabled": r.enabled,
            "conditions": [
                {
                    "id": c.id,
                    "planet": c.planet,
                    "relation": c.relation,
                    "target": c.target,
                    "orb": c.orb,
                    "value": c.value,
                }
                for c in r.conditions
            ],
            "outcomes": [
                {
                    "id": o.id,
                    "effect": o.effect,
                    "weight": o.weight,
                    "sector_id": o.sector_id,
                }
                for o in r.outcomes
            ],
        }
        for r in rules
    ]

@router.get("/{rule_id}")
def get_rule(rule_id:str, db: Session = Depends(get_db)):
    """List all rules with nested conditions and outcomes."""
    r = db.scalar((select(Rule)).where(Rule.rule_id == rule_id))
    return {
            "id": r.id,
            "rule_id": r.rule_id,
            "name": r.name,
            "description": r.description,
            "confidence": r.confidence,
            "enabled": r.enabled,
            "conditions": [
                {
                    "id": c.id,
                    "planet": c.planet,
                    "relation": c.relation,
                    "target": c.target,
                    "orb": c.orb,
                    "value": c.value,
                }
                for c in r.conditions
            ],
            "outcomes": [
                {
                    "id": o.id,
                    "effect": o.effect,
                    "weight": o.weight,
                    "sector_id": o.sector_id,
                }
                for o in r.outcomes
            ],
        }

# -----------------------------
# UPDATE
# -----------------------------
@router.put("/{rule_id}")
def update_rule(rule_id: str, payload: dict, db: Session = Depends(get_db)):
    rule = db.scalar(select(Rule).where(Rule.rule_id == rule_id))
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    # Apply updates
    for key, value in payload.items():
        if key in {"name", "description", "confidence", "enabled"}:
            setattr(rule, key, value)

    # Optional: update nested relations
    if "conditions" in payload:
        rule.conditions.clear()
        for cond_data in payload["conditions"]:
            rule.conditions.append(Condition(**cond_data))
    if "outcomes" in payload:
        rule.outcomes.clear()
        for out_data in payload["outcomes"]:
            rule.outcomes.append(Outcome(**out_data))

    db.commit()
    db.refresh(rule)
    return {
        "id": rule.id,
        "rule_id": rule.rule_id,
        "name": rule.name,
        "description": rule.description,
        "conditions": [c.__dict__ for c in rule.conditions],
        "outcomes": [o.__dict__ for o in rule.outcomes],
    }


# -----------------------------
# DELETE
# -----------------------------
@router.delete("/{rule_id}")
def delete_rule(rule_id: str, db: Session = Depends(get_db)):
    rule = db.scalar(select(Rule).where(Rule.rule_id == rule_id))
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    db.delete(rule)
    db.commit()
    return {"deleted": rule_id}
