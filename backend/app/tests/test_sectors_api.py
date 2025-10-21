# app/tests/test_sectors_api.py
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.common.models import Base
from app.api.routes_sectors_api import router as sectors_router

@pytest.fixture(scope="module")
def test_app():
    """Create a FastAPI app with an in-memory DB."""
    app = FastAPI()
    app.include_router(sectors_router)

    # In-memory SQLite setup
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    # Dependency override
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    for route in app.router.routes:
        if hasattr(route.endpoint, "__dependencies__"):
            route.endpoint.__dependencies__["get_db"] = override_get_db

    client = TestClient(app)
    return client


def test_create_and_get_sector(test_app):
    """POST + GET sector CRUD test."""
    client = test_app

    # Create
    payload = {"code": "EQUITY", "name": "Equity Market", "description": "Stocks and shares"}
    resp = client.post("/api/sectors/", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == "EQUITY"

    # Fetch list
    resp = client.get("/api/sectors/")
    assert resp.status_code == 200
    sectors = resp.json()
    assert any(s["code"] == "EQUITY" for s in sectors)

    # Update
    update = {"name": "Equities Market", "description": "Updated description"}
    resp = client.put("/api/sectors/EQUITY", json=update)
    assert resp.status_code == 200
    assert "Updated" in resp.json()["description"]

    # Delete
    resp = client.delete("/api/sectors/EQUITY")
    assert resp.status_code == 200
    assert resp.json()["deleted"] == "EQUITY"

    # Verify deletion
    resp = client.get("/api/sectors/")
    assert all(s["code"] != "EQUITY" for s in resp.json())
