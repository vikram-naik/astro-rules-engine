# app/tests/test_aspect_handler.py
import pytest
from datetime import datetime

from app.core.rules.relations.aspect_handler import AspectHandler
from app.core.astro.providers.stub_provider import StubProvider
from app.core.common.schemas import ConditionRead
from app.core.db.enums import Relation


@pytest.fixture
def provider():
    return StubProvider()


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


# ---- Tests for explicit numeric aspects using "aspect_with" ----

def test_aspect_with_no_explicit_angle(provider):
    """Generic aspect_with using explicit numeric angle."""
    provider.set_longitude_map({"sun": 0.0, "moon": 60.0})
    cond = make_cond("sun", "aspect_with", "moon", orb=2.0,) # no value
    h = AspectHandler()  # no fixed angle, no condition.value
    assert not h.check(provider, cond, datetime(2025, 1, 1), orb_default=1.0)

def test_aspect_with_explicit_angle(provider):
    """Generic aspect_with using explicit numeric angle."""
    provider.set_longitude_map({"sun": 0.0, "moon": 60.0})
    cond = make_cond("sun", "aspect_with", "moon", orb=2.0, value=60.0)
    h = AspectHandler()  # no fixed angle, uses condition.value
    assert h.check(provider, cond, datetime(2025, 1, 1), orb_default=1.0)


def test_aspect_with_explicit_angle_fail(provider):
    """Fails when outside orb tolerance."""
    provider.set_longitude_map({"sun": 0.0, "moon": 70.0})
    cond = make_cond("sun", "aspect_with", "moon", orb=1.0, value=60.0)
    h = AspectHandler()
    assert not h.check(provider, cond, datetime(2025, 1, 1), orb_default=1.0)


# ---- Tests for fixed-angle relations (as per registry) ----
@pytest.mark.parametrize(
    "relation,angle",
    [
        ("conjunct_with", 0.0),
        ("sextile_with", 60.0),
        ("square_with", 90.0),
        ("trine_with", 120.0),
        ("opposition_with", 180.0),
    ],
)
def test_fixed_angle_relations(provider, relation, angle):
    """Simulate registry-provided AspectHandler(angle=...)."""
    provider.set_longitude_map({"jupiter": 0.0, "saturn": float(angle)})
    cond = make_cond("jupiter", relation, "saturn", orb=3.0)
    # registry passes handler with fixed angle
    h = AspectHandler(target_angle=angle)
    assert h.check(provider, cond, datetime(2025, 1, 1), orb_default=1.0)


def test_fixed_angle_outside_orb(provider):
    """Fails when outside default orb for fixed-angle handler."""
    provider.set_longitude_map({"mars": 0.0, "venus": 95.0})
    cond = make_cond("mars", "square_with", "venus", orb=1.0)
    h = AspectHandler(target_angle=90.0)
    assert not h.check(provider, cond, datetime(2025, 1, 1), orb_default=1.0)


def test_exception_handling(monkeypatch):
    """Ensure handler gracefully handles provider failures."""
    provider = StubProvider()
    h = AspectHandler(target_angle=60.0)

    def bad_longitude(*_, **__):
        raise RuntimeError("bad")

    provider.longitude = bad_longitude
    cond = make_cond("sun", "aspect_with", "moon", orb=2.0, value=60.0)
    assert not h.check(provider, cond, datetime(2025, 1, 1), orb_default=2.0)
