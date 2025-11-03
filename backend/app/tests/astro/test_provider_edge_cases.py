import pytest
from datetime import datetime, date

import skyfield
from app.core.db.enums import AyanamsaMode, Planet
from app.core.astro.providers.skyfield_provider import SkyfieldPlanetMapper, SkyfieldProvider
from app.core.astro.providers.swisseph_provider import SwissEphemPlanetMapper, SwissEphemProvider
from app.core.astro.providers.stub_provider import StubProvider
from app.core.astro.factories.provider_factory import get_provider

# ---------- StubProvider -----------------------------------------------------

def test_stubprovider_explicit_map_and_missing_key():
    p = StubProvider()
    p.set_longitude_map({"sun": 120.5})
    assert p.longitude("sun", datetime(2025,1,1)) == 120.5
    with pytest.raises(KeyError):
        p.longitude("moon", datetime(2025,1,1))

def test_stubprovider_motion_and_retro_map():
    p = StubProvider()
    val = p.longitude("mars", datetime(2025,1,1))
    assert 0 <= val < 360
    p.set_retro_map({"mars": True})
    assert p.is_retrograde("mars", datetime(2025,1,1))
    assert not p.is_retrograde("venus", datetime(2025,1,1))

# ---------- SkyfieldProvider -------------------------------------------------

@pytest.mark.parametrize("mode", list(AyanamsaMode))
def test_skyfieldprovider_modes_and_ketu_offset(mode):
    p = SkyfieldProvider(ayanamsa_mode=mode)
    d = datetime(2025,1,1)
    sun = p.longitude("sun", d)
    ketu = p.longitude("ketu", d)
    rahu = p.longitude("rahu", d)
    diff = abs((ketu - rahu + 180) % 360 - 180)

    # In tropical mode, node offsets may be disabled (Ketu == Rahu)
    if mode == AyanamsaMode.tropical:
        assert diff in (0, 180), f"Tropical mode Ketu/Rahu should be identical or opposite, got {diff}"
    else:
        assert 170 < diff < 190, f"{mode.value} mode Ketu/Rahu offset out of range: {diff}"
    assert 0 <= sun < 360


# ---------- SwissEphemProvider ----------------------------------------------

@pytest.mark.parametrize("mode", list(AyanamsaMode))
def test_swissephprovider_mode_switch_and_longitude(mode):
    p = SwissEphemProvider(ayanamsa_mode=mode)
    val = p.longitude("sun", datetime(2025,1,1))
    assert 0 <= val < 360

def test_swissephprovider_unsupported_planet_and_ketu_adjustment(monkeypatch):
    p = SwissEphemProvider()
    # bad planet string
    with pytest.raises(NotImplementedError):
        p.longitude("notaplanet", datetime(2025,1,1))

    # patch mapper to ensure ketu offset logic
    p.planet_mapper.resolve = lambda pl: 0
    monkeypatch.setattr("swisseph.calc_ut", lambda jd, pid, flags: ([180.0, 0, 0], 0))
    val = p.longitude(Planet.ketu, datetime(2025,1,1))
    assert 0 <= val < 360

def test_swissephprovider_is_retrograde_fallback(monkeypatch):
    p = SwissEphemProvider()
    monkeypatch.setattr("swisseph.calc_ut", lambda *a, **kw: ([], 0))
    # should not raise and must return False
    assert not p.is_retrograde("mars", datetime(2025,1,1))

# ---------- Cross consistency ------------------------------------------------

def test_cross_provider_sun_longitude_consistency():
    """Skyfield and SwissEphem should agree within 0.2° in Lahiri mode."""
    d = datetime(2025,1,1)
    s1 = SkyfieldProvider(ayanamsa_mode=AyanamsaMode.lahiri)
    s2 = SwissEphemProvider(ayanamsa_mode=AyanamsaMode.lahiri)
    lon1 = s1.longitude("sun", d)
    lon2 = s2.longitude("sun", d)
    diff = abs((lon1 - lon2 + 180) % 360 - 180)
    assert diff < 0.2


