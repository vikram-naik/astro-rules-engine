# app/core/common/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./astro_rules.db"

# --- Declarative Base ---
Base = declarative_base()

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
