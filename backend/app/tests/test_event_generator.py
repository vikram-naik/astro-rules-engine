from datetime import date

import pytest
from app.core.db.models import Rule, Condition, Outcome
from app.core.db.enums import Planet, Relation, OutcomeEffect
from app.core.analysis.event_generator import EventGeneratorService
from app.core.rules.engine.rules_engine_impl import RulesEngineImpl


def test_event_generation_flow(db_session, monkeypatch):
    """
    Verify EventGeneratorService correctly creates interval events
    when RulesEngineImpl.evaluate_rule returns True for a range of dates.
    Uses the real provider factory (get_provider) with the stub provider.
    """
    db = db_session

    # ------------------------------------------------------------------
    # Setup: minimal valid rule with condition + outcome
    # ------------------------------------------------------------------
    rule = Rule(
        rule_id="R-EVT-1",
        name="event-generator-rule",
        description="Rule for event generation test",
        enabled=True,
    )
    cond = Condition(
        planet=Planet.mars.value,       # e.g. "Mars"
        relation=Relation.in_axis.value,  # e.g. "In Axis"
        target="Venus",
        orb=3.0,
        value=None,
    )
    outc = Outcome(
        sector_id=None,
        effect=OutcomeEffect.Bullish.value,  # "Bullish"
        weight=1.0,
    )
    rule.conditions = [cond]
    rule.outcomes = [outc]
    db.add(rule)
    db.commit()
    db.refresh(rule)

    # ------------------------------------------------------------------
    # Monkeypatch only RulesEngineImpl.evaluate_rule for deterministic True window
    # ------------------------------------------------------------------
    def fake_evaluate_rule(self, rule_obj, dt):
        # True from Jan 2–4, False otherwise
        if date(2025, 1, 2) <= dt <= date(2025, 1, 4):
            return True, {"note": f"{rule_obj.name} active on {dt.isoformat()}"}
        return False, {}

    monkeypatch.setattr(RulesEngineImpl, "evaluate_rule", fake_evaluate_rule)

    # ------------------------------------------------------------------
    # Instantiate EventGeneratorService with stub provider via factory
    # ------------------------------------------------------------------
    generator = EventGeneratorService(db_session=db, astro_provider_name="stub")

    events = generator.generate_for_rule(
        rule_id=rule.id,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 7),
        provider="stub",
        overwrite=True,
    )

    # ------------------------------------------------------------------
    # Assertions
    # ------------------------------------------------------------------
    assert isinstance(events, list)
    assert len(events) == 1

    evt = events[0]
    assert evt.start_date == date(2025, 1, 2)
    assert evt.end_date == date(2025, 1, 4)
    assert evt.duration_type.name == "interval"
    assert evt.metadata_json.get("note").startswith("event-generator-rule active")
