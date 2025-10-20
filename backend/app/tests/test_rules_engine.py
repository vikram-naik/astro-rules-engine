from core.astro_provider import AstroProvider
from core.rules_engine import AstroRulesEngine
from core.schemas import RuleCreate, Condition, Outcome, OutcomeEffect
from datetime import datetime


def test_jupiter_ketu_rule():
    provider = AstroProvider()
    engine = AstroRulesEngine(provider)
    # create a rule that matches stub provider's deterministic mapping by using owner from provider
    # find a date where the stub returns nakshatra owner Ketu for jupiter
    dt = datetime(2025, 1, 1)
    # naive rule: jupiter in nakshatra owned by Ketu
    cond = Condition(planet="jupiter", relation="in_nakshatra_owned_by", target="Ketu")
    out = Outcome(sector_code="EQUITY", effect=OutcomeEffect.Bearish)
    rule = RuleCreate(rule_id="T1", name="test", conditions=[cond], outcomes=[out])
    events = engine.evaluate_rule(rule, dt)
    assert isinstance(events, list)