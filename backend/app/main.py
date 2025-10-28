# app/main.py
from fastapi.templating import Jinja2Templates
from app.core.db.db import Base, engine
from app.core.common.logger import LoggingMiddleware, setup_logger
from app.core.common.config import settings

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from contextlib import asynccontextmanager

from app.api.routes_rules import router as rules_router
from app.api.routes_sectors_api import router as sectors_router
from app.api.routes_reference_api import router as ref_router
from app.api.routes_rule_event import router as rule_event_router
from app.api.routes_astro_config import router as astro_config_router

# Setup logger
logger = setup_logger(settings.log_level)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context for startup and shutdown logic."""
    # ✅ Startup: initialize database tables
    logger.info("Creating database schema...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database schema ready.")
    yield
    # ✅ Shutdown: if any cleanup is needed later
    logger.info("Shutting down application.")


# ✅ Pass lifespan into FastAPI constructor
app = FastAPI(title="Astro Rules Engine", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

app.add_middleware(LoggingMiddleware)

# ✅ Register routers
app.include_router(sectors_router)
app.include_router(rules_router)
app.include_router(ref_router)
app.include_router(rule_event_router)
app.include_router(astro_config_router)
# this import is done here to avoid circular deps as ui_router needs templates defined.
from app.api.routes_ui_workbench import router as ui_router
app.include_router(ui_router)

@app.get("/")
def root():
    """Health check endpoint."""
    return {"message": "Astro Rules Engine API is running."}