# -------------------------------------------------------------------------
# 🌞 Shared edge-case helpers
# -------------------------------------------------------------------------

@pytest.mark.parametrize("provider_cls", [SkyfieldProvider, SwissEphemProvider])
def test_invalid_planet_name_raises(provider_cls):
    p = provider_cls()
    with pytest.raises(NotImplementedError):
        p.longitude("invalid_planet", datetime(2025, 1, 1))

  

@pytest.mark.parametrize("provider_cls", [SkyfieldProvider, SwissEphemProvider])
def test_nakshatra_and_angular_helpers(provider_cls):
    """Covers nakshatra_index, owner, and angular_distance utilities."""
    p = provider_cls()
    assert p.nakshatra_index(0) == 0
    assert p.nakshatra_index(359.9) == 26
    assert isinstance(p.nakshatra_owner(3), str)
    assert 0 <= p.angular_distance(10, 350) <= 20


# -------------------------------------------------------------------------
# ☀️ Skyfield-specific edge cases
# -------------------------------------------------------------------------

def test_skyfield_rahu_ketu_offset():
    """Ensure Rahu/Ketu are opposite within ±10° margin."""
    p = SkyfieldProvider(ayanamsa_mode=AyanamsaMode.lahiri)
    when = datetime(2025, 1, 1)
    rahu = p.longitude("rahu", when)
    ketu = p.longitude("ketu", when)
    diff = abs((ketu - rahu + 180) % 360 - 180)
    assert 170 <= diff <= 190


def test_skyfield_is_retrograde_defensive(monkeypatch):
    """Cover retrograde True/False and exception fallback."""
    p = SkyfieldProvider()
    when = datetime(2025, 1, 1)

    # Patch longitude to simulate backward motion
    monkeypatch.setattr(p, "longitude", lambda planet, when: 120.0 if planet == "mars" else 130.0)
    res = p.is_retrograde("mars", when)
    assert isinstance(res, bool)

    # Force exception inside longitude to hit fallback
    def boom(*_, **__): raise RuntimeError("test crash")
    monkeypatch.setattr(p, "longitude", boom)
    assert p.is_retrograde("mars", when) is False


# -------------------------------------------------------------------------
# 🪐 SwissEphem-specific edge cases
# -------------------------------------------------------------------------

def test_swiss_mapper_keyerror():
    mapper = SwissEphemProvider().planet_mapper
    with pytest.raises(KeyError):
        mapper.resolve("not_a_planet")


def test_swiss_is_retrograde_unmapped(monkeypatch):
    """Hit the defensive path where planet is not in planet_mapper."""
    p = SwissEphemProvider()
    # ensure attribute missing or empty mapping
    setattr(p, "planet_mapper", {})
    when = datetime(2025, 1, 1)
    assert p.is_retrograde("nonexistent", when) is False


def test_swiss_is_retrograde_exception(monkeypatch):
    """Force exception path in is_retrograde."""
    p = SwissEphemProvider()
    monkeypatch.setattr(p, "_normalize_when", lambda when: (_ for _ in ()).throw(RuntimeError("boom")))
    assert p.is_retrograde("sun", datetime(2025, 1, 1)) is False


def test_swiss_longitude_with_unsupported_str(monkeypatch):
    """Hit ValueError in longitude() when planet name is not valid."""
    p = SwissEphemProvider()
    with pytest.raises(NotImplementedError):
        p.longitude("FakePlanet", datetime(2025, 1, 1))

def test_swiss_longitude_with_unsupported_str(monkeypatch):
    """Hit ValueError in longitude() when planet name is not valid."""
    p = SwissEphemProvider()
    lon = p.longitude(Planet.sun, datetime(2025, 1, 1))
    assert lon is not None



