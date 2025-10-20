"""
Tests for Provider Factory
--------------------------
Verifies that get_provider() dynamically loads and instantiates
the correct provider classes via importlib.
"""

from core.astro.factories.provider_factory import get_provider
from core.astro.interfaces.i_astro_provider import IAstroProvider
import pytest


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
