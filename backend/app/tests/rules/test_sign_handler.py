import pytest
from datetime import datetime
from app.core.rules.relations.sign_handler import SignHandler
from app.core.astro.providers.stub_provider import StubProvider
from app.core.common.schemas import ConditionRead
from app.core.db.enums import Planet, Relation


def make_cond(planet: str, target: str):
    planet_enum = Planet[planet]
    return ConditionRead(
        id=1,
        rule_id=1,
        planet=planet_enum,
        relation=Relation.in_sign,
        target=target,
        orb=None,
        value=None,
    )


@pytest.fixture
def when():
    return datetime(2025, 1, 1)


def test_sign_handler_numeric_index(when):
    sp = StubProvider()
    sp.set_longitude_map({"sun": 10.0})
    cond = make_cond("sun", "0")
    assert SignHandler().check(sp, cond, when, orb_default=2.0) is True


def test_sign_handler_name_aries(when):
    sp = StubProvider()
    sp.set_longitude_map({"sun": 10.0})
    cond = make_cond("sun", "Aries")
    assert SignHandler().check(sp, cond, when, orb_default=2.0) is True


def test_sign_handler_boundary_false(when):
    sp = StubProvider()
    sp.set_longitude_map({"sun": 30.1})
    cond = make_cond("sun", "Aries")
    assert SignHandler().check(sp, cond, when, orb_default=2.0) is False


def test_sign_handler_invalid_name(when):
    sp = StubProvider()
    sp.set_longitude_map({"sun": 10.0})
    cond = make_cond("sun", "NotASign")
    assert SignHandler().check(sp, cond, when, orb_default=2.0) is False


def test_sign_handler_numeric_out_of_range(when):
    sp = StubProvider()
    sp.set_longitude_map({"sun": 10.0})
    cond = make_cond("sun", "99")  # invalid index
    assert SignHandler().check(sp, cond, when, orb_default=2.0) is False


def test_sign_handler_empty_target(when):
    sp = StubProvider()
    sp.set_longitude_map({"sun": 10.0})
    cond = make_cond("sun", "")
    assert SignHandler().check(sp, cond, when, orb_default=2.0) is False


def test_sign_handler_provider_exception(when):
    class BrokenProvider(StubProvider):
        def longitude(self, planet, when):
            raise RuntimeError("boom")

    bp = BrokenProvider()
    cond = make_cond("sun", "Aries")
    assert SignHandler().check(bp, cond, when, orb_default=2.0) is False


def test_sign_handler_boundary_rounding(when):
    sp = StubProvider()
    sp.set_longitude_map({"sun": 359.9})  # Pisces (index 11)
    cond = make_cond("sun", "Pisces")
    assert SignHandler().check(sp, cond, when, orb_default=2.0) is True
