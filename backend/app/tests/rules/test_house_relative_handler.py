import pytest
from datetime import datetime
from app.core.rules.relations.house_relative_handler import HouseRelativeHandler
from app.core.common.schemas import ConditionRead
from app.core.astro.providers.stub_provider import StubProvider
from app.core.db.enums import Relation  


def make_cond(planet, relation, target, orb=None, value=None):
    relation_enum = Relation[relation]
    return ConditionRead(
        planet=planet,
        relation=relation_enum,
        target=target,
        orb=orb,
        value=value,
        id=1,
        rule_id=1,
    )

@pytest.fixture
def provider():
    return StubProvider()


def test_same_house(provider):
    provider.set_longitude_map({"sun": 10.0, "moon": 20.0})
    cond = make_cond("moon", "in_house_relative_to", "sun", value="1")
    h = HouseRelativeHandler()
    assert h.check(provider, cond, datetime(2025, 1, 1), orb_default=2.0)


def test_7th_house(provider):
    provider.set_longitude_map({"sun": 0.0, "moon": 180.0})
    cond = make_cond("moon", "in_house_relative_to", "sun", value="7")
    h = HouseRelativeHandler()
    assert h.check(provider, cond, datetime(2025, 1, 1), orb_default=2.0)


def test_4th_house(provider):
    provider.set_longitude_map({"sun": 0.0, "mars": 90.0})
    cond = make_cond("mars", "in_house_relative_to", "sun", value="4")
    h = HouseRelativeHandler()
    assert h.check(provider, cond, datetime(2025, 1, 1), orb_default=2.0)


def test_wrap_around(provider):
    provider.set_longitude_map({"sun": 350.0, "venus": 20.0})
    cond = make_cond("venus", "in_house_relative_to", "sun", value="2")
    h = HouseRelativeHandler()
    assert h.check(provider, cond, datetime(2025, 1, 1), orb_default=2.0)


def test_not_in_house(provider):
    provider.set_longitude_map({"sun": 0.0, "moon": 200.0})
    cond = make_cond("moon", "in_house_relative_to", "sun", value="4")
    h = HouseRelativeHandler()
    assert not h.check(provider, cond, datetime(2025, 1, 1), orb_default=2.0)
