# app/core/astro/providers/tests/test_skyfield_provider.py
from datetime import datetime, date
from zoneinfo import ZoneInfo
from app.core.astro.providers.skyfield_provider import SkyfieldProvider
from app.core.db.enums import AyanamsaMode

def test_longitude_date_and_datetime_consistency():
    provider = SkyfieldProvider(AyanamsaMode.lahiri)
    provider.configure(location={"lat": 19.0760, "lon": 72.8777}, tz_name="Asia/Kolkata")

    dt = datetime(2025, 10, 26, 9, 15, tzinfo=ZoneInfo("Asia/Kolkata"))
    lon_dt = provider.longitude("sun", dt)
    lon_date = provider.longitude("sun", date(2025, 10, 26))

    # Should be within a fraction of a degree since same local day
    assert abs(lon_dt - lon_date) < 1.0, "Longitude (date vs datetime) should be consistent"

def test_configure_sets_topocentric_context():
    provider = SkyfieldProvider(AyanamsaMode.lahiri)
    provider.configure(location={"lat": 28.6139, "lon": 77.2090}, tz_name="Asia/Kolkata")
    assert hasattr(provider, "observer")
    assert "Asia/Kolkata" in str(provider.tz)

def test_is_retrograde_consistency():
    provider = SkyfieldProvider(AyanamsaMode.lahiri)
    provider.configure(location={"lat": 19.0760, "lon": 72.8777}, tz_name="Asia/Kolkata")
    dt = datetime(2025, 10, 26, 9, 15, tzinfo=ZoneInfo("Asia/Kolkata"))
    assert isinstance(provider.is_retrograde("mars", dt), bool)
