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

import pytest
from datetime import datetime
from app.core.astro.providers.skyfield_provider import SkyfieldProvider
from app.core.astro.providers.swisseph_provider import SwissEphemProvider
from app.core.astro.providers.stub_provider import StubProvider


@pytest.mark.parametrize("provider_cls", [SkyfieldProvider, SwissEphemProvider, StubProvider])
def test_nakshatra_index_and_owner_consistency(provider_cls):
    """
    Verify nakshatra_index(...) and nakshatra_owner(...) produce consistent results
    for key planetary longitudes across providers.
    """
    date = datetime(2025, 1, 1)
    provider = provider_cls()

    # Test over key planets
    for planet in ["sun", "moon", "mars", "jupiter"]:
        lon = provider.longitude(planet, date)
        nak_idx = provider.nakshatra_index(lon)
        owner = provider.nakshatra_owner(nak_idx)

        assert 0 <= nak_idx <= 26, f"Invalid nakshatra index for {planet}: {nak_idx}"
        assert isinstance(owner, str) and owner, f"Empty nakshatra owner for {planet}"

        print(f"{provider_cls.__name__}: {planet} → Nakshatra #{nak_idx} ({owner})")


def test_nakshatra_index_owner_matrix_tolerance():
    """
    Compare nakshatra indices and owners across providers to ensure consistent
    nakshatra boundaries and ownership.
    """
    date = datetime(2025, 1, 1)
    skyfield = SkyfieldProvider()
    swisseph = SwissEphemProvider()

    for planet in ["sun", "moon", "mars", "jupiter"]:
        lon_sf = skyfield.longitude(planet, date)
        lon_sw = swisseph.longitude(planet, date)

        nak_sf = skyfield.nakshatra_index(lon_sf)
        nak_sw = swisseph.nakshatra_index(lon_sw)
        diff = abs(nak_sf - nak_sw)

        assert diff <= 1, f"Nakshatra mismatch for {planet}: {nak_sf} vs {nak_sw}"

        owner_sf = skyfield.nakshatra_owner(nak_sf)
        owner_sw = swisseph.nakshatra_owner(nak_sw)

        assert owner_sf == owner_sw, f"Owner mismatch for {planet}: {owner_sf} vs {owner_sw}"

        print(
            f"{planet:<8} SF={nak_sf:02d}({owner_sf})  "
            f"SW={nak_sw:02d}({owner_sw})  Δ={diff}"
        )


@pytest.mark.parametrize("provider_cls", [SkyfieldProvider, SwissEphemProvider, StubProvider])
def test_angular_distance_consistency(provider_cls):
    """
    Validate angular_distance() function across providers for circular distance logic.
    """
    provider = provider_cls()

    cases = [
        (10, 350, 20),
        (0, 180, 180),
        (45, 90, 45),
        (270, 90, 180),
        (359, 1, 2),
    ]

    for a, b, expected in cases:
        result = provider.angular_distance(a, b)
        assert abs(result - expected) < 1e-6, f"Incorrect angular distance for {a},{b}"

        print(f"{provider_cls.__name__}: angular_distance({a},{b}) = {result:.6f}")


def test_angular_distance_matrix_tolerance():
    """
    Compare angular_distance results between providers to ensure consistent
    modular arithmetic and wrapping.
    """
    skyfield = SkyfieldProvider()
    swisseph = SwissEphemProvider()

    for a, b in [(10, 350), (45, 90), (270, 90), (359, 1)]:
        d_sf = skyfield.angular_distance(a, b)
        d_sw = swisseph.angular_distance(a, b)

        diff = abs(d_sf - d_sw)
        assert diff < 1e-6, f"Angular distance mismatch: {d_sf} vs {d_sw}"

        print(f"Δ angular_distance({a},{b}) = {diff:.8f}")
