from datetime import datetime

import pytest
from app.core.astro.providers.skyfield_provider import SkyfieldProvider

def test_skyfield_provider_longitudes():
    p = SkyfieldProvider()
    dt = datetime(2025, 1, 1)
    lon_sun = p.longitude("sun", dt)
    lon_rahu = p.longitude("rahu", dt)
    lon_ketu = p.longitude("ketu", dt)

    assert 0 <= lon_sun < 360
    assert 0 <= lon_rahu < 360
    assert (lon_ketu - lon_rahu) % 360 == pytest.approx(180.0, abs=1e-6)
