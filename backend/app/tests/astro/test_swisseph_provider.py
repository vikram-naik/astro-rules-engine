# app/core/astro/providers/tests/test_swisseph_provider.py
from datetime import datetime, date
from zoneinfo import ZoneInfo
from app.core.astro.providers.swisseph_provider import SwissEphemProvider
from app.core.db.enums import AyanamsaMode

def test_longitude_computation_and_tz_handling():
    provider = SwissEphemProvider(AyanamsaMode.lahiri)
    provider.configure(location={"lat": 19.0760, "lon": 72.8777}, tz_name="Asia/Kolkata")

    dt = datetime(2025, 10, 26, 9, 15, tzinfo=ZoneInfo("Asia/Kolkata"))
    lon_dt = provider.longitude("sun", dt)
    lon_date = provider.longitude("sun", date(2025, 10, 26))

    assert abs(lon_dt - lon_date) < 1.0, "Longitude (date vs datetime) should be close"

def test_configure_sets_topo():
    provider = SwissEphemProvider(AyanamsaMode.lahiri)
    provider.configure(location={"lat": 28.6139, "lon": 77.2090}, tz_name="Asia/Kolkata")
    assert hasattr(provider, "tz")
    assert "Asia/Kolkata" in str(provider.tz)

def test_is_retrograde_returns_bool():
    provider = SwissEphemProvider(AyanamsaMode.lahiri)
    provider.configure(location={"lat": 19.0760, "lon": 72.8777}, tz_name="Asia/Kolkata")
    dt = datetime(2025, 10, 26, 9, 15, tzinfo=ZoneInfo("Asia/Kolkata"))
    assert isinstance(provider.is_retrograde("jupiter", dt), bool)
