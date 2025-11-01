import pytest
from datetime import datetime
from app.core.rules.relations.nakshatra_handler import NakshatraOwnedHandler
from app.core.db.models import Condition

from app.core.rules.relations.registry import Relation
from app.core.astro.providers.stub_provider import StubProvider

@pytest.fixture
def handler():
    return NakshatraOwnedHandler()

@pytest.fixture
def provider(monkeypatch):
    """Stub provider with deterministic nakshatra index and owner responses."""
    sp = StubProvider()

    def fake_longitude(planet, when):
        return {
            "sun": 100.0,
            "moon": 240.0,
        }.get(planet, 0.0)

    def fake_nakshatra_index(lon):
        # arbitrary mapping — keeps logic deterministic
        return int(lon // 13.3333) % 27

    def fake_nakshatra_owner(idx):
        owners = [
            "sun", "moon", "mars", "mercury", "jupiter",
            "venus", "saturn", "rahu", "ketu"
        ]
        return owners[idx % len(owners)]

    monkeypatch.setattr(sp, "longitude", fake_longitude)
    monkeypatch.setattr(sp, "nakshatra_index", fake_nakshatra_index)
    monkeypatch.setattr(sp, "nakshatra_owner", fake_nakshatra_owner)
    return sp

@pytest.fixture
def when():
    return datetime(2025, 1, 1)

def make_cond(planet, target):
    return Condition(
        id=1,
        rule_id=1,
        planet=planet,
        relation=Relation.in_nakshatra_owned_by,
        target=target,
        orb=None,
        value=None,
    )

def test_positive_match(handler, provider, when):
    """Planet is in Nakshatra owned by target planet (match expected)."""
    cond = make_cond("moon", "sun")  # based on stub logic
    assert handler.check(provider, cond, when, orb_default=2.0) is True

def test_negative_match(handler, provider, when):
    """Planet in Nakshatra owned by a different planet."""
    cond = make_cond("sun", "mars")
    assert handler.check(provider, cond, when, orb_default=2.0) is False

def test_case_insensitivity(handler, provider, when):
    """Case variations of planet names should not affect comparison."""
    cond = make_cond("moon", "SUN")  # based on stub logic
    assert handler.check(provider, cond, when, orb_default=2.0) is True

def test_provider_exception_returns_false(monkeypatch, handler, provider, when):
    """If provider methods fail, handler should safely return False."""
    def bad_longitude(*args, **kwargs):
        raise RuntimeError("boom")
    monkeypatch.setattr(provider, "longitude", bad_longitude)
    cond = make_cond("sun", "venus")
    assert handler.check(provider, cond, when, orb_default=2.0) is False
