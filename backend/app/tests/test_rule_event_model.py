# app/tests/test_rule_event_model.py
import pytest
from datetime import date

# import exact models from your repo
from app.core.db.models import Sector, Rule, Condition, Outcome
from app.core.db.models_analysis import RuleEvent, DurationType, EventSubtype
from app.core.db.enums import Planet, Relation, OutcomeEffect  # uses your enums file

def test_rule_event_crud(db_session):
    db = db_session

    # create minimal Sector
    sector = Sector(code="S001", name="Test Sector", description="sector for tests")
    db.add(sector)
    db.commit()
    db.refresh(sector)

    # create a Rule (use rule_id as external id)
    rule = Rule(
        rule_id="R-STUB-1",
        name="test-rule",
        description="rule for event CRUD test",
        enabled=True,
    )
    # create a Condition and Outcome using real enum values
    cond = Condition(
        planet=Planet.sun.name,
        relation=Relation.in_sign.name,
        target=Planet.ketu.name,
        orb=1.0,
        value=None,
    )
    outc = Outcome(
        sector_id=sector.id,
        effect=OutcomeEffect.Bullish.value,
        weight=1.0,
    )

    rule.conditions = [cond]
    rule.outcomes = [outc]
    db.add(rule)
    db.commit()
    db.refresh(rule)

    # create a RuleEvent linked to the rule
    evt = RuleEvent(
        rule_id=rule.id,
        start_date=date(2025, 1, 2),
        end_date=date(2025, 1, 4),
        duration_type=DurationType.interval,
        event_subtype=EventSubtype.transient,
        provider="swisseph",
        metadata_json={"note": "test"},
    )
    db.add(evt)
    db.commit()
    db.refresh(evt)

    # assertions
    fetched = db.query(RuleEvent).filter(RuleEvent.id == evt.id).one()
    assert fetched.rule_id == rule.id
    assert fetched.provider == "swisseph"
    assert fetched.duration_type == DurationType.interval
    assert fetched.event_subtype == EventSubtype.transient
