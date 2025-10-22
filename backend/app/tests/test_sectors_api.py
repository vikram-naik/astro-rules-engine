


def test_create_and_get_sector(client):
    """POST + GET sector CRUD test."""

    # Create
    payload = {"code": "EQUITY", "name": "Equity Market", "description": "Stocks and shares"}
    resp = client.post("/api/sectors/", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["code"] == "EQUITY"

    # Fetch list
    resp = client.get("/api/sectors/")
    assert resp.status_code == 200, resp.text
    sectors = resp.json()
    assert any(s["code"] == "EQUITY" for s in sectors)

    # Get 
    print(data)
    resp = client.get(f"/api/sectors/{data['code']}")
    assert resp.status_code == 200, resp.text
    sector = resp.json()
    assert sector["code"] == "EQUITY"

    # Update
    update = {"name": "Equities Market", "description": "Updated description"}
    resp = client.put(f"/api/sectors/{data['id']}", json=update)
    assert resp.status_code == 200, resp.text
    assert "Updated" in resp.json()["description"]

    # Delete
    resp = client.delete("/api/sectors/EQUITY")
    assert resp.status_code == 200, resp.text
    assert resp.json()["deleted"] == "EQUITY"

    # Verify deletion
    resp = client.get("/api/sectors/")
    assert all(s["code"] != "EQUITY" for s in resp.json())
