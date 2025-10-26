"""
Provider mode consistency tests
===============================

✅ Validates that all supported Ayanamsa modes (Lahiri, Raman, Krishnamurti, KP, etc.)
produce consistent sidereal longitudes between Skyfield and SwissEphem providers.

These are *cross-ephemeris verification tests* — ensuring both engines interpret
ayanamsa offsets identically, regardless of internal computational model.

Runs a light-weight matrix validation:
    - Same planet (Sun) on a fixed date
    - Compare longitudes across both providers
    - Log and assert difference < 0.2° across all supported modes

Additionally:
    - Computes the offset Δ(mode) = mode.lon - Lahiri.lon for each provider
    - Validates inter-provider agreement for each Δ(mode)
"""

import pytest
from datetime import datetime
from app.core.astro.factories.provider_factory import get_provider
from app.core.db.enums import AyanamsaMode


@pytest.fixture(scope="module")
def when():
    """Reference date for sidereal longitude comparisons."""
    return datetime(2025, 1, 1, 0, 0)


@pytest.fixture(scope="module")
def modes():
    """Supported ayanamsa modes to test."""
    return ["lahiri", "raman", "krishnamurti", "tropical"]


@pytest.fixture(scope="module")
def planet():
    """Reference planet to check offsets (Sun is ideal, low daily variation)."""
    return "sun"


def compute_longitudes(mode, planet, when):
    """Helper: get longitudes from both providers under given mode."""
    ayanamsa_mode = AyanamsaMode(mode.lower())

    sky = get_provider("skyfield", ayanamsa_mode=ayanamsa_mode, fresh=True)
    swe = get_provider("swisseph", ayanamsa_mode=ayanamsa_mode, fresh=True)
    # sky.ayanamsa_mode = swe.ayanamsa_mode = mode

    lon_sky = sky.longitude(planet, when)
    lon_swe = swe.longitude(planet, when)
    return lon_sky, lon_swe


def angular_diff(a, b):
    """Returns shortest angular difference (abs)."""
    return abs((a - b + 180) % 360 - 180)


@pytest.mark.parametrize("mode", ["lahiri", "raman", "krishnamurti", "tropical"])
def test_mode_longitudes_within_tolerance(mode, planet, when):
    """
    Ensure that for each ayanamsa mode, Skyfield and SwissEphem give nearly identical results.

    Expected tolerance: ≤ 0.2° for all supported modes.
    """
    lon_sky, lon_swe = compute_longitudes(mode, planet, when)
    delta = angular_diff(lon_sky, lon_swe)
    print(f"[INFO] {mode:<14} Δ(Skyfield–SwissEphem) = {delta:.4f}°")
    assert delta < 0.2, f"Inconsistent longitude for {mode}: {delta:.4f}°"


def test_mode_offsets_vs_lahiri(planet, when, modes):
    """
    Compare each ayanamsa mode’s sidereal offset vs Lahiri baseline.

    Ensures Δ(mode) = mode.lon - lahiri.lon is stable across providers.
    Tolerance widened slightly to allow for rounding differences in ayanamsa computation.
    """
    ref_sky, ref_swe = compute_longitudes("lahiri", planet, when)

    results = []
    for mode in modes:
        lon_sky, lon_swe = compute_longitudes(mode, planet, when)
        offset_sky = angular_diff(lon_sky, ref_sky)
        offset_swe = angular_diff(lon_swe, ref_swe)
        delta_between_providers = abs(offset_sky - offset_swe)
        results.append((mode, offset_sky, offset_swe, delta_between_providers))

        print(
            f"[SUMMARY] {mode:<14} offset_sky={offset_sky:8.4f}°, "
            f"offset_swe={offset_swe:8.4f}°, Δ={delta_between_providers:7.4f}°"
        )

        assert delta_between_providers < 0.2, (
            f"Ayanamsa offset mismatch for {mode}: Skyfield={offset_sky:.3f}°, "
            f"SwissEphem={offset_swe:.3f}°"
        )

    print("\n[MODE OFFSET MATRIX]")
    print("Mode".ljust(15), "Skyfield(Δ°)".rjust(14), "SwissEphem(Δ°)".rjust(18))
    for mode, off_sky, off_swe, _ in results:
        print(f"{mode:<15}{off_sky:>12.4f}{off_swe:>18.4f}")

def test_raman_minus_lahiri_offset_is_consistent(when):
    sky_raman = get_provider("skyfield", ayanamsa_mode=AyanamsaMode.raman, fresh=True)
    sky_lahiri = get_provider("skyfield", ayanamsa_mode=AyanamsaMode.lahiri, fresh=True)
    lon_raman = sky_raman.longitude("sun", when)
    lon_lahiri = sky_lahiri.longitude("sun", when)

    # Minimal circular difference
    delta = abs((lon_raman - lon_lahiri + 180) % 360 - 180)
    assert abs(delta - 1.446) < 0.05, f"Unexpected Raman–Lahiri offset: {delta:.3f}°"

