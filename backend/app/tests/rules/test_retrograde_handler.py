# app/tests/test_retrograde_handler.py
from datetime import datetime
import pytest
from app.core.rules.relations.retrograde_handler import RetrogradeHandler
from app.core.astro.providers.stub_provider import StubProvider
from app.core.common.schemas import ConditionRead
from app.core.db.enums import Relation, Planet

def test_retrograde_true():
    sp = StubProvider()
    sp.set_retro_map({"mars": True})
    cond = ConditionRead(id=1, rule_id=1, planet=Planet.mars, relation=Relation.retrograde, target=None, orb=None, value=None)
    h = RetrogradeHandler()
    assert h.check(sp, cond, datetime(2025,1,1), orb_default=2.0) is True

def test_retrograde_false():
    sp = StubProvider()
    sp.set_retro_map({"mars": False})
    cond = ConditionRead(id=1, rule_id=1, planet=Planet.mars, relation=Relation.retrograde, target=None, orb=None, value=None)
    h = RetrogradeHandler()
    assert h.check(sp, cond, datetime(2025,1,1), orb_default=2.0) is False
