"""
Database package initializer.

Ensures all models are imported so SQLAlchemy Base.metadata
includes every table before create_all() or migrations.
"""

from app.core.db.db import Base, engine, SessionLocal, get_db

# Import core models first (these define Rule, Outcome, Sector, etc.)
from app.core.db import models  

# Import analysis models next (these define RuleEvent, CorrelationResult, etc.)
from app.core.db import models_analysis  


__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "models",
    "models_analysis",
]
