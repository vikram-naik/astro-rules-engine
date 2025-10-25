# app/tests/test_sign_handler.py
from datetime import datetime
import pytest
from app.core.rules.relations.sign_handler import SignHandler
from app.core.astro.providers.stub_provider import StubProvider
from app.core.common.schemas import ConditionRead
from app.core.db.enums import Planet, Relation

def make_cond(planet: str, target: str):
    planet_enum = Planet[planet]
    return ConditionRead(id=1, rule_id=1, planet=planet_enum, relation=Relation.in_sign, target=target, orb=None, value=None)

def test_sign_handler_numeric_index():
    sp = StubProvider()
    # stub longitude for planet -> 10° => Aries (index 0)
    sp.set_longitude_map({"sun": 10.0})
    cond = make_cond("sun", "0")
    h = SignHandler()
    assert h.check(sp, cond, datetime(2025,1,1), orb_default=2.0) is True

def test_sign_handler_name_aries():
    sp = StubProvider()
    sp.set_longitude_map({"sun": 10.0})
    cond = make_cond("sun", "Aries")  # user-friendly name
    h = SignHandler()
    assert h.check(sp, cond, datetime(2025,1,1), orb_default=2.0) is True

def test_sign_handler_boundary_false():
    sp = StubProvider()
    # 29.9° -> Aries (index 0). 30.1 -> Taurus (index 1)
    sp.set_longitude_map({"sun": 30.1})
    cond = make_cond("sun", "Aries")
    h = SignHandler()
    assert h.check(sp, cond, datetime(2025,1,1), orb_default=2.0) is False
