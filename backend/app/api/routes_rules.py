# app/api/routes_rules.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.db import get_db
from app.core.db.models import Rule, ConditionGroup, Condition, Outcome, Sector

router = APIRouter(prefix="/api/rules", tags=["rules"])


# --------------------------------------------------------
# Utility: Recursive creation of groups and conditions
# --------------------------------------------------------
def build_condition_group(group_data: dict, rule: Rule, parent_group=None):
    """Recursively create a ConditionGroup with nested conditions and subgroups."""
    group = ConditionGroup(
        rule=rule,
        parent_group=parent_group,
        operator=group_data.get("operator", "AND"),
        order=group_data.get("order", 0),
    )

    # Add conditions under this group
    for cond_data in group_data.get("conditions", []):
        cond = Condition(
            planet=cond_data.get("planet"),
            relation=cond_data.get("relation"),
            target=cond_data.get("target"),
            orb=cond_data.get("orb"),
            value=cond_data.get("value"),
        )
        group.conditions.append(cond)

    # Recurse into subgroups
    for sub_data in group_data.get("subgroups", []):
        subgroup = build_condition_group(sub_data, rule, parent_group=group)
        group.subgroups.append(subgroup)

    return group


def serialize_condition_group(group: ConditionGroup):
    """Recursively serialize a ConditionGroup tree into JSON."""
    return {
        "id": group.id,
        "operator": group.operator,
        "order": group.order,
        "conditions": [
            {
                "id": c.id,
                "planet": c.planet,
                "relation": c.relation,
                "target": c.target,
                "orb": c.orb,
                "value": c.value,
            }
            for c in group.conditions
        ],
        "subgroups": [serialize_condition_group(sg) for sg in group.subgroups],
    }


# --------------------------------------------------------
# CREATE
# --------------------------------------------------------
@router.post("/")
def create_rule(payload: dict, db: Session = Depends(get_db)):
    """
    Create a new rule with nested condition groups and outcomes.
    """
    rule = Rule(
        name=payload.get("name"),
        description=payload.get("description"),
        confidence=payload.get("confidence", 1.0),
        enabled=payload.get("enabled", True),
    )

    # --- Condition Groups ---
    for group_data in payload.get("condition_groups", []):
        group = build_condition_group(group_data, rule)
        rule.condition_groups.append(group)

    # --- Outcomes ---
    for out_data in payload.get("outcomes", []):
        sector_id = out_data.get("sector_id")
        if sector_id:
            sector = db.scalar(select(Sector).where(Sector.id == sector_id))
            if not sector:
                raise HTTPException(status_code=400, detail=f"Invalid sector_id {sector_id}")
            out_data["sector_id"] = sector.id
        rule.outcomes.append(Outcome(**out_data))

    db.add(rule)
    db.commit()
    db.refresh(rule)
    return {"id": rule.id}


# --------------------------------------------------------
# READ ALL
# --------------------------------------------------------
@router.get("/")
def list_rules(db: Session = Depends(get_db)):
    """List all rules with nested condition groups and outcomes."""
    rules = db.execute(select(Rule)).unique().scalars().all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "confidence": r.confidence,
            "enabled": r.enabled,
            "condition_groups": [serialize_condition_group(g) for g in r.condition_groups],
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


# --------------------------------------------------------
# READ ONE
# --------------------------------------------------------
@router.get("/{rule_id:int}")
def get_rule(rule_id: int, db: Session = Depends(get_db)):
    r = db.scalar(select(Rule).where(Rule.id == rule_id))
    if not r:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {
        "id": r.id,
        "name": r.name,
        "description": r.description,
        "confidence": r.confidence,
        "enabled": r.enabled,
        "condition_groups": [serialize_condition_group(g) for g in r.condition_groups],
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


# --------------------------------------------------------
# UPDATE
# --------------------------------------------------------
@router.put("/{rule_id:int}")
def update_rule(rule_id: int, payload: dict, db: Session = Depends(get_db)):
    rule = db.scalar(select(Rule).where(Rule.id == rule_id))
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    # --- Update top-level fields ---
    for key, value in payload.items():
        if key in {"name", "description", "confidence", "enabled"}:
            setattr(rule, key, value)

    # --- Replace condition groups if provided ---
    if "condition_groups" in payload:
        rule.condition_groups.clear()
        for group_data in payload["condition_groups"]:
            group = build_condition_group(group_data, rule)
            rule.condition_groups.append(group)

    # --- Replace outcomes if provided ---
    if "outcomes" in payload:
        rule.outcomes.clear()
        for out_data in payload["outcomes"]:
            sector_id = out_data.get("sector_id")
            if sector_id:
                sector = db.scalar(select(Sector).where(Sector.id == sector_id))
                if not sector:
                    raise HTTPException(status_code=400, detail=f"Invalid sector_id {sector_id}")
                out_data["sector_id"] = sector.id
            rule.outcomes.append(Outcome(**out_data))

    db.commit()
    db.refresh(rule)

    return {
        "id": rule.id,
        "name": rule.name,
        "description": rule.description,
        "confidence": rule.confidence,
        "enabled": rule.enabled,
        "condition_groups": [serialize_condition_group(g) for g in rule.condition_groups],
        "outcomes": [
            {
                "id": o.id,
                "effect": o.effect,
                "weight": o.weight,
                "sector_id": o.sector_id,
            }
            for o in rule.outcomes
        ],
    }


# --------------------------------------------------------
# DELETE
# --------------------------------------------------------
@router.delete("/{rule_id:int}")
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.scalar(select(Rule).where(Rule.id == rule_id))
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    db.delete(rule)
    db.commit()
    return {"deleted": rule_id}
