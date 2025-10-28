# app/models/astro_config.py
from sqlalchemy import Column, Float, String
from app.core.db.db import Base

class AstroConfig(Base):
    __tablename__ = "astro_config"
    id = Column(String, primary_key=True, default="global")
    lon = Column(Float)
    lat = Column(Float)
    alt = Column(Float, default=0.0)
    tz = Column(String, default="UTC")
    ayanamsa = Column(String, default="lahiri")
