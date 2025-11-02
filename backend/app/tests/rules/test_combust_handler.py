# app/tests/test_combust_handler.py
from datetime import datetime
import pytest
from app.core.rules.relations.combust_handler import CombustHandler
from app.core.astro.providers.stub_provider import StubProvider
from app.core.db.models import Condition
from app.core.db.enums import Relation
from app.core.common import config
from app.tests.rules import make_cond


@pytest.fixture
def handler():
    return CombustHandler()


@pytest.fixture
def when():
    return datetime(2025, 1, 1)


def test_combust_by_sun_true_default_orb(handler, when):
    sp = StubProvider()
    sp.set_longitude_map({"mars": 100.0, "sun": 105.0})
    cond = make_cond(planet="mars",
                         relation=Relation.combust_by_sun, target=None, orb=None, value=None)
    assert handler.check(sp, cond, when, orb_default=8.0) is True


def test_combust_by_sun_false_small_orb(handler, when):
    sp = StubProvider()
    sp.set_longitude_map({"mars": 100.0, "sun": 110.0})
    cond = make_cond(planet="mars",
                         relation=Relation.combust_by_sun, target=None, orb=3.0, value=None)
    assert handler.check(sp, cond, when, orb_default=8.0) is False


def test_combust_with_settings_override(handler, when, monkeypatch):
    sp = StubProvider()
    sp.set_longitude_map({"venus": 100.0, "sun": 106.0})
    monkeypatch.setattr(config.settings, "astro_combust_orbs", {"venus": 7.0})
    cond = make_cond( planet="venus",
                         relation=Relation.combust_by_sun, target=None, orb=None, value=None)
    assert handler.check(sp, cond, when, orb_default=4.0) is True


def test_combust_exact_boundary(handler, when):
    """Distance exactly equal to orb should still be combust."""
    sp = StubProvider()
    sp.set_longitude_map({"mars": 100.0, "sun": 108.0})
    cond = make_cond( planet="mars",
                         relation=Relation.combust_by_sun, target=None, orb=8.0, value=None)
    assert handler.check(sp, cond, when, orb_default=4.0) is True


def test_combust_just_outside_orb(handler, when):
    sp = StubProvider()
    sp.set_longitude_map({"mars": 100.0, "sun": 108.1})
    cond = make_cond(planet="mars",
                         relation=Relation.combust_by_sun, target=None, orb=8.0, value=None)
    assert handler.check(sp, cond, when, orb_default=4.0) is False


def test_combust_wraparound_angle(handler, when):
    """Sun at 359°, planet at 2° → 3° apart = combust if orb_default >=3"""
    sp = StubProvider()
    sp.set_longitude_map({"sun": 359.0, "mercury": 2.0})
    cond = make_cond(planet="mercury",
                         relation=Relation.combust_by_sun, target=None, orb=None, value=None)
    assert handler.check(sp, cond, when, orb_default=5.0) is True


def test_combust_provider_error(monkeypatch, handler, when):
    """If provider fails, check should return False gracefully."""
    class BadProvider:
        def longitude(self, planet, when):
            raise ValueError("Broken provider")

    bp = BadProvider()
    cond = make_cond(planet="mars",
                         relation=Relation.combust_by_sun, target=None, orb=None, value=None)
    assert handler.check(bp, cond, when, orb_default=8.0) is False


def test_combust_settings_exception(monkeypatch, handler, when):
    """If accessing settings raises, CombustHandler should gracefully fall back to DEFAULT_ORB."""
    sp = StubProvider()
    sp.set_longitude_map({"sun": 100.0, "mars": 102.0})

    # Create a mock that fails on any attribute access
    class BadSettings:
        def __getattr__(self, name):
            raise RuntimeError("Configuration access failure")

    # ✅ Patch the imported singleton INSIDE the combust_handler module
    monkeypatch.setattr("app.core.rules.relations.combust_handler.settings", BadSettings())

    cond =make_cond(
        planet="mars",
        relation=Relation.combust_by_sun,
        target=None,
        orb=None,
        value=None,
    )

    # Should now trigger the `except Exception` branch and use DEFAULT_ORB fallback
    result = handler.check(sp, cond, when, orb_default=8.0)
    assert result is True


def test_combust_settings_non_dict(monkeypatch, handler, when):
    """If settings.combust_orbs exists but is not a dict, fall back to DEFAULT_ORB."""
    sp = StubProvider()
    sp.set_longitude_map({"sun": 100.0, "venus": 102.0})

    # Patch the settings to return a non-dict type (like float)
    class WeirdSettings:
        combust_orbs = 5.0  # Invalid type (should be dict)

    monkeypatch.setattr("app.core.rules.relations.combust_handler.settings", WeirdSettings())

    cond = make_cond(
        planet="venus",
        relation=Relation.combust_by_sun,
        target=None,
        orb=None,
        value=None,
    )

    # Should use fallback DEFAULT_ORB (8°)
    result = handler.check(sp, cond, when, orb_default=8.0)
    assert result is True
