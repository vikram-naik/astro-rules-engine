# app/core/common/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.common.models import Base

DATABASE_URL = "sqlite:///./astro_rules.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}, echo=False, future=True
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def init_db():
    Base.metadata.create_all(engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
