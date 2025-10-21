# app/api/routes_sectors_api.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.common.db import get_db, init_db
from app.core.common.models import Sector

router = APIRouter(prefix="/api/sectors", tags=["sectors"])


# -----------------------------
# CREATE
# -----------------------------
@router.post("/")
def create_sector(payload: dict, db: Session = Depends(get_db)):
    """Create a sector."""
    code = payload.get("code")
    if not code:
        print("code not found.... ")
        raise HTTPException(status_code=400, detail="Sector code is required")

    existing = db.scalar(select(Sector).where(Sector.code == code))
    if existing:
        raise HTTPException(status_code=400, detail=f"Sector '{code}' already exists")

    sector = Sector(
        code=code,
        name=payload.get("name"),
        description=payload.get("description"),
    )
    db.add(sector)
    db.commit()
    db.refresh(sector)
    return {"id": sector.id, "code": sector.code, "name": sector.name}


# -----------------------------
# READ
# -----------------------------
@router.get("/")
def list_sectors(db: Session = Depends(get_db)):
    """List all sectors."""
    sectors = db.scalars(select(Sector)).all()
    return [
        {"id": s.id, "code": s.code, "name": s.name, "description": s.description}
        for s in sectors
    ]


@router.get("/{code}")
def get_sector(code: str, db: Session = Depends(get_db)):
    """Get sector by code."""
    sector = db.scalar(select(Sector).where(Sector.code == code))
    if not sector:
        raise HTTPException(status_code=404, detail="Sector not found")
    return {"id": sector.id, "code": sector.code, "name": sector.name, "description": sector.description}


# -----------------------------
# UPDATE
# -----------------------------
@router.put("/{id}")
def update_sector(id: str, payload: dict, db: Session = Depends(get_db)):
    """Update a sector."""
    sector = db.scalar(select(Sector).where(Sector.id == id))
    if not sector:
        raise HTTPException(status_code=404, detail="Sector not found")

    sector.name = payload.get("name", sector.name)
    sector.description = payload.get("description", sector.description)

    db.commit()
    db.refresh(sector)
    return {"id": sector.id, "code": sector.code, "name": sector.name, "description": sector.description}


# -----------------------------
# DELETE
# -----------------------------
@router.delete("/{code}")
def delete_sector(code: str, db: Session = Depends(get_db)):
    """Delete sector by code."""
    sector = db.scalar(select(Sector).where(Sector.code == code))
    if not sector:
        raise HTTPException(status_code=404, detail="Sector not found")

    db.delete(sector)
    db.commit()
    return {"deleted": code}
