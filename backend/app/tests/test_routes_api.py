# backend/app/tests/test_routes_api.py
"""
Integration tests for FastAPI routes
------------------------------------
Covers /rules, /evaluate, and /correlation endpoints.
"""

from fastapi.testclient import TestClient
from app.main import app
from app.core.common.db import get_session
from app.core.common.models import RuleModel
import json
import pytest
from datetime import datetime
from sqlalchemy import text

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_rules_table():
    """Clean up rules before and after each test."""
    with get_session() as session:
        session.exec(text("DELETE FROM rulemodel;"))
        session.commit()
    yield
    with get_session() as session:
        session.exec(text("DELETE FROM rulemodel;"))
        session.commit()


def test_rules_crud_cycle():
    """Test basic CRUD operations for /rules endpoints."""

    # --- Create rule ---
    rule_payload = {
        "name": "Jupiter in Ketu Nakshatra",
        "description": "Test rule for correlation",
        "confidence": 0.9,
        "enabled": True,
        "conditions": [
            {"planet": "jupiter", "relation": "in_nakshatra_owned_by", "target": "ketu"}
        ],
        "outcomes": [
            {"sector_code": "EQUITY", "effect": "Bullish", "weight": 1.0}
        ],
    }
    response = client.post("/rules/", json=rule_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Jupiter in Ketu Nakshatra"

    rule_id = data["rule_id"]

    # --- Get rule ---
    response = client.get(f"/rules/{rule_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["rule_id"] == rule_id

    # --- Update rule ---
    update_payload = {"confidence": 0.8}
    response = client.put(f"/rules/{rule_id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["confidence"] == 0.8

    # --- Delete rule ---
    response = client.delete(f"/rules/{rule_id}")
    assert response.status_code == 200
    msg = response.json()
    assert "deleted" in msg["message"].lower()

def test_evaluate_and_correlation(monkeypatch):
    """Test /evaluate and /correlation endpoints with mocked services."""

    def mock_evaluate_rules_for_range(start_date, end_date):
        return [
            {
                "rule_id": "R001",
                "name": "Mock Rule",
                "date": "2025-01-01",
                "sector": "EQUITY",
                "effect": "Bullish",
                "weight": 1.0,
                "confidence": 1.0,
            }
        ]

    def mock_analyze_correlation(events, ticker, lookahead_days, market_provider_type=None):
        return {
            "ticker": ticker,
            "lookahead_days": lookahead_days,
            "per_rule": {"R001": {"name": "Mock Rule", "stats": {1: {"hit_rate": 1.0}}}},
            "aggregate": {1: {"hit_rate": 1.0}},
        }

    # ✅ Patch where the route uses these functions
    monkeypatch.setattr("app.api.routes_eval.evaluate_rules_for_range", mock_evaluate_rules_for_range)
    monkeypatch.setattr("app.api.routes_correlation.analyze_correlation", mock_analyze_correlation)

    # --- Evaluate endpoint ---
    eval_payload = {"start_date": "2025-01-01", "end_date": "2025-01-02"}
    response = client.post("/evaluate/", json=eval_payload)
    assert response.status_code == 200
    data = response.json()
    assert "events" in data
    assert data["count"] == 1

    # --- Correlation endpoint ---
    corr_payload = {
        "start_date": "2025-01-01",
        "end_date": "2025-01-05",
        "ticker": "^TEST",
        "lookahead_days": [1, 3],
    }
    response = client.post("/correlation/run", json=corr_payload)
    assert response.status_code == 200
    result = response.json()
    assert result["ticker"] == "^TEST"
    assert "aggregate" in result
    assert "per_rule" in result
