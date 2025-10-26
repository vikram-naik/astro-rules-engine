from app.core.db.enums import Relation
import pytest
from datetime import datetime
from app.core.rules.relations.retrograde_handler import RetrogradeHandler
from app.core.common.schemas import ConditionRead
from app.core.astro.providers.stub_provider import StubProvider


@pytest.fixture
def handler():
    return RetrogradeHandler()


@pytest.fixture
def provider():
    sp = StubProvider()
    sp.set_retro_map({
        "mars": True,
        "venus": False
    })
    return sp


@pytest.fixture
def when():
    return datetime(2025, 1, 1)


def make_cond(planet):
    return ConditionRead(
        id=1,
        rule_id=1,
        planet=planet,
        relation=Relation.is_retrograde,
        target=None,
        orb=None,
        value=None
    )


def test_retrograde_true(handler, provider, when):
    cond = make_cond("mars")
    assert handler.check(provider, cond, when, orb_default=2.0) is True


def test_retrograde_false(handler, provider, when):
    cond = make_cond("venus")
    assert handler.check(provider, cond, when, orb_default=2.0) is False


def test_case_insensitive(handler, provider, when):
    cond = make_cond("MARS")
    assert handler.check(provider, cond, when, orb_default=2.0) is True


def test_missing_method(handler, provider, when):
    """Simulate AttributeError when provider lacks `is_retrograde`."""
    class DummyProvider:
        pass

    dummy = DummyProvider()
    cond = make_cond("mars")
    assert handler.check(dummy, cond, when, orb_default=2.0) is False


def test_non_callable_attribute(handler, provider, when):
    """Simulate TypeError by assigning non-callable to is_retrograde."""
    provider.is_retrograde = None
    cond = make_cond("mars")
    assert handler.check(provider, cond, when, orb_default=2.0) is False


def test_provider_exception(handler, provider, when):
    """Simulate arbitrary runtime failure."""
    def boom(*args, **kwargs):
        raise RuntimeError("crash")
    provider.is_retrograde = boom
    cond = make_cond("mars")
    assert handler.check(provider, cond, when, orb_default=2.0) is False
