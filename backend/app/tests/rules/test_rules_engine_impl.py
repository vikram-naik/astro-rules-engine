"""
Unit tests for RulesEngineImpl.

Covers:
- Initialization logging and config
- _check_condition behavior (success, missing handler, exceptions)
- evaluate_rule full flow including early termination and event generation
"""

import pytest
from datetime import datetime
from types import SimpleNamespace
from app.core.rules.engine.rules_engine_impl import RulesEngineImpl, get_orb
from app.core.common.schemas import ConditionRead
from app.core.db.enums import Relation
from app.core.common.config import settings



# -------------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------------

@pytest.fixture
def when():
    return datetime(2025, 1, 1)


@pytest.fixture
def fake_provider():
    """Stub AstroProvider with longitude stubbed in."""
    class FakeProvider:
        def __init__(self):
            self.called = []

        def longitude(self, planet, when):
            self.called.append((planet, when))
            return 123.456

    return FakeProvider()


@pytest.fixture
def engine(fake_provider):
    """RulesEngineImpl with FakeProvider."""
    return RulesEngineImpl(provider=fake_provider, orb_default=5.0)


# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------

def make_condition(relation="in_sign", planet="sun", target="aries"):
    """Constructs a minimal ConditionRead."""
    return ConditionRead(
        planet=planet,
        relation=Relation[relation],
        target=target,
        orb=None,
        id=1,
        rule_id=1,
    )


def make_rule(conditions, outcomes=None):
    """Creates a fake RuleCreate-like object."""
    return SimpleNamespace(
        rule_id=42,
        conditions=conditions,
        outcomes=outcomes or [
            SimpleNamespace(
                sector_code="EQUITY",
                effect="Bullish",
                weight=0.8,
            )
        ],
        confidence=0.9,
    )


# -------------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------------

def test_init_logs_provider_and_orb(caplog, fake_provider):
    """Ensure RulesEngineImpl initialization logs provider and orb_default."""
    caplog.set_level("DEBUG")
    engine = RulesEngineImpl(fake_provider, 3.0)
    assert engine.provider is fake_provider
    assert engine.orb_default == 3.0
    assert "initialized" in caplog.text


def test_check_condition_success(monkeypatch, engine, when):
    """Happy path: longitude + handler returns True."""
    cond = make_condition("in_sign")

    class DummyHandler:
        def check(self, provider, cond, when, orb_default):
            return True

    monkeypatch.setattr(
        "app.core.rules.relations.registry.get_relation_handler",
        lambda rel: DummyHandler()
    )

    assert engine._check_condition(cond, when) is True


def test_check_condition_handler_exception1(monkeypatch, engine, when):
    """Handler raises → should be caught and return False."""
    class FaultyHandler:
        def check(self, *a, **kw):
            raise ValueError("Bad handler")
    
    monkeypatch.setattr(
        "app.core.rules.relations.registry.get_relation_handler",
        lambda rel: FaultyHandler()
    )

    cond = make_condition("in_sign")
    assert engine._check_condition(cond, when) is False



def test_check_condition_longitude_exception(monkeypatch, engine, fake_provider, when):
    """Simulate provider.longitude raising an exception."""
    def bad_longitude(*a, **kw):
        raise RuntimeError("Longitude failed")
    fake_provider.longitude = bad_longitude

    cond = make_condition("in_sign")
    result = engine._check_condition(cond, when)
    assert result is False


def test_check_condition_missing_handler(monkeypatch, engine, when):
    """Handler missing: should log warning and return False."""
    monkeypatch.setattr("app.core.rules.relations.registry.get_relation_handler",
                        lambda rel: None)
    cond = make_condition("in_sign")
    result = engine._check_condition(cond, when)
    assert result is False


def test_check_condition_handler_exception(monkeypatch, engine, when):
    """Handler raises: should be caught and return False."""
    def faulty_handler(*args, **kwargs):
        raise ValueError("bad handler")
    monkeypatch.setattr("app.core.rules.relations.registry.get_relation_handler",
                        lambda rel: SimpleNamespace(check=faulty_handler))

    cond = make_condition("in_sign")
    result = engine._check_condition(cond, when)
    assert result is False


def test_evaluate_rule_all_conditions_true(monkeypatch, engine, when):
    """All conditions pass → events returned."""
    monkeypatch.setattr(engine, "_check_condition", lambda cond, when: True)

    conds = [make_condition("in_sign"), make_condition("aspect_with")]
    rule = make_rule(conds)

    events = engine.evaluate_rule(rule, when)
    assert len(events) == 1
    event = events[0]
    assert event["rule_id"] == 42
    # assert "EQUITY" in event["sector"]
    assert event["confidence"] == 0.9


def test_evaluate_rule_condition_false(monkeypatch, engine, when):
    """Early return: if any condition fails, no events."""
    monkeypatch.setattr(engine, "_check_condition", lambda cond, when: False)
    conds = [make_condition("in_sign"), make_condition("aspect_with")]
    rule = make_rule(conds)
    result = engine.evaluate_rule(rule, when)
    assert result == []


def test_evaluate_rule_logs_and_structure(monkeypatch, engine, when, caplog):
    """Ensure proper event structure is built."""
    caplog.set_level("DEBUG")
    monkeypatch.setattr(engine, "_check_condition", lambda c, w: True)
    rule = make_rule([make_condition("in_sign")])
    events = engine.evaluate_rule(rule, when)
    assert isinstance(events, list)
    assert events[0]["rule_id"] == 42
    assert "events_count" in caplog.text

def test_get_orb():
    # def get_orb(planet_a: str, planet_b: str) -> float: 
    planet_a = None
    planet_b = None
    orb = get_orb(planet_a, planet_b)
    assert orb == settings.orb_default 