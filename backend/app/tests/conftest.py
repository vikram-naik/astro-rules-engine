"""
Pytest configuration for test database and FastAPI app.
Creates a temporary file-based SQLite database shared across all tests,
ensures all tables are created, and cleans up data after each test.

Two cleanup strategies are supported:
1. Transactional rollback (fast, fully isolated, default)
2. Row deletion (safe if rollback isolation is not desired)

Switch with the USE_TRANSACTIONAL_FIXTURE flag below.
"""

import os
import tempfile
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.core.db import Base, get_db


# ------------------------------------------------------------------------------
# ⚙️  CONFIG
# ------------------------------------------------------------------------------
USE_TRANSACTIONAL_FIXTURE = True  # set to False to use DELETE-based cleanup


# ------------------------------------------------------------------------------
# 🧱  TEMP DATABASE SETUP
# ------------------------------------------------------------------------------
@pytest.fixture(scope="session")
def temp_db_path():
    """Create a temporary SQLite file DB for all tests."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


@pytest.fixture(scope="session")
def test_engine(temp_db_path):
    """Session-scoped SQLAlchemy engine bound to a temp file DB."""
    engine = create_engine(
        f"sqlite:///{temp_db_path}",
        connect_args={"check_same_thread": False},
    )

    # Ensure all models are registered before schema creation
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


# ------------------------------------------------------------------------------
# 🧪  TRANSACTIONAL OR DELETE-BASED SESSION FIXTURE
# ------------------------------------------------------------------------------
@pytest.fixture(scope="function")
def db_session(test_engine):
    """
    Provide a clean SQLAlchemy session for each test.

    If USE_TRANSACTIONAL_FIXTURE=True, each test runs inside a transaction
    that is rolled back automatically.
    Otherwise, rows are deleted from all tables after each test.
    """
    SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = SessionTesting()

    if USE_TRANSACTIONAL_FIXTURE:
        # Start a SAVEPOINT transaction so each test rolls back cleanly
        connection = test_engine.connect()
        trans = connection.begin()
        session.bind = connection

        try:
            yield session
        finally:
            # Roll back the transaction (undo all test changes)
            session.close()
            trans.rollback()
            connection.close()

    else:
        # DELETE-based cleanup (safe if background threads use the same DB)
        try:
            yield session
        finally:
            for table in reversed(Base.metadata.sorted_tables):
                session.execute(text(f"DELETE FROM {table.name}"))
            session.commit()
            session.close()


# ------------------------------------------------------------------------------
# 🌐  FASTAPI TEST CLIENT FIXTURE
# ------------------------------------------------------------------------------
@pytest.fixture(scope="function")
def client(db_session):
    """
    Provide a FastAPI TestClient bound to the temporary test DB.
    Each test automatically gets a clean DB session.
    """

    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# ------------------------------------------------------------------------------
# 🧾  DEBUG TEST (optional)
# ------------------------------------------------------------------------------
# Uncomment to verify isolation works:
#
# def test_db_cleanup_check(db_session):
#     from sqlalchemy import text
#     db_session.execute(text("INSERT INTO rule (name, expression) VALUES ('a', 'b')"))
#     db_session.commit()
#     count = db_session.execute(text("SELECT COUNT(*) FROM rule")).scalar()
#     assert count == 1
#
# def test_db_is_clean_after_previous(db_session):
#     from sqlalchemy import text
#     count = db_session.execute(text("SELECT COUNT(*) FROM rule")).scalar()
#     assert count == 0
