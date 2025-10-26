from app.core.common.schemas import ConditionRead
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