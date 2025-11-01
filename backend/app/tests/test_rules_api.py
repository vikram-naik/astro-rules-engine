# app/tests/test_rules_api.py


def test_rule_crud_flow(client):
    # 1️⃣ Create reference sector
    sector_payload = {
        "code": "COMMODITY",
        "name": "Commodity Market",
        "description": "Raw materials",
    }
    resp = client.post("/api/sectors/", json=sector_payload)
    assert resp.status_code == 200, resp.text

    # 2️⃣ Create rule with grouped conditions + outcomes
    rule_payload = {
        "name": "Saturn in Capricorn",
        "description": "Commodities steady under Saturn in Capricorn",
        "confidence": 0.8,
        "enabled": True,
        "condition_groups": [
            {
                "operator": "AND",
                "conditions": [
                    {"planet": "saturn", "relation": "in_sign", "target": "capricorn"}
                ],
            }
        ],
        "outcomes": [
            {"effect": "Bullish", "weight": 1.0, "sector_id": 1}
        ],
    }

    resp = client.post("/api/rules/", json=rule_payload)
    assert resp.status_code == 200, resp.text
    rule_id = resp.json()["id"]
    assert isinstance(rule_id, int)

    # 3️⃣ Get all rules
    resp = client.get("/api/rules/")
    assert resp.status_code == 200
    rules = resp.json()
    assert len(rules) == 1
    assert rules[0]["name"].startswith("Saturn")
    assert "condition_groups" in rules[0]
    assert len(rules[0]["condition_groups"]) == 1

    # 4️⃣ Update rule (change name, condition, and outcome)
    update_payload = {
        "name": "Saturn in Capricorn (Updated)",
        "condition_groups": [
            {
                "operator": "AND",
                "conditions": [
                    {"planet": "saturn", "relation": "is_retrograde"}
                ],
            }
        ],
        "outcomes": [
            {"effect": "Bearish", "weight": 0.5, "sector_id": 1}
        ],
    }

    resp = client.put(f"/api/rules/{rule_id}", json=update_payload)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "Updated" in body["name"]
    assert body["outcomes"][0]["effect"] == "Bearish"
    assert body["condition_groups"][0]["conditions"][0]["relation"] == "is_retrograde"

    # 5️⃣ Delete rule
    resp = client.delete(f"/api/rules/{rule_id}")
    assert resp.status_code == 200
    assert resp.json()["deleted"] == rule_id

    # 6️⃣ Verify cascade → rule should no longer exist
    resp = client.get("/api/rules/")
    assert resp.status_code == 200
    assert resp.json() == []

def test_create_rule_with_nested_or_and_groups(client):
    """Tests deep nesting of condition groups like (A AND (B OR (C AND D)))."""

    # Create a reference sector first
    sector_payload = {"code": "TECH", "name": "Technology", "description": "Tech stocks"}
    resp = client.post("/api/sectors/", json=sector_payload)
    assert resp.status_code == 200, resp.text

    # Deeply nested group definition: A AND (B OR (C AND D))
    payload = {
        "name": "Nested AND-OR Test",
        "description": "Complex logical structure test",
        "confidence": 1.0,
        "enabled": True,
        "condition_groups": [
            {
                "operator": "AND",
                "conditions": [
                    {"planet": "sun", "relation": "in_sign", "target": "aries"}  # A
                ],
                "subgroups": [
                    {
                        "operator": "OR",
                        "conditions": [
                            {"planet": "moon", "relation": "in_sign", "target": "leo"}  # B
                        ],
                        "subgroups": [
                            {
                                "operator": "AND",
                                "conditions": [
                                    {"planet": "mars", "relation": "in_sign", "target": "capricorn"},  # C
                                    {"planet": "venus", "relation": "in_sign", "target": "taurus"},    # D
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
        "outcomes": [
            {"effect": "Bullish", "weight": 1.5, "sector_id": 1}
        ],
    }

    # Create rule
    resp = client.post("/api/rules/", json=payload)
    assert resp.status_code == 200, resp.text
    rule_id = resp.json()["id"]

    # Fetch rule and verify nested structure
    resp = client.get(f"/api/rules/{rule_id}")
    assert resp.status_code == 200
    data = resp.json()

    # Verify top-level AND
    assert data["condition_groups"][0]["operator"] == "AND"
    assert len(data["condition_groups"][0]["conditions"]) == 1

    # Verify nested OR
    nested_or = data["condition_groups"][0]["subgroups"][0]
    assert nested_or["operator"] == "OR"
    assert len(nested_or["conditions"]) == 1

    # Verify deepest AND group
    deep_and = nested_or["subgroups"][0]
    assert deep_and["operator"] == "AND"
    assert len(deep_and["conditions"]) == 2


def test_multiple_top_level_groups(client):
    """Test a rule with multiple top-level condition groups."""

    sector_payload = {"code": "ENERGY", "name": "Energy", "description": "Oil & Gas"}
    client.post("/api/sectors/", json=sector_payload)

    payload = {
        "name": "Multi-root Group Rule",
        "description": "Should support multiple top-level condition groups",
        "enabled": True,
        "condition_groups": [
            {
                "operator": "AND",
                "conditions": [
                    {"planet": "saturn", "relation": "in_sign", "target": "aquarius"}
                ],
            },
            {
                "operator": "OR",
                "conditions": [
                    {"planet": "jupiter", "relation": "in_sign", "target": "pisces"}
                ],
            },
        ],
        "outcomes": [{"effect": "Neutral", "weight": 0.7, "sector_id": 1}],
    }

    resp = client.post("/api/rules/", json=payload)
    assert resp.status_code == 200
    rule_id = resp.json()["id"]

    resp = client.get(f"/api/rules/{rule_id}")
    assert resp.status_code == 200
    data = resp.json()

    assert len(data["condition_groups"]) == 2
    assert {g["operator"] for g in data["condition_groups"]} == {"AND", "OR"}


def test_serialization_order_and_operators(client):
    """Validate that order and operator fields are preserved and serialized correctly."""

    sector_payload = {"code": "AUTO", "name": "Automobile", "description": "Auto stocks"}
    client.post("/api/sectors/", json=sector_payload)

    payload = {
        "name": "Operator Order Rule",
        "description": "Ensures order and operator serialization is stable",
        "condition_groups": [
            {"operator": "AND", "order": 2, "conditions": []},
            {"operator": "OR", "order": 1, "conditions": []},
        ],
        "outcomes": [{"effect": "Bullish", "weight": 1.0, "sector_id": 1}],
    }

    resp = client.post("/api/rules/", json=payload)
    assert resp.status_code == 200
    rule_id = resp.json()["id"]

    resp = client.get(f"/api/rules/{rule_id}")
    assert resp.status_code == 200
    data = resp.json()

    orders = [g["order"] for g in data["condition_groups"]]
    operators = [g["operator"] for g in data["condition_groups"]]

    assert set(operators) == {"AND", "OR"}
    assert all(isinstance(o, int) for o in orders)
