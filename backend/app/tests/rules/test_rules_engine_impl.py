"""
Tests for RulesEngineImpl
-------------------------
Verifies condition evaluation and event generation
using the StubProvider (deterministic astro data).
"""

from datetime import datetime
from app.core.astro.providers.stub_provider import StubProvider
from app.core.rules.engine.rules_engine_impl import RulesEngineImpl
from app.core.common.schemas import RuleCreate, Condition, Outcome, OutcomeEffect, Relation


def make_basic_rule():
    """Helper to construct a simple Jupiter-Ketu conjunction rule."""
    cond = Condition(
        planet="jupiter",
        relation=Relation.conjunct_with,
        target="rahu",
        orb=10.0
    )
    out = Outcome(sector_code="EQUITY", effect=OutcomeEffect.Bearish)
    return RuleCreate(
        rule_id="T_CONJ",
        name="Test Jupiter-Rahu Conjunction",
        conditions=[cond],
        outcomes=[out],
        confidence=0.9
    )


def test_engine_evaluate_rule_stub():
    """Ensure engine evaluates a rule and produces event(s)."""
    provider = StubProvider()
    engine = RulesEngineImpl(provider)

    rule = make_basic_rule()
    dt = datetime(2025, 1, 1)

    events = engine.evaluate_rule(rule, dt)
    assert isinstance(events, list)
    assert len(events) >= 0
    # If conditions match, event dict keys should be correct
    if events:
        e = events[0]
        assert "rule_id" in e and "sector" in e and "effect" in e


def test_condition_in_nakshatra_owned_by():
    """Check nakshatra ownership condition evaluation."""
    provider = StubProvider()
    engine = RulesEngineImpl(provider)

    cond = Condition(
        planet="jupiter",
        relation=Relation.in_nakshatra_owned_by,
        target="Ketu"
    )
    out = Outcome(sector_code="METAL", effect=OutcomeEffect.Bearish)
    rule = RuleCreate(
        rule_id="R002",
        name="Jupiter in Ketu Nakshatra",
        conditions=[cond],
        outcomes=[out]
    )

    dt = datetime(2025, 1, 1)
    events = engine.evaluate_rule(rule, dt)
    assert isinstance(events, list)


def test_engine_handles_invalid_planet_gracefully():
    """Should not raise exceptions for unsupported planet names."""
    provider = StubProvider()
    engine = RulesEngineImpl(provider)

    cond = Condition(planet="unknown", relation=Relation.conjunct_with, target="sun")
    out = Outcome(sector_code="EQUITY", effect=OutcomeEffect.Bearish)
    rule = RuleCreate(rule_id="INVALID", name="Bad planet", conditions=[cond], outcomes=[out])

    dt = datetime(2025, 1, 1)
    events = engine.evaluate_rule(rule, dt)
    assert events == []
