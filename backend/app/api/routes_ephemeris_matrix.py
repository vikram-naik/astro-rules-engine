"""
app/api/routes_ephemeris_matrix.py — Clean version
Uses SQLAlchemy 2.0 `Session.get()` and relies on cache DB being pre-initialized.
"""

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, Field
from datetime import date, time
from typing import Optional
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.db.astro_config import AstroConfig
from app.core.astro.services.ephemeris_service import EphemerisService
from app.core.db.enums import AyanamsaMode

router = APIRouter(prefix="/api/ephemeris", tags=["ephemeris"])


class MatrixRequest(BaseModel):
    start_date: date
    reference_time: time = time(0, 0, 0)
    force_refresh: bool = False


@router.get("/providers")
def list_providers(cache_db: Session = Depends(get_db)):
    """Return available ephemeris providers."""
    svc = EphemerisService(cache_db)
    return svc.get_providers()


@router.post("/matrix")
def post_matrix(
    payload: MatrixRequest = Body(...),
    db: Session = Depends(get_db),
    cache_db: Session = Depends(get_db),
):
    """Generate a 7-day ephemeris matrix."""

    cfg = db.get(AstroConfig, "global")
    if not cfg:
        raise HTTPException(status_code=500, detail="Astro configuration not initialized")

    svc = EphemerisService(cache_db)

    try:
        result = svc.compute_matrix(
            provider_id=cfg.ephemeris_provider,
            ayanamsa=AyanamsaMode[cfg.ayanamsa],
            tz_name=cfg.tz,
            lat=cfg.lat,
            lon=cfg.lon,
            alt=int(cfg.alt or 0),
            start_date=payload.start_date,
            reference_time=payload.reference_time,
            force_refresh=payload.force_refresh,
            max_workers=cfg.ephemeris_max_workers,
            node_mode=cfg.ephemeris_node_mode,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
