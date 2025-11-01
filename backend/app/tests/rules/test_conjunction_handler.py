import pytest
from datetime import datetime
from app.core.rules.relations.conjunction_handler import ConjunctionHandler
from app.core.db.models import Condition
from app.core.rules.relations.registry import Relation
from app.core.astro.providers.stub_provider import StubProvider

@pytest.fixture
def handler():
    return ConjunctionHandler()

@pytest.fixture
def provider():
    return StubProvider()

@pytest.fixture
def when():
    return datetime(2025, 1, 1)

def make_cond(planet, target, orb=None):
    return Condition(
        id=1,
        rule_id=1,
        planet=planet,
        relation=Relation.conjunct_with,
        target=target,
        orb=orb,
        value=None,
    )

def test_exact_conjunction(handler, provider, when):
    """Planets with exactly same longitude should be conjunct."""
    provider.set_longitude_map({"sun": 100.0, "moon": 100.0})
    cond = make_cond("sun", "moon", orb=5.0)
    assert handler.check(provider, cond, when, orb_default=2.0) is True

def test_within_orb(handler, provider, when):
    """Planets within allowable orb should be conjunct."""
    provider.set_longitude_map({"sun": 100.0, "moon": 102.5})
    cond = make_cond("sun", "moon", orb=3.0)
    assert handler.check(provider, cond, when, orb_default=2.0) is True

def test_outside_orb(handler, provider, when):
    """Planets beyond the orb should not be conjunct."""
    provider.set_longitude_map({"sun": 100.0, "moon": 107.0})
    cond = make_cond("sun", "moon", orb=3.0)
    assert handler.check(provider, cond, when, orb_default=2.0) is False

def test_default_orb_applied(handler, provider, when):
    """If orb not specified, use orb_default parameter."""
    provider.set_longitude_map({"sun": 10.0, "venus": 12.0})
    cond = make_cond("sun", "venus", orb=None)
    assert handler.check(provider, cond, when, orb_default=5.0) is True

def test_longitude_exception_returns_false(monkeypatch, handler, provider, when):
    """If longitude computation fails, return False safely."""
    def bad_longitude(*args, **kwargs):
        raise ValueError("Broken provider")

    monkeypatch.setattr(provider, "longitude", bad_longitude)
    cond = make_cond("sun", "moon", orb=3.0)
    assert handler.check(provider, cond, when, orb_default=2.0) is False
