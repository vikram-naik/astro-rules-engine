import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.common.models import Base
from app.core.common.db import get_db


@pytest.fixture(scope="function")
def test_app():
    # ✅ Shared in-memory DB URI
    engine = create_engine(
        "sqlite:///file::memory:?cache=shared",
        connect_args={"check_same_thread": False, "uri": True},
    )

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # Override FastAPI dependency
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    Base.metadata.drop_all(bind=engine)
