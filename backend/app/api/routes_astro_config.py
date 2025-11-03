# app/api/routes_astro_config.py

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session
from app.core.db.db import get_db
from app.core.db.astro_config import AstroConfig
from app.core.astro.factories.provider_factory import get_provider
from app.core.common.config import settings
from datetime import time as TimeType

router = APIRouter(prefix="/api/astro", tags=["astro"])


# ---------- internal helper ----------
def _get_config_row(db: Session) -> AstroConfig:
    row = db.query(AstroConfig).get("global")
    if not row:
        row = AstroConfig(
            id="global",
            lon=float(settings.astro_location_lon),
            lat=float(settings.astro_location_lat),
            alt=float(settings.astro_location_alt),
            tz=settings.astro_timezone,
            ayanamsa=settings.astro_ayanamsa_mode,
            ephemeris_provider="skyfield",
            ephemeris_node_mode="mean",
            ephemeris_max_workers=2,
        )
        db.add(row)
        db.commit()
    return row


# ---------- Routes ----------

@router.get("/config")
def get_config(db: Session = Depends(get_db)):
    """
    Returns the current astro configuration (location, ayanamsa, ephemeris settings).
    """
    row = _get_config_row(db)
    return {
        "lon": row.lon,
        "lat": row.lat,
        "alt": row.alt,
        "tz": row.tz,
        "ayanamsa": row.ayanamsa,
        "ephemeris_provider": row.ephemeris_provider,
        "ephemeris_node_mode": row.ephemeris_node_mode,
        "ephemeris_max_workers": row.ephemeris_max_workers,
        "default_reference_time": (
            row.default_reference_time.strftime("%H:%M:%S")
            if row.default_reference_time
            else "00:00:00"
        ),
    }



@router.post("/config")
def update_config(payload: dict = Body(...), db: Session = Depends(get_db)):
    """
    Updates astro configuration, including ephemeris provider and node mode.
    """
    row = _get_config_row(db)

    # Update base astro fields
    row.lon = float(payload.get("lon", row.lon))
    row.lat = float(payload.get("lat", row.lat))
    row.alt = float(payload.get("alt", row.alt))
    row.tz = payload.get("tz", row.tz)
    row.ayanamsa = payload.get("ayanamsa", row.ayanamsa)

    # Update ephemeris-specific fields
    if "ephemeris_provider" in payload:
        row.ephemeris_provider = payload["ephemeris_provider"]
    if "ephemeris_node_mode" in payload:
        row.ephemeris_node_mode = payload["ephemeris_node_mode"]
    if "ephemeris_max_workers" in payload:
        try:
            row.ephemeris_max_workers = int(payload["ephemeris_max_workers"])
        except ValueError:
                pass
    if "default_reference_time" in payload:
        try:
            h, m, s = (payload["default_reference_time"] or "00:00:00").split(":")
            row.default_reference_time = TimeType(int(h), int(m), int(s))
        except Exception:
            pass
    db.add(row)
    db.commit()

    # Re-bootstrap providers with updated ayanamsa/location
    for name in ("swisseph", "skyfield"):
        get_provider(
            name,
            ayanamsa_mode=row.ayanamsa,
            fresh=True,
            location={"lon": row.lon, "lat": row.lat, "alt": row.alt},
            tz_name=row.tz,
        )

    return {"status": "ok"}


@router.post("/config/reset")
def reset_config(db: Session = Depends(get_db)):
    """
    Resets astro configuration to factory defaults (.env / settings values).
    """
    row = _get_config_row(db)

    row.lon = float(settings.astro_location_lon)
    row.lat = float(settings.astro_location_lat)
    row.alt = float(settings.astro_location_alt)
    row.tz = settings.astro_timezone
    row.ayanamsa = settings.astro_ayanamsa_mode
    row.ephemeris_provider = "skyfield"
    row.ephemeris_node_mode = "mean"
    row.ephemeris_max_workers = 2
    row.default_reference_time = TimeType(0, 0, 0)

    db.add(row)
    db.commit()

    for name in ("swisseph", "skyfield"):
        get_provider(
            name,
            ayanamsa_mode=row.ayanamsa,
            fresh=True,
            location={"lon": row.lon, "lat": row.lat, "alt": row.alt},
            tz_name=row.tz,
        )

    return {"status": "reset"}
