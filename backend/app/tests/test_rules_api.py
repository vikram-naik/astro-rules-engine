# app/tests/test_rules_api.py




def test_rule_crud_flow(client):

    # Create reference sector
    sector_payload = {"code": "COMMODITY", "name": "Commodity Market", "description": "Raw materials"}
    resp = client.post("/api/sectors/", json=sector_payload)
    assert resp.status_code == 200, resp.text

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
    assert resp.status_code == 200, resp.text
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
