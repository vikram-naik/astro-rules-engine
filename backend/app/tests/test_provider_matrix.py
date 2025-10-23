"""
Tests validating all IAstroProvider implementations (Stub, SwissEphem, Skyfield)
produce compatible outputs for the same API surface.
"""

import pytest
from datetime import datetime
from app.core.db.enums import Planet
from app.core.astro.providers.stub_provider import StubProvider
from app.core.astro.providers.swisseph_provider import SwissEphemProvider
from app.core.astro.providers.skyfield_provider import SkyfieldProvider


@pytest.mark.parametrize("provider_cls", [StubProvider, SwissEphemProvider, SkyfieldProvider])
def test_provider_api_surface(provider_cls):
    """
    Verify that each provider implements the full IAstroProvider interface
    and returns valid numeric results for each method.
    """
    provider = provider_cls()
    date = datetime(2025, 1, 1)

    # Longitude checks for key planets
    for planet in ["sun", "moon", "mars", "jupiter"]:
        lon = provider.longitude(planet, date)
        assert isinstance(lon, (int, float))
        assert 0.0 <= lon < 360.0, f"{provider_cls.__name__} returned invalid longitude"

    # Node longitudes
    for node in ["rahu", "ketu"]:
        lon = provider.longitude(node, date)
        assert isinstance(lon, (int, float))
        assert 0.0 <= lon < 360.0, f"{provider_cls.__name__} returned invalid node longitude"

    # Nakshatra index
    idx = provider.nakshatra_index(123.456)
    assert isinstance(idx, int)
    assert 0 <= idx < 27

    # Nakshatra owner
    owner = provider.nakshatra_owner(idx)
    assert isinstance(owner, str)
    assert len(owner) > 0

    # Angular distance
    d = provider.angular_distance(10, 350)
    assert abs(d - 20.0) < 1e-6  # wrap-around correctness


def test_provider_longitude_consistency_tolerance():
    """
    Ensure that SwissEphemProvider and SkyfieldProvider return comparable
    longitudes for key planets (sidereal alignment tolerance).
    """
    date = datetime(2025, 1, 1)
    skyfield = SkyfieldProvider()
    swisseph = SwissEphemProvider()

    for planet in Planet.__members__:
        lon_sf = skyfield.longitude(planet, date)
        lon_sw = swisseph.longitude(planet, date)
        assert 0 <= lon_sf < 360
        assert 0 <= lon_sw < 360
        diff = abs((lon_sf - lon_sw + 180) % 360 - 180)
        assert diff < 3.0, f"{planet} difference too large: {diff}°"


def test_lahiri_alignment_debug():
    from datetime import datetime
    from app.core.astro.providers.skyfield_provider import SkyfieldProvider
    from app.core.astro.providers.swisseph_provider import SwissEphemProvider

    date = datetime(2025, 1, 1)
    sky = SkyfieldProvider()
    swe = SwissEphemProvider()

    for planet in Planet.__members__:
        sf = sky.longitude(planet, date)
        sw = swe.longitude(planet, date)
        print(f"{planet:<8} Skyfield={sf:.4f} SwissEphem={sw:.4f} Δ={abs(sf-sw):.4f}")


@pytest.mark.parametrize("provider_cls", [SwissEphemProvider, SkyfieldProvider])
@pytest.mark.parametrize("mode", ["tropical", "lahiri", "krishnamurti", "raman"])
def test_provider_mode_switch(provider_cls, mode):
    """Verify each provider respects the ayanamsa_mode setting."""
    import os
    os.environ["ASTRO_AYANAMSA_MODE"] = mode
    p = provider_cls()
    date = datetime(2025, 1, 1)
    sun = p.longitude("sun", date)
    # tropical and sidereal should differ by ~24° for Lahiri-like modes
    if mode == "tropical":
        tropical = sun
        os.environ["ASTRO_AYANAMSA_MODE"] = "lahiri"
        sidereal = provider_cls().longitude("sun", date)
        diff = abs((tropical - sidereal + 180) % 360 - 180)
        assert 23 < diff < 25

    # # In test_provider_mode_switch
    # if mode == "tropical":
    #     assert not getattr(p, "is_sidereal", True)
    # else:
    #     assert getattr(p, "is_sidereal", False)