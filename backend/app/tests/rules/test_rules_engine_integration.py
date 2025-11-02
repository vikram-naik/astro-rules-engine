"""
Integration tests for RulesEngineImpl using real handlers + StubProvider.

This validates that the full rule evaluation pipeline (provider → handler → event)
works correctly across all supported relation types.
"""

import pytest
from datetime import datetime
from app.core.rules.engine.rules_engine_impl import RulesEngineImpl
from app.core.astro.providers.stub_provider import StubProvider
from app.core.db.models import Condition, Rule

from app.core.db.enums import Relation
from app.tests.rules import make_cond, make_rule as shared_make_rule


# -------------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------------

@pytest.fixture
def when():
    return datetime(2025, 1, 1)


@pytest.fixture
def provider():
    """Stub provider with known longitudes."""
    p = StubProvider()
    # Sun at 0°, Moon at 90°, Venus near Sun, Jupiter–Saturn 120° apart
    p.set_longitude_map({
        "sun": 0.0,
        "moon": 90.0,
        "venus": 3.0,
        "jupiter": 0.0,
        "saturn": 120.0,
        "mercury": 15.0,
    })
    return p


@pytest.fixture
def engine(provider):
    return RulesEngineImpl(provider, orb_default=5.0)


def make_rule(conditions):
    """Build a minimal rule for testing, no ORM."""
    class FakeGroup:
        def __init__(self, conditions):
            self.operator = "AND"
            self.conditions = conditions
            self.subgroups = []

    class FakeRule:
        def __init__(self, conditions):
            self.id = 1
            self.name = "Integration Rule"
            self.confidence = 0.9
            self.condition_groups = [FakeGroup(conditions)]
            self.outcomes = [
                # Simple namespace-like object, not ORM model
                type("Outcome", (), {"sector_id": 1, "effect": "Bullish", "weight": 0.7})()
            ]

    return FakeRule(conditions)



# -------------------------------------------------------------------------
# Core Tests
# -------------------------------------------------------------------------

def test_in_sign_relation(engine, provider, when):
    """Verify Sun in Aries → SignHandler executes successfully."""
    cond = make_cond(planet="sun", relation=Relation.in_sign, target="aries")
    rule = make_rule([cond])
    result = engine.evaluate_rule(rule, when)
    print(result)
    assert result and result[0]["rule_id"] == 1


def test_house_relative_relation(engine, provider, when):
    """Moon 90° from Sun → 4th house."""
    cond = make_cond(
        planet="moon",
        relation=Relation.in_house_relative_to,
        target="sun",
        value="4",
    )
    rule = make_rule([cond])
    result = engine.evaluate_rule(rule, when)
    assert result and result[0]["rule_id"] == 1


def test_combust_relation(engine, provider, when):
    """Venus near Sun within orb → combust."""
    cond = make_cond(planet="venus", relation=Relation.combust_by_sun, target=None)
    rule = make_rule([cond])
    result = engine.evaluate_rule(rule, when)
    assert result and result[0]["rule_id"] == 1


def test_aspect_relation(engine, provider, when):
    """Jupiter 120° from Saturn → trine aspect."""
    cond = make_cond( 
        planet="jupiter",
        relation=Relation.aspect_with,
        target="saturn",
        value=120.0,
    )
    rule = make_rule([cond])
    result = engine.evaluate_rule(rule, when)
    assert result and result[0]["rule_id"] == 1


def test_axis_relation(engine, provider, when):
    """Sun opposite Saturn → axis alignment."""
    provider.set_longitude_map({"sun": 0.0, "saturn": 180.0})
    cond = make_cond(
        planet="sun",
        relation=Relation.in_axis,
        target="saturn",
    )
    rule = make_rule([cond])
    result = engine.evaluate_rule(rule, when)
    assert result and result[0]["rule_id"] == 1


def test_nakshatra_owned_by_relation(engine, provider, when):
    """Verify Moon is in a Nakshatra owned by Venus."""
    cond = make_cond(
        planet="moon",
        relation=Relation.in_nakshatra_owned_by,
        target="venus",
    )

    # Mock the Nakshatra lookup chain
    provider.nakshatra_index = lambda lon: 5
    provider.nakshatra_owner = lambda idx: "venus"

    rule = make_rule([cond])
    result = engine.evaluate_rule(rule, when)
    print("Nakshatra result:", result)

    assert result and result[0]["rule_id"] == 1




def test_retrograde_relation(monkeypatch, engine, provider, when):
    """Retrograde handler → uses provider.is_retrograde()."""
    provider.is_retrograde = lambda planet, when: True
    cond = make_cond(planet="mercury", relation=Relation.is_retrograde, target=None)
    rule = make_rule([cond])
    result = engine.evaluate_rule(rule, when)
    assert result and result[0]["rule_id"] == 1


def test_mixed_conditions_all_true(engine, provider, when):
    """Combust + HouseRelative both True → event generated."""
    conds = [
        make_cond(planet="venus", relation=Relation.combust_by_sun, target=None),
        make_cond(planet="moon", relation=Relation.in_house_relative_to, target="sun", value="4"),
    ]
    rule = make_rule(conds)
    result = engine.evaluate_rule(rule, when)
    assert result and len(result) == 1


def test_partial_failure(engine, provider, when):
    """One condition fails → no event generated."""
    conds = [
        make_cond(planet="sun", relation=Relation.in_sign, target="aries"),
        make_cond(planet="venus", relation=Relation.combust_by_sun, target=None, orb=-1),  # invalid orb
    ]
    rule = make_rule(conds)
    result = engine.evaluate_rule(rule, when)
    assert result == []

@pytest.mark.parametrize("angle,expected", [
    (0.0, "conjunction"),
    (60.0, "sextile"),
    (90.0, "square"),
    (120.0, "trine"),
    (180.0, "opposition"),
])
def test_aspect_named_relations(engine, provider, when, angle, expected):
    """Validate that known angular separations map to the correct named aspects."""
    provider.set_longitude_map({"jupiter": 0.0, "saturn": angle})
    cond = make_cond(
        planet="jupiter",
        relation=Relation.aspect_with,
        target="saturn",
        value=angle,  # float degrees
    )
    rule = make_rule([cond])
    result = engine.evaluate_rule(rule, when)
    assert result and result[0]["rule_id"] == 1, f"Failed for aspect={expected}"

@pytest.mark.parametrize("relation,angle,name", [
    (Relation.trine_with, 120.0, "trine"),
    (Relation.square_with, 90.0, "square"),
    (Relation.sextile_with, 60.0, "sextile"),
    (Relation.opposition_with, 180.0, "opposition"),
    (Relation.quincunx_with, 150.0, "quincunx"),
    (Relation.semisextile_with, 30.0, "semisextile"),
    (Relation.semisquare_with, 45.0, "semisquare"),
    (Relation.quintile_with, 72.0, "quintile"),
    (Relation.sesquiquadrate_with, 135.0, "sesquiquadrate"),
])
def test_named_aspect_relations(engine, provider, when, relation, angle, name):
    """Check all named aspect_with derivatives like trine_with, sextile_with, etc."""
    provider.set_longitude_map({"jupiter": 0.0, "saturn": angle})
    cond =make_cond(
        planet="jupiter",
        relation=relation,
        target="saturn",
    )
    rule = make_rule([cond])
    result = engine.evaluate_rule(rule, when)
    assert result and result[0]["rule_id"] == 1, f"{name} aspect failed"