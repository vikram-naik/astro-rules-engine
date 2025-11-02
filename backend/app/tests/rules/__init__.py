from app.core.db.enums import Relation
from app.core.db.models import Condition, ConditionGroup, Rule


def make_cond(planet, relation, target, orb=None, value=None):
    if isinstance(relation, str):
        relation_enum = Relation[relation]
    else:
        relation_enum = relation
    return Condition(
        planet=planet,
        relation=relation_enum,
        target=target,
        orb=orb,
        value=value,
        id=1,
    )

def make_rule(conditions, id="R001"):
    """Build a minimal rule for testing."""
    rule = Rule(
        name=f"Rule-{id}",
        outcomes=[
            {"sector_id": 1, "effect": "Bullish", "weight": 0.7}
        ],
        confidence=0.8,
        enabled=True
    )
    # Create a condition group for this rule
    group = ConditionGroup(rule=rule, operator="AND")
    group.conditions.append(conditions)
    rule.condition_groups.append(group)
    return rule