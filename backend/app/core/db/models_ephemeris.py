"""
app/core/db/models_ephemeris.py

Defines the EphemerisCache ORM model used to store computed planetary
positions and states for caching. This table lives in the in-memory
SQLite database managed by cache_db.py.
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String, Text, UniqueConstraint, Index

from app.core.db.db import Base

class EphemerisCache(Base):
    __tablename__ = "ephemeris_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String, nullable=False)
    ayanamsa = Column(String, nullable=False)
    tz_name = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    alt = Column(Integer, default=0)
    reference_time = Column(String, nullable=False)  # "HH:MM:SS"
    date = Column(String, nullable=False)            # "YYYY-MM-DD"
    planet = Column(String, nullable=False)

    longitude = Column(Float, nullable=False)
    longitude_dms = Column(Text)
    speed = Column(Float)
    is_retrograde = Column(Integer, default=0)
    is_stationary = Column(Integer, default=0)
    dignity = Column(String)
    combust = Column(Integer, default=0)

    transition_time_local = Column(String)
    transition_from = Column(String)
    transition_to = Column(String)

    json_extra = Column(Text)

    __table_args__ = (
        UniqueConstraint(
            "provider", "ayanamsa", "tz_name", "lat", "lon",
            "reference_time", "date", "planet",
            name="uq_ephemeris_key"
        ),
        Index(
            "idx_ephem_key",
            "provider", "ayanamsa", "tz_name", "lat", "lon", "reference_time", "date"
        ),
    )

    def to_dict(self):
        """Convenience serializer for JSON responses."""
        return {
            "provider": self.provider,
            "ayanamsa": self.ayanamsa,
            "tz_name": self.tz_name,
            "lat": self.lat,
            "lon": self.lon,
            "alt": self.alt,
            "reference_time": self.reference_time,
            "date": self.date,
            "planet": self.planet,
            "longitude": self.longitude,
            "longitude_dms": self.longitude_dms,
            "speed": self.speed,
            "is_retrograde": bool(self.is_retrograde),
            "is_stationary": bool(self.is_stationary),
            "dignity": self.dignity,
            "combust": bool(self.combust),
            "transition_time_local": self.transition_time_local,
            "transition_from": self.transition_from,
            "transition_to": self.transition_to,
        }
