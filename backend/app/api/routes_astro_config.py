# app/api/routes/astro_config.py
from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session
from app.core.db.db import get_db
from app.core.db.astro_config import AstroConfig
from app.core.astro.factories.provider_factory import get_provider
from app.core.common.config import settings

router = APIRouter(prefix="/api/astro", tags=["astro"])

def _get_config_row(db: Session) -> AstroConfig:
    row = db.query(AstroConfig).get("global")
    if not row:
        row = AstroConfig(
            id="global",
            lon=float(settings.astro_location_lon),
            lat=float(settings.astro_location_lat),
            alt=float(settings.astro_location_alt),
            tz=settings.astro_timezone,
            ayanamsa=settings.astro_ayanamsa_mode
        )
        db.add(row)
        db.commit()
    return row

@router.get("/config")
def get_config(db: Session = Depends(get_db)):
    row = _get_config_row(db)
    return dict(lon=row.lon, lat=row.lat, alt=row.alt, tz=row.tz, ayanamsa=row.ayanamsa)

@router.post("/config")
def update_config(payload: dict = Body(...), db: Session = Depends(get_db)):
    row = _get_config_row(db)
    row.lon = float(payload.get("lon", row.lon))
    row.lat = float(payload.get("lat", row.lat))
    row.alt = float(payload.get("alt", row.alt))
    row.tz = payload.get("tz", row.tz)
    row.ayanamsa = payload.get("ayanamsa", row.ayanamsa)
    db.add(row)
    db.commit()
    # rebootstrap both providers
    for name in ("swisseph", "skyfield"):
        get_provider(name, ayanamsa_mode=row.ayanamsa, fresh=True,
                     location={"lon": row.lon, "lat": row.lat, "alt": row.alt},
                     tz_name=row.tz)
    return {"status": "ok"}

@router.post("/config/reset")
def reset_config(db: Session = Depends(get_db)):
    row = _get_config_row(db)
    row.lon = float(settings.astro_location_lon)
    row.lat = float(settings.astro_location_lat)
    row.alt = float(settings.astro_location_alt)
    row.tz = settings.astro_timezone
    row.ayanamsa = settings.astro_ayanamsa_mode
    db.add(row)
    db.commit()
    for name in ("swisseph", "skyfield"):
        get_provider(name, ayanamsa_mode=row.ayanamsa, fresh=True,
                     location={"lon": row.lon, "lat": row.lat, "alt": row.alt},
                     tz_name=row.tz)
    return {"status": "reset"}
