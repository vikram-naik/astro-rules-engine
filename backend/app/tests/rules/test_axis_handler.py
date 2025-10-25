# app/tests/test_axis_handler.py
import pytest
from datetime import datetime

from app.core.rules.relations.axis_handler import AxisHandler
from app.core.astro.providers.stub_provider import StubProvider
from app.core.common.schemas import ConditionRead
from app.core.db.enums import Relation


@pytest.fixture
def provider():
    return StubProvider()


def make_cond(planet, relation, target, orb=None, value=None):
    return ConditionRead(
        planet=planet,
        relation=Relation[relation],
        target=target,
        orb=orb,
        value=value,
        id=1,
        rule_id=1,
    )


def test_in_axis_true(provider):
    """Planets exactly opposite (~180° apart)."""
    provider.set_longitude_map({"sun": 0.0, "moon": 180.0})
    cond = make_cond("sun", "in_axis", "moon", orb=3.0)
    h = AxisHandler()
    assert h.check(provider, cond, datetime(2025, 1, 1), orb_default=2.0)


def test_in_axis_within_orb(provider):
    """Planets slightly off 180°, within orb tolerance."""
    provider.set_longitude_map({"sun": 0.0, "moon": 182.0})
    cond = make_cond("sun", "in_axis", "moon", orb=3.0)
    h = AxisHandler()
    assert h.check(provider, cond, datetime(2025, 1, 1), orb_default=2.0)


def test_not_in_axis_outside_orb(provider):
    """Planets far from 180°, should fail."""
    provider.set_longitude_map({"sun": 0.0, "moon": 150.0})
    cond = make_cond("sun", "in_axis", "moon", orb=2.0)
    h = AxisHandler()
    assert not h.check(provider, cond, datetime(2025, 1, 1), orb_default=2.0)


def test_axis_with_default_orb(provider):
    """Orb not set, uses orb_default."""
    provider.set_longitude_map({"sun": 10.0, "mars": 190.0})
    cond = make_cond("sun", "in_axis", "mars", orb=None)
    h = AxisHandler()
    assert h.check(provider, cond, datetime(2025, 1, 1), orb_default=5.0)


def test_axis_provider_failure(monkeypatch):
    """Handler should return False if provider fails."""
    provider = StubProvider()

    def bad_longitude(*_, **__):
        raise RuntimeError("fail")

    provider.longitude = bad_longitude
    cond = make_cond("sun", "in_axis", "moon", orb=2.0)
    h = AxisHandler()
    assert not h.check(provider, cond, datetime(2025, 1, 1), orb_default=2.0)
