from fastapi import FastAPI
from app.core.common.db import create_db_and_tables
from app.api.routes_rules import router as rules_router
from app.api.routes_eval import router as eval_router
from app.api.routes_correlation import router as corr_router
from app.core.common.logger import setup_logger, LoggingMiddleware


logger = setup_logger("INFO")


app = FastAPI(title="Astro Rules Engine")
app.add_middleware(LoggingMiddleware, logger=logger)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()


app.include_router(rules_router, prefix="/rules", tags=["rules"])
app.include_router(eval_router, prefix="/evaluate", tags=["evaluate"])
app.include_router(corr_router)

@app.get("/")
def root():
    return {"status": "ok", "service": "Astro Rules Engine"}