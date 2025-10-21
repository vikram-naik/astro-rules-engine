# app/tests/test_rules_crud.py
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.core.common.models import Base, Sector, Rule, Condition, Outcome


@pytest.fixture(scope="module")
def test_db():
    """Create an in-memory SQLite DB for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False, future=True)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(test_db):
    with Session(test_db) as s:
        yield s


def test_rule_condition_outcome_crud(session):
    # 1️⃣ Create sector (reference)
    sector = Sector(code="EQUITY", name="Equity Market", description="Stock market sector")
    session.add(sector)
    session.commit()
    session.refresh(sector)
    assert sector.id is not None

    # 2️⃣ Create rule
    rule = Rule(rule_id="R001", name="Jupiter in Ketu Nakshatra", description="Market weakens")
    cond = Condition(planet="jupiter", relation="in_nakshatra", target="ketu", orb=10.0)
    out = Outcome(effect="Bearish", weight=1.0, sector=sector)

    rule.conditions.append(cond)
    rule.outcomes.append(out)

    session.add(rule)
    session.commit()
    session.refresh(rule)

    # 3️⃣ Validate persistence
    assert rule.id is not None
    assert rule.conditions[0].planet == "jupiter"
    assert rule.outcomes[0].sector.name == "Equity Market"

    # 4️⃣ Query rule and linked outcome
    db_rule = session.scalar(select(Rule).where(Rule.rule_id == "R001"))
    assert db_rule.name == "Jupiter in Ketu Nakshatra"
    assert db_rule.outcomes[0].effect == "Bearish"
    assert db_rule.outcomes[0].sector.code == "EQUITY"

    # 5️⃣ Update
    db_rule.name = "Jupiter in Ketu Nakshatra (Updated)"
    session.commit()
    session.refresh(db_rule)
    assert "(Updated)" in db_rule.name

    # 6️⃣ Delete rule → cascades to conditions & outcomes, but sector remains
    session.delete(db_rule)
    session.commit()

    assert session.scalars(select(Condition)).all() == []
    assert session.scalars(select(Outcome)).all() == []
    sectors_remaining = session.scalars(select(Sector)).all()
    assert len(sectors_remaining) == 1  # sector should persist
