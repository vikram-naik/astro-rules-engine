import pytest
from app.core.rules.relations.registry import (
    register_relation,
    get_relation_handler,
    registered_relations,
)
from app.core.rules.relations.i_relation import IRelationHandler
from app.core.db.enums import Relation


# --- Dummy handlers for testing ---
class DummyHandler(IRelationHandler):
    def check(self, *args, **kwargs):
        return True


class NewHandler(DummyHandler):
    def check(self, *args, **kwargs):
        return "new"


@pytest.fixture(autouse=True)
def isolated_registry(monkeypatch):
    """Provide a clean, isolated registry for each test."""
    empty_registry = {}
    monkeypatch.setattr("app.core.rules.relations.registry._registry", empty_registry)
    yield


# --- Tests ---

def test_register_and_get_handler():
    """Ensure registered handler can be retrieved and instantiated."""
    register_relation(Relation.in_sign, DummyHandler)
    handler = get_relation_handler(Relation.in_sign)
    assert isinstance(handler, DummyHandler)


def test_get_handler_unregistered_returns_none():
    """When a relation isn't registered, None should be returned."""
    # Start with an empty registry due to fixture
    result = get_relation_handler(Relation.aspect_with)
    assert result is None


def test_registered_relations_returns_copy():
    """Returned dict should be a copy, not the internal registry."""
    register_relation(Relation.in_axis, DummyHandler)
    reg1 = registered_relations()
    reg2 = registered_relations()
    assert reg1 == reg2
    assert reg1 is not reg2  # ensure copy, not reference


def test_register_overwrites_existing():
    """Re-registering the same relation replaces previous handler."""
    register_relation(Relation.in_sign, DummyHandler)
    first = get_relation_handler(Relation.in_sign)
    register_relation(Relation.in_sign, NewHandler)
    second = get_relation_handler(Relation.in_sign)
    # Validate that type changed, not just subclass
    assert type(first) is DummyHandler
    assert type(second) is NewHandler
