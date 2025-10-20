# backend/app/main.py
"""
Main application entrypoint for Astro Rules Engine
--------------------------------------------------
Uses FastAPI with lifespan events, Pydantic v2 settings,
and modular routers for rules, evaluation, and correlation.
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.common.config import settings
from app.core.common.db import create_db_and_tables
from app.core.common.logger import setup_logger

# Routers
from app.api.routes_rules import router as rules_router
from app.api.routes_eval import router as eval_router
from app.api.routes_correlation import router as corr_router

# Setup logger
logger = setup_logger(settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Modern FastAPI lifespan handler.
    Handles startup and shutdown events.
    """
    logger.info("🚀 Starting Astro Rules Engine backend...")
    create_db_and_tables()
    yield
    logger.info("🛑 Shutting down Astro Rules Engine backend...")


# Initialize FastAPI app with lifespan events
app = FastAPI(
    title="Astro Rules Engine API",
    description="API for managing and evaluating astrological market rules.",
    version="1.0.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(rules_router)
app.include_router(eval_router)
app.include_router(corr_router)


@app.get("/", tags=["root"])
def root():
    """Simple health check endpoint."""
    return {"message": "Astro Rules Engine backend is running."}
