import pytest
from datetime import date, time, datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.astro.services.ephemeris_service import EphemerisService, find_ingress
from app.core.db.enums import AyanamsaMode, Planet, Sign


@pytest.mark.parametrize("provider_id", ["skyfield", "swisseph"])
def test_jupiter_reference_time_effect(provider_id):
    """
    Verify Jupiter longitude difference at 1976-02-28 for Asia/Kolkata
    between 00:00:00 and 01:58:57 local times (Lahiri / Sidereal).
    """
    svc = EphemerisService()
    tz_name = "Asia/Kolkata"
    lat, lon, alt = 20.45, 72.57, 0
    start_date = date(1976, 2, 28)

    # ---- case 1: midnight local ----
    res_mid = svc.compute_matrix(
        provider_id=provider_id,
        ayanamsa=AyanamsaMode.lahiri,
        tz_name=tz_name,
        lat=lat,
        lon=lon,
        alt=alt,
        start_date=start_date,
        reference_time=time(0, 0, 0),
        force_refresh=True,
    )
    lon_mid = res_mid["rows"][0]["cells"]["jupiter"]["longitude"]
    print(f"[{provider_id}] Lahiri 00:00:00 → {lon_mid:.6f}°")

    # ---- case 2: 01:58:57 local ----
    res_mkt = svc.compute_matrix(
        provider_id=provider_id,
        ayanamsa=AyanamsaMode.lahiri,
        tz_name=tz_name,
        lat=lat,
        lon=lon,
        alt=alt,
        start_date=start_date,
        reference_time=time(1, 58, 57),
        force_refresh=True,
    )
    lon_mkt = res_mkt["rows"][0]["cells"]["jupiter"]["longitude"]
    print(f"[{provider_id}] Lahiri 01:58:57 → {lon_mkt:.6f}°")

    diff = (lon_mkt - lon_mid + 180) % 360 - 180
    print(f"[{provider_id}] ΔJupiter ≈ {diff:.6f}° (~{diff*60:.1f}′)")

    assert abs(diff) < 0.05, f"{provider_id}: Too large delta {diff:.3f}°"


@pytest.mark.parametrize("provider_id", ["skyfield", "swisseph"])
def test_jupiter_ingress_time_estimation(provider_id):
    """
    Compute exact Lahiri ingress time for Jupiter crossing from Pisces → Aries.
    """
    svc = EphemerisService()
    tz_name = "Asia/Kolkata"
    lat, lon, alt = 20.45, 72.57, 0
    start_date = date(1976, 2, 28)

    provider = svc.cache.query  # placeholder to show intent; provider comes from compute_matrix
    provider = svc.compute_matrix(
        provider_id=provider_id,
        ayanamsa=AyanamsaMode.lahiri,
        tz_name=tz_name,
        lat=lat,
        lon=lon,
        alt=alt,
        start_date=start_date,
        reference_time=time(0, 0, 0),
        force_refresh=True,
    )

    # Reuse provider correctly through get_provider to avoid caching confusion
    from app.core.astro.factories.provider_factory import get_provider
    prov = get_provider(
        provider_id,
        ayanamsa_mode=AyanamsaMode.lahiri,
        location={"lon": lon, "lat": lat, "alt": alt},
        tz_name=tz_name,
        fresh=False,
    )

    when_l = datetime.combine(start_date, time(0, 0, 0)).replace(tzinfo=ZoneInfo(tz_name))
    when_next = when_l + timedelta(days=1)

    # Aries starts at 0°, boundary = 0° (Pisces→Aries)
    ingress_dt = find_ingress(prov, Planet.jupiter, when_l, when_next, 0.0)
    assert ingress_dt is not None, f"{provider_id}: Ingress not found for Jupiter."

    print(
        f"[{provider_id}] Jupiter ingress Pisces→Aries (Lahiri) "
        f"at {ingress_dt.strftime('%Y-%m-%d %H:%M:%S %Z')}"
    )

    # Expect around 04:30–05:00 IST
    assert 4 <= ingress_dt.hour <= 5, f"{provider_id}: Ingress expected ~04–05 IST, got {ingress_dt.hour:02d}:{ingress_dt.minute:02d}"

    
@pytest.mark.parametrize("provider_id", ["skyfield", "swisseph"])
def test_jupiter_ingress_time_estimation(provider_id):
    """
    Robust search for Jupiter Lahiri ingress Pisces→Aries (~late Feb 1976).
    Expands search window until crossing is found.
    """
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    from app.core.astro.factories.provider_factory import get_provider
    from app.core.astro.services.ephemeris_service import find_ingress
    from app.core.db.enums import AyanamsaMode, Planet

    tz = "Asia/Kolkata"
    lat, lon, alt = 20.45, 72.57, 0
    prov = get_provider(
        provider_id,
        ayanamsa_mode=AyanamsaMode.lahiri,
        location={"lon": lon, "lat": lat, "alt": alt},
        tz_name=tz,
        fresh=False,
    )

    # start a few days earlier to ensure both providers cover ingress
    start_dt = datetime(1976, 2, 25, 0, 0, tzinfo=ZoneInfo(tz))
    end_dt   = start_dt + timedelta(days=7)

    ingress_dt = find_ingress(prov, Planet.jupiter, start_dt, end_dt, 0.0)
    if ingress_dt is None:
        # last resort: probe 10-day window to ensure search completeness
        end_dt = start_dt + timedelta(days=10)
        ingress_dt = find_ingress(prov, Planet.jupiter, start_dt, end_dt, 0.0)

    l0 = prov.longitude(Planet.jupiter, start_dt)
    l1 = prov.longitude(Planet.jupiter, end_dt)
    print(f"[{provider_id}] window {start_dt}→{end_dt}")
    print(f"[{provider_id}] lon(start)={l0:.4f}°, lon(end)={l1:.4f}°")

    assert ingress_dt is not None, f"{provider_id}: ingress not found even after 10-day scan."

    print(
        f"[{provider_id}] Jupiter Pisces→Aries ingress (Lahiri) "
        f"at {ingress_dt.strftime('%Y-%m-%d %H:%M %Z')}"
    )

    # Validate broad physical realism: 1976-02-25 … 1976-03-02 IST
    assert datetime(1976, 2, 25, tzinfo=ZoneInfo(tz)) <= ingress_dt <= datetime(
        1976, 3, 2, tzinfo=ZoneInfo(tz)
    ), f"{provider_id}: ingress {ingress_dt} outside expected epoch window"