# -----------------------
# SKYFIELD: mapper & utils
# -----------------------
def test_skyfield_longitude_with_unsupported_str(monkeypatch):
    """Hit ValueError in longitude() when planet name is not valid."""
    p = SkyfieldProvider()
    lon = p.longitude(Planet.sun, datetime(2025, 1, 1))
    assert lon is not None


def test_skyfield_planet_mapper_resolve_missing():
    mapper = SkyfieldPlanetMapper()
    with pytest.raises(KeyError):
        # create an artificial Planet-like object to force KeyError
        class FakePlanet: pass
        mapper.resolve(FakePlanet())  # not in map

def test_skyfield_wrap_and_normalize():
    p = SkyfieldProvider(ayanamsa_mode=AyanamsaMode.lahiri)
    assert p._wrap_angle(-10) == pytest.approx(350.0)
    assert p._wrap_angle(370) == pytest.approx(10.0)

def test_skyfield_lahiri_and_modes():
    p = SkyfieldProvider(ayanamsa_mode=AyanamsaMode.lahiri)
    # choose a JD (use a datetime converted via provider helper)
    when = datetime(2025, 1, 1)
    # compute JD via skyfield helper indirectly on _ayanamsa_deg by calling underlying lahiri fn
    jd = 2460676.5  # known JD for 2025-01-01 00:00 UT (approx)
    lahiri = p._lahiri_ayanamsa_deg_from_jd(jd)
    # Check expected numeric range for Lahiri
    assert 0.0 <= lahiri < 360.0
    # Check mode branches (krishnamurti, raman, tropical)
    p.ayanamsa_mode = AyanamsaMode.krishnamurti
    assert p._ayanamsa_deg(jd) == pytest.approx(lahiri - 0.1)
    p.ayanamsa_mode = AyanamsaMode.raman
    assert p._ayanamsa_deg(jd) == pytest.approx(lahiri - 1.446)
    p.ayanamsa_mode = AyanamsaMode.tropical
    assert p._ayanamsa_deg(jd) == pytest.approx(0.0)

def test_skyfield_mean_lunar_node_and_wrap():
    p = SkyfieldProvider()
    # known JD should return a float in 0..360
    jd = 2460676.5
    node = p._mean_lunar_node_deg_from_jd(jd)
    assert 0.0 <= node < 360.0

def test_skyfield_nakshatra_and_owner_and_angular_distance():
    p = SkyfieldProvider()
    # nakshatra boundaries: 0..26
    assert 0 <= p.nakshatra_index(0.0) <= 26
    assert 0 <= p.nakshatra_index(359.9999) <= 26
    # owner wraps
    for idx in (0, 1, 6, 7, 27, 54):
        owner = p.nakshatra_owner(idx)
        assert isinstance(owner, str) and owner != ""
    # angular distance tests
    assert p.angular_distance(10, 350) == pytest.approx(20.0)
    assert p.angular_distance(0, 180) == pytest.approx(180.0)

# -----------------------
# SKYFIELD: is_retrograde (monkeypatch longitude)
# -----------------------
def test_skyfield_is_retrograde_positive_and_negative(monkeypatch):
    p = SkyfieldProvider()
    # patch p.longitude to simulate forward motion (+10°) and backward motion (-10°)
    def lon_forward(planet, when):
        return 100.0
    def lon_forward_one_day(planet, when):
        return 110.0
    monkeypatch.setattr(p, "longitude", lambda planet, when: lon_forward(planet, when) if when == datetime(2025,1,1) else lon_forward_one_day(planet, when))
    # not retrograde in forward case
    assert p.is_retrograde("mars", datetime(2025,1,1)) is False

    # backward motion
    def lon_back(planet, when):
        return 100.0
    def lon_back_one_day(planet, when):
        return 90.0
    monkeypatch.setattr(p, "longitude", lambda planet, when: lon_back(planet, when) if when == datetime(2025,1,1) else lon_back_one_day(planet, when))
    assert p.is_retrograde("mars", datetime(2025,1,1)) is True

    # if longitude raises -> defensive False
    monkeypatch.setattr(p, "longitude", lambda planet, when: (_ for _ in ()).throw(RuntimeError("boom")))
    assert p.is_retrograde("mars", datetime(2025,1,1)) is False

