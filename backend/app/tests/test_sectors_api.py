# app/tests/test_sectors_api.py

# @pytest.fixture(scope="module")
# def test_app():
#     """Create a FastAPI app with an in-memory DB."""
#     app = FastAPI()
#     app.include_router(sectors_router)

#     # In-memory SQLite setup
#     engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
#     TestingSessionLocal = sessionmaker(bind=engine)
#     Base.metadata.create_all(engine)

#     # Dependency override
#     def override_get_db():
#         db = TestingSessionLocal()
#         try:
#             yield db
#         finally:
#             db.close()

#     for route in app.router.routes:
#         if hasattr(route.endpoint, "__dependencies__"):
#             route.endpoint.__dependencies__["get_db"] = override_get_db

#     client = TestClient(app)
#     return client


def test_create_and_get_sector(test_app):
    """POST + GET sector CRUD test."""
    client = test_app

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
