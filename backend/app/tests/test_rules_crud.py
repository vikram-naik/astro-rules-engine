# app/tests/test_rules_crud.py
from sqlalchemy import select
from app.core.db.models import Sector, Rule, ConditionGroup, Condition, Outcome


def test_rule_condition_outcome_crud(db_session):
    session = db_session

    # 1️⃣ Create sector (reference)
    sector = Sector(code="EQUITY", name="Equity Market", description="Stock market sector")
    session.add(sector)
    session.commit()
    session.refresh(sector)
    assert sector.id is not None

    # 2️⃣ Create rule with one condition group and one condition
    rule = Rule(
        name="Jupiter in Ketu Nakshatra",
        description="Market weakens",
        confidence=0.9,
        enabled=True,
    )

    # Create a condition group for this rule
    group = ConditionGroup(rule=rule, operator="AND")
    cond = Condition(
        planet="jupiter",
        relation="in_nakshatra_owned_by",
        target="ketu",
        orb=10.0,
    )
    group.conditions.append(cond)
    rule.condition_groups.append(group)

    # Add one outcome
    out = Outcome(effect="Bearish", weight=1.0, sector=sector)
    rule.outcomes.append(out)

    session.add(rule)
    session.commit()
    session.refresh(rule)

    # 3️⃣ Validate persistence
    assert rule.id is not None
    assert len(rule.condition_groups) == 1
    assert rule.condition_groups[0].conditions[0].planet == "jupiter"
    assert rule.outcomes[0].sector.name == "Equity Market"

    # 4️⃣ Query rule and linked outcome
    db_rule = session.scalar(select(Rule).where(Rule.id == rule.id))
    assert db_rule.name == "Jupiter in Ketu Nakshatra"
    assert db_rule.outcomes[0].effect == "Bearish"
    assert db_rule.outcomes[0].sector.code == "EQUITY"

    # 5️⃣ Update
    db_rule.name = "Jupiter in Ketu Nakshatra (Updated)"
    session.commit()
    session.refresh(db_rule)
    assert "(Updated)" in db_rule.name

    # 6️⃣ Delete rule → cascades to condition groups, conditions & outcomes
    session.delete(db_rule)
    session.commit()

    # All associated conditions, groups, and outcomes should be deleted
    assert session.scalars(select(Condition)).all() == []
    assert session.scalars(select(ConditionGroup)).all() == []
    assert session.scalars(select(Outcome)).all() == []

    # But sector should persist
    sectors_remaining = session.scalars(select(Sector)).all()
    assert len(sectors_remaining) == 1
    assert sectors_remaining[0].code == "EQUITY"