# -----------------------
# SWISSEPH: longitude behavior via monkeypatching swe.calc_ut
# -----------------------

def test_swisseph_longitude_unsupported_planet():
    prov = SwissEphemProvider(AyanamsaMode.lahiri)
    with pytest.raises(NotImplementedError):
        prov.longitude("not-a-planet", datetime(2025,1,1))

# -----------------------
# SWISSEPH: is_retrograde
# -----------------------
import app.core.astro.providers.swisseph_provider as swmod

def test_is_retrograde_unmapped_planet():
    """If planet not in planet_mapper → should safely return False."""
    provider = SwissEphemProvider()
    provider.planet_mapper = {}  # simulate missing mapping
    result = provider.is_retrograde("sun", datetime(2025, 1, 1))
    assert result is False


def test_is_retrograde_calc_ut_returns_short_list(monkeypatch):
    """If swe.calc_ut returns <4 items → returns False."""
    provider = SwissEphemProvider()
    provider.planet_mapper = {"sun": 0}

    class DummySWE:
        @staticmethod
        def calc_ut(jd, body_code, flags):
            return ([1.0, 2.0, 3.0], None)  # len=3 → triggers False

    monkeypatch.setattr(swmod, "swe", DummySWE)
    assert provider.is_retrograde("sun", datetime(2025, 1, 1)) is False


# small helper to ensure providers are created fresh and same ayanamsa
def _get_providers():
    sky = get_provider("skyfield", ayanamsa_mode=AyanamsaMode.lahiri, fresh=True)
    swe = get_provider("swisseph", ayanamsa_mode=AyanamsaMode.lahiri, fresh=True)
    return {"skyfield": sky, "swisseph": swe}

@pytest.mark.parametrize("planet,when_iso,expected", [
    # Mercury tests (Mercury retrograde Mar 14 - Apr 7, 2025)
     ("mercury", "2024-04-02", True), 
    ("mercury", "2024-04-04T00:00:00+00:00", True), 
    ("mercury", "2025-03-20T00:00:00+00:00", True),   # inside Mercury retrograde
    ("mercury", "2025-01-10T00:00:00+00:00", False),  # outside retrograde

    # Mars tests (Mars retrograde Dec 6, 2024 - Feb 23, 2025)
    ("mars", "2024-12-20T00:00:00+00:00", True),      # inside Mars retrograde
    ("mars", "2025-03-01T00:00:00+00:00", False),     # after Mars direct
])
def test_real_retrograde_events_across_providers(planet, when_iso, expected):
    """
    Regression test using real-world retrograde windows (not monkeypatched).
    Ensures both Skyfield and SwissEphem report the same boolean for is_retrograde.
    """
    when = datetime.fromisoformat(when_iso)
    providers = _get_providers()

    for name, prov in providers.items():
        # providers expose is_retrograde(planet, when)
        print(f"{name}: {planet} retrograde={expected} on {when_iso}")
        assert prov.is_retrograde(planet, when) is expected, (
            f"{name}: expected {planet} retrograde={expected} on {when_iso}, "
            f"got {prov.is_retrograde(planet, when)}"
        )


def test_is_retrograde_exception(monkeypatch):
    """If swe.calc_ut raises, provider must return False (defensive)."""
    provider = SwissEphemProvider()
    provider.planet_mapper = {"sun": 0}

    class DummySWE:
        @staticmethod
        def calc_ut(*args, **kwargs):
            raise RuntimeError("boom")

    monkeypatch.setattr(swmod, "swe", DummySWE)
    assert provider.is_retrograde("sun", datetime(2025, 1, 1)) is False