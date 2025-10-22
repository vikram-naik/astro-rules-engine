# app/tests/test_rule_events_api.py
import pytest
from datetime import date
from app.core.db.models import Rule, Condition, Outcome, Sector
from app.core.db.enums import Planet, Relation, OutcomeEffect

def test_generate_and_list_events(client, db_session):
    db = db_session

    # create sector (if required by Outcome)
    sector = Sector(code="S-T1", name="Sector Test", description="sector")
    db.add(sector)
    db.commit()
    db.refresh(sector)

    # create a rule with condition/outcome
    rule = Rule(
        rule_id="R-API-1",
        name="api-generator-rule",
        description="API test rule",
        enabled=True,
    )
    cond = Condition(
        planet=Planet.moon.name,
        relation=Relation.in_sign.name,
        target="Taurus",
        orb=1.0,
        value=None,
    )
    outc = Outcome(
        sector_id=sector.id,
        effect=OutcomeEffect.Neutral.value if hasattr(OutcomeEffect, "Neutral") else OutcomeEffect.Bullish.value,
        weight=1.0,
    )

    rule.conditions = [cond]
    rule.outcomes = [outc]
    db.add(rule)
    db.commit()
    db.refresh(rule)

    # call the API to generate events (route base: /api/rules/{rule_id}/generate_events)
    url = f"/api/rules/{rule.rule_id}/generate_events"
    params = {
        "start_date": date(2025, 1, 1),
        "end_date": date(2025, 1, 5),
        "provider": "stub",
        "overwrite": "true",
    }
    resp = client.post(url, params=params)
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)

    # now fetch persisted events
    list_url = f"/api/rules/{rule.rule_id}/events"
    resp2 = client.get(list_url)
    assert resp2.status_code == 200
    data = resp2.json()
    assert isinstance(data, list)
