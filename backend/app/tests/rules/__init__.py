from app.core.common.schemas import ConditionRead, RuleCreate
from app.core.db.enums import Relation


def make_cond(planet, relation, target, orb=None, value=None):
    relation_enum = Relation[relation]
    return ConditionRead(
        planet=planet,
        relation=relation_enum,
        target=target,
        orb=orb,
        value=value,
        id=1,
        rule_id=1,
    )

def make_rule(conditions, rule_id="R001"):
    """Build a minimal rule for testing."""
    return RuleCreate(
        name=f"Rule-{rule_id}",
        conditions=conditions,
        outcomes=[
            {"sector_code": "EQUITY", "effect": "Bullish", "weight": 0.7}
        ],
        confidence=0.8,
        rule_id=rule_id,
        enabled=True
    )