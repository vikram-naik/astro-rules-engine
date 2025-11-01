"""
app/tests/ephemeris/test_ephemeris_matrix.py
Integration tests for the Ephemeris Matrix API using pytest fixtures from conftest.py.
"""

import pytest
from datetime import date
from app.core.db.astro_config import AstroConfig


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _ensure_config(db_session):
    """Guarantee a global AstroConfig row exists for testing."""
    row = db_session.get(AstroConfig, "global")
    if not row:
        row = AstroConfig(
            id="global",
            lon=72.8777,
            lat=19.0760,
            alt=0,
            tz="Asia/Kolkata",
            ayanamsa="lahiri",
            ephemeris_provider="skyfield",
            ephemeris_node_mode="mean",
            ephemeris_max_workers=2,
        )
        db_session.add(row)
        db_session.commit()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_list_providers(client, db_session):
    """Confirm both ephemeris providers are listed."""
    _ensure_config(db_session)
    resp = client.get("/api/ephemeris/providers")
    assert resp.status_code == 200
    data = resp.json()
    ids = [p["id"] for p in data]
    assert "skyfield" in ids
    assert "swisseph" in ids


def test_matrix_basic_flow(client, db_session):

    """Basic request to /api/ephemeris/matrix returns valid 7-day grid."""
    _ensure_config(db_session)
    payload = {
        "start_date": "2025-10-26",
        "location": {"lat": 19.0760, "lon": 72.8777, "alt": 0},
        "tz_name": "Asia/Kolkata",
        "ayanamsa": "lahiri",
        "reference_time": "00:00:00",
        "force_refresh": True,
    }
    resp = client.post("/api/ephemeris/matrix", json=payload)
    assert resp.status_code == 200, resp.text
    js = resp.json()

    # Basic structure
    assert "meta" in js and "rows" in js and "planets" in js
    assert len(js["rows"]) == 7
    assert len(js["planets"]) == 12
    assert js["meta"]["start_date"].startswith("2025-10-26")


def test_matrix_reads_global_config(client, db_session):
    """Ensure AstroConfig provider overrides any local payload values."""
    _ensure_config(db_session)
    row = db_session.get(AstroConfig, "global")
    row.ephemeris_provider = "swisseph"
    row.ephemeris_max_workers = 1
    db_session.add(row)
    db_session.commit()

    payload = {
        "start_date": "2025-10-27",
        "location": {"lat": 19.0760, "lon": 72.8777, "alt": 0},
        "tz_name": "Asia/Kolkata",
        "ayanamsa": "lahiri",
    }

    resp = client.post("/api/ephemeris/matrix", json=payload)
    assert resp.status_code == 200
    js = resp.json()
    assert js["meta"]["provider"] == "swisseph"


@pytest.mark.parametrize("day_offset", [0, 1])
def test_matrix_cache_behavior(client, db_session, day_offset):
    """
    The second call for same date range should hit cache and return
    identical results.
    """
    
    _ensure_config(db_session)
    start_date = date(2025, 10, 28 + day_offset)
    payload = {
        "start_date": start_date.isoformat(),
        "location": {"lat": 19.0760, "lon": 72.8777, "alt": 0},
        "tz_name": "Asia/Kolkata",
        "ayanamsa": "lahiri",
    }

    r1 = client.post("/api/ephemeris/matrix", json=payload)
    assert r1.status_code == 200
    j1 = r1.json()

    print(j1)
    # repeat to trigger cache usage
    r2 = client.post("/api/ephemeris/matrix", json=payload)
    assert r2.status_code == 200
    j2 = r2.json()
    print(j2)
    assert j1["meta"]["start_date"] == j2["meta"]["start_date"]


    sun1 = j1["rows"][0]["cells"]["sun"]["longitude"]
    sun2 = j2["rows"][0]["cells"]["sun"]["longitude"]
    assert pytest.approx(sun1, rel=1e-8) == sun2
