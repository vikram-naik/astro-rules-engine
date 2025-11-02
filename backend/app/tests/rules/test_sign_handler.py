import pytest
from datetime import datetime
from app.core.rules.relations.sign_handler import SignHandler
from app.core.astro.providers.stub_provider import StubProvider
from app.tests.rules import make_cond as shared_make_cond
from app.core.db.enums import Relation

# -------------------------------------------------------------------------
# Helper utilities
# -------------------------------------------------------------------------

def make_cond(planet: str, target: str, value=None, orb=None):
    """Helper to build a valid Condition object."""
    return shared_make_cond(planet, Relation.in_sign, target, value, orb)


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
