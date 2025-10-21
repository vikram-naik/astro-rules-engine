# app/tests/test_rules_api.py
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.common.models import Base
from app.api.routes_rules import router as rules_router
from app.api.routes_sectors_api import router as sectors_router


@pytest.fixture(scope="module")
def test_app():
    """Spin up FastAPI app with both routers and in-memory DB."""
    app = FastAPI()
    app.include_router(sectors_router)
    app.include_router(rules_router)

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

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


def test_rule_crud_flow(test_app):
    client = test_app

    # Create reference sector
    sector_payload = {"code": "COMMODITY", "name": "Commodity Market", "description": "Raw materials"}
    resp = client.post("/api/sectors/", json=sector_payload)
    assert resp.status_code == 200

    # Create rule with condition + outcome
    rule_payload = {
        "rule_id": "R001",
        "name": "Saturn in Capricorn",
        "description": "Commodities steady under Saturn in Capricorn",
        "confidence": 0.8,
        "enabled": True,
        "conditions": [
            {"planet": "saturn", "relation": "in_sign", "target": "capricorn"}
        ],
        "outcomes": [
            {"effect": "Bullish", "weight": 1.0, "sector_id": 1}
        ]
    }
    resp = client.post("/api/rules/", json=rule_payload)
    assert resp.status_code == 200
    assert resp.json()["rule_id"] == "R001"

    # Get rules
    resp = client.get("/api/rules/")
    assert resp.status_code == 200
    rules = resp.json()
    assert len(rules) == 1
    assert rules[0]["name"].startswith("Saturn")

    # Update rule
    update_payload = {
        "name": "Saturn in Capricorn (Updated)",
        "conditions": [{"planet": "saturn", "relation": "retrograde"}],
        "outcomes": [{"effect": "Bearish", "weight": 0.5, "sector_id": 1}]
    }
    resp = client.put("/api/rules/R001", json=update_payload)
    assert resp.status_code == 200
    assert "Updated" in resp.json()["rule_id"] or "Updated" in resp.json().get("name", "")

    # Delete rule
    resp = client.delete("/api/rules/R001")
    assert resp.status_code == 200
    assert resp.json()["deleted"] == "R001"

    # Verify cascade
    resp = client.get("/api/rules/")
    assert resp.json() == []
