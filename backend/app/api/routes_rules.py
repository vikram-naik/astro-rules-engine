# app/api/routes_rules.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.db import get_db
from app.core.db.models import Rule, ConditionGroup, Condition, Outcome, Sector

router = APIRouter(prefix="/api/rules", tags=["rules"])


# ---------------------------------------------------------------------
# Recursive group builder (trust frontend order)
# ---------------------------------------------------------------------
def build_condition_group(group_data: dict, rule: Rule, parent_group=None, group_index: int = 0):
    """
    Recursively create a ConditionGroup tree (preserving local order).
    - Uses the frontend-provided 'order' value whenever present.
    - Falls back to group_index only if 'order' is missing.
    """
    grp_order = group_data.get("order", group_index)

    group = ConditionGroup(
        rule=rule,
        parent_group=parent_group,
        operator=group_data.get("operator", "AND"),
        order=grp_order,
    )

    # Add conditions (trust frontend order)
    for idx, cond_data in enumerate(group_data.get("conditions", [])):
        cond_order = cond_data.get("order", idx)
        cond = Condition(
            planet=cond_data.get("planet"),
            relation=cond_data.get("relation"),
            target=cond_data.get("target"),
            orb=cond_data.get("orb"),
            value=cond_data.get("value"),
            order=cond_order,
        )
        group.conditions.append(cond)

    # Recursively add subgroups (trust frontend order)
    for idx, sub_data in enumerate(group_data.get("subgroups", [])):
        build_condition_group(
            sub_data, rule, parent_group=group, group_index=idx
        )

    return group


# ---------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------
def serialize_condition_group(group: ConditionGroup):
    """Serialize a ConditionGroup tree sorted by 'order' for deterministic output."""
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
                "order": getattr(c, "order", 0),
            }
            for c in sorted(group.conditions, key=lambda x: getattr(x, "order", 0))
        ],
        "subgroups": [
            serialize_condition_group(sg)
            for sg in sorted(group.subgroups, key=lambda x: getattr(x, "order", 0))
        ],
    }


# ---------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------
@router.post("/")
def create_rule(payload: dict, db: Session = Depends(get_db)):
    """Create a new rule with nested condition groups and outcomes."""
    print(f"Payload: {payload} ")
    rule = Rule(
        name=payload.get("name"),
        description=payload.get("description"),
        confidence=payload.get("confidence", 1.0),
        enabled=payload.get("enabled", True),
    )

    for idx, group_data in enumerate(payload.get("condition_groups", [])):
        group = build_condition_group(group_data, rule, group_index=idx)
        rule.condition_groups.append(group)

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


# ---------------------------------------------------------------------
# READ ALL
# ---------------------------------------------------------------------
@router.get("/")
def list_rules(db: Session = Depends(get_db)):
    rules = db.execute(select(Rule)).unique().scalars().all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "confidence": r.confidence,
            "enabled": r.enabled,
            "condition_groups": [
                serialize_condition_group(g)
                for g in sorted(r.condition_groups, key=lambda x: getattr(x, "order", 0))
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


# ---------------------------------------------------------------------
# READ ONE
# ---------------------------------------------------------------------
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
        "condition_groups": [
            serialize_condition_group(g)
            for g in sorted(r.condition_groups, key=lambda x: getattr(x, "order", 0))
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


# ---------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------
@router.put("/{rule_id:int}")
def update_rule(rule_id: int, payload: dict, db: Session = Depends(get_db)):
    rule = db.scalar(select(Rule).where(Rule.id == rule_id))
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    for key, value in payload.items():
        if key in {"name", "description", "confidence", "enabled"}:
            setattr(rule, key, value)

    if "condition_groups" in payload:
        rule.condition_groups.clear()
        for idx, group_data in enumerate(payload["condition_groups"]):
            group = build_condition_group(group_data, rule, group_index=idx)
            rule.condition_groups.append(group)

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
        "condition_groups": [
            serialize_condition_group(g)
            for g in sorted(rule.condition_groups, key=lambda x: getattr(x, "order", 0))
        ],
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


# ---------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------
@router.delete("/{rule_id:int}")
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.scalar(select(Rule).where(Rule.id == rule_id))
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    db.delete(rule)
    db.commit()
    return {"deleted": rule_id}
