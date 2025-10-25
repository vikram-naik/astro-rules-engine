# app/tests/test_combust_handler.py
from datetime import datetime
import pytest
from app.core.rules.relations.combust_handler import CombustHandler
from app.core.astro.providers.stub_provider import StubProvider
from app.core.common.schemas import ConditionRead
from app.core.db.enums import Relation, Planet

def test_combust_by_sun_true_default_orb():
    sp = StubProvider()
    # planet 100°, sun 105° -> angular distance 5° -> combust if default orb >=5
    sp.set_longitude_map({"mars": 100.0, "sun": 105.0})
    cond = ConditionRead(id=1, rule_id=1, planet="mars", relation=Relation.combust_by_sun, target=None, orb=None, value=None)
    h = CombustHandler()
    assert h.check(sp, cond, datetime(2025,1,1), orb_default=8.0) is True

def test_combust_by_sun_false_small_orb():
    sp = StubProvider()
    sp.set_longitude_map({"mars": 100.0, "sun": 110.0})
    cond = ConditionRead(id=1, rule_id=1, planet="mars", relation=Relation.combust_by_sun, target=None, orb=3.0, value=None)
    h = CombustHandler()
    assert h.check(sp, cond, datetime(2025,1,1), orb_default=8.0) is False

def test_combust_with_settings_override(monkeypatch):
    sp = StubProvider()
    sp.set_longitude_map({"venus": 100.0, "sun": 106.0})
    # simulate settings ASTRO combust map where venus has 7
    from app.core.common import config
    monkeypatch.setattr(config.settings, "astro_combust_orbs", {"venus": 7.0})
    cond = ConditionRead(id=1, rule_id=1, planet="venus", relation=Relation.combust_by_sun, target=None, orb=None, value=None)
    h = CombustHandler()
    assert h.check(sp, cond, datetime(2025,1,1), orb_default=4.0) is True
