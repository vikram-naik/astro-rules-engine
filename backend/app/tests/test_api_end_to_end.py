# app/tests/test_api_end_to_end.py
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.common.models import Base
from app.api.routes_rules import router as rules_router
from app.api.routes_sectors_api import router as sectors_router
from app.core.common.db import get_db


@pytest.fixture(scope="module")
def test_app():
    """FastAPI test app with shared in-memory SQLite."""
    app = FastAPI()
    app.include_router(sectors_router)
    app.include_router(rules_router)

    # ✅ Shared in-memory DB across all sessions
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # 👈 this ensures shared memory across connections
        echo=False,
        future=True,
    )

    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # ✅ Override all router dependencies to use shared session
    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    return client


def test_end_to_end_rules_and_sectors(test_app):
    client = test_app

    # 1️⃣ Create sector
    sector_payload = {"code": "EQUITY", "name": "Equity Market", "description": "Stock-related sector"}
    resp = client.post("/api/sectors/", json=sector_payload)
    assert resp.status_code == 200, resp.text
    assert resp.json()["code"] == "EQUITY"

    # 2️⃣ Create rule linked to that sector
    rule_payload = {
        "rule_id": "R001",
        "name": "Saturn in Capricorn",
        "description": "Commodities steady under Saturn in Capricorn",
        "confidence": 0.9,
        "enabled": True,
        "conditions": [{"planet": "saturn", "relation": "in_sign", "target": "capricorn"}],
        "outcomes": [{"effect": "Bullish", "weight": 1.0, "sector_id": 1}],
    }
    resp = client.post("/api/rules/", json=rule_payload)
    assert resp.status_code == 200, resp.text
    assert resp.json()["rule_id"] == "R001"

    # 3️⃣ Fetch rules
    resp = client.get("/api/rules/")
    assert resp.status_code == 200
    rules = resp.json()
    assert len(rules) == 1
    assert rules[0]["rule_id"] == "R001"

    # 4️⃣ Update rule
    update_payload = {
        "name": "Saturn in Capricorn (Updated)",
        "conditions": [{"planet": "saturn", "relation": "retrograde"}],
        "outcomes": [{"effect": "Bearish", "weight": 0.5, "sector_id": 1}],
    }
    resp = client.put("/api/rules/R001", json=update_payload)
    assert resp.status_code == 200
    assert "Updated" in resp.text

    # 5️⃣ Delete rule
    resp = client.delete("/api/rules/R001")
    assert resp.status_code == 200
    assert resp.json()["deleted"] == "R001"

    # 6️⃣ Ensure sector still exists
    resp = client.get("/api/sectors/")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    # 7️⃣ Delete sector
    resp = client.delete("/api/sectors/EQUITY")
    assert resp.status_code == 200
    assert resp.json()["deleted"] == "EQUITY"

    # 8️⃣ Verify cleanup
    resp = client.get("/api/sectors/")
    assert resp.status_code == 200
    assert resp.json() == []
