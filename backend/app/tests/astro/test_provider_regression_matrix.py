import pytest
from datetime import datetime, timedelta
from app.core.db.enums import AyanamsaMode
from app.core.astro.factories.provider_factory import get_provider

def angular_diff(a, b):
    return abs((a - b + 180) % 360 - 180)

@pytest.mark.parametrize("planet", ["sun", "moon", "mars"])
@pytest.mark.parametrize("mode", [
    AyanamsaMode.lahiri,
    AyanamsaMode.raman,
    AyanamsaMode.krishnamurti,
    AyanamsaMode.tropical,
])
def test_cross_date_ayanamsa_consistency(planet, mode):
    """
    Regression test: Verify Skyfield and SwissEphem remain within 0.2°
    across 10 dates from 2020–2030 for all ayanamsa modes.
    """
    start_date = datetime(2020, 1, 1)
    dates = [start_date + timedelta(days=365 * i) for i in range(0, 10)]

    sky = get_provider("skyfield", ayanamsa_mode=mode, fresh=True)
    swe = get_provider("swisseph", ayanamsa_mode=mode, fresh=True)

    for d in dates:
        lon_sky = sky.longitude(planet, d)
        lon_swe = swe.longitude(planet, d)
        delta = angular_diff(lon_sky, lon_swe)
        assert delta < 0.2, (
            f"{planet} mismatch >0.2° on {d.date()} in mode={mode.value}: {delta:.3f}°"
        )
