"""
Tests for Provider Factory
--------------------------
Verifies that get_provider() dynamically loads and instantiates
the correct provider classes via importlib.
"""

from app.core.astro.factories.provider_factory import clear_providers, get_provider
from app.core.astro.interfaces.i_astro_provider import IAstroProvider
import pytest

from app.core.db.enums import AyanamsaMode


@pytest.fixture(autouse=True)
def reset_providers():
    clear_providers()
    yield
    clear_providers()

def test_factory_creates_and_caches_provider():
    p1 = get_provider("swisseph", ayanamsa_mode=AyanamsaMode.lahiri)
    p2 = get_provider("swisseph")
    assert p1 is p2, "Provider factory should cache instances"

def test_factory_creates_new_on_fresh():
    p1 = get_provider("swisseph", ayanamsa_mode=AyanamsaMode.lahiri)
    p2 = get_provider("swisseph", fresh=True)
    assert p1 is not p2, "fresh=True should force new instance"

def test_factory_configures_with_defaults():
    provider = get_provider("skyfield", ayanamsa_mode=AyanamsaMode.lahiri)
    assert hasattr(provider, "lat")
    assert hasattr(provider, "tz")
    assert abs(provider.lat) > 0, "Default lat should be configured"

def test_factory_respects_custom_location():
    loc = {"lat": 28.6139, "lon": 77.2090}
    provider = get_provider("swisseph", location=loc, tz_name="Asia/Kolkata", fresh=True)
    assert provider.lat == loc["lat"]
    assert "Asia/Kolkata" in str(provider.tz)

def test_get_provider_stub():
    """Factory should load the StubProvider implementation."""
    provider = get_provider("stub")
    assert isinstance(provider, IAstroProvider)
    assert provider.__class__.__name__ == "StubProvider"

    # validate method presence
    assert hasattr(provider, "longitude")
    assert hasattr(provider, "nakshatra_index")
    assert hasattr(provider, "angular_distance")

def test_get_provider_swisseph(monkeypatch):
    """Factory should attempt to load SwissEphemProvider if pyswisseph is installed."""
    provider = get_provider("swisseph")
    assert isinstance(provider, IAstroProvider)
    assert provider.__class__.__name__ == "SwissEphemProvider"

def test_invalid_provider_type():
    """Invalid provider should raise ValueError."""
    with pytest.raises(ValueError):
        get_provider("invalid_type")
