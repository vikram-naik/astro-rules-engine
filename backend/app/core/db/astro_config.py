# app/core/db/astro_config.py

from sqlalchemy import Column, Float, String, Integer
from app.core.db.db import Base


class AstroConfig(Base):
    __tablename__ = "astro_config"

    id = Column(String, primary_key=True, default="global")

    # Location
    lon = Column(Float)
    lat = Column(Float)
    alt = Column(Float, default=0.0)

    # Time & Ayanamsa
    tz = Column(String, default="UTC")
    ayanamsa = Column(String, default="lahiri")

    # ---- Ephemeris Settings ----
    ephemeris_provider = Column(String, default="skyfield")     # skyfield | swisseph
    ephemeris_node_mode = Column(String, default="mean")         # mean | true
    ephemeris_max_workers = Column(Integer, default=2)           # concurrency for ephemeris
