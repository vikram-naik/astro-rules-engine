"""
Relation Handler Registry
-------------------------
Purpose:
    Provides a global registry mapping each Relation enum to its corresponding
    IRelationHandler implementation class.

Functional Overview:
    - register_relation(rel, handler_cls):
        Registers a handler for a specific Relation type.

    - get_relation_handler(rel):
        Returns an instantiated handler if registered, otherwise None.

    - registered_relations():
        Returns a shallow copy of the internal registry dictionary.

Usage:
    from app.core.db.enums import Relation
    from app.core.rules.relations.sign_handler import SignHandler
    from app.core.rules.relations.registry import register_relation, get_relation_handler

    register_relation(Relation.in_sign, SignHandler)
    handler = get_relation_handler(Relation.in_sign)
    assert isinstance(handler, SignHandler)
"""

from typing import Dict, Type, Optional
from app.core.db.enums import Relation
from .i_relation import IRelationHandler

_registry: Dict[Relation, Type[IRelationHandler]] = {}


def register_relation(rel: Relation, handler_cls: Type[IRelationHandler]) -> None:
    """Register a handler class for a Relation enum."""
    _registry[rel] = handler_cls


def get_relation_handler(rel: Relation) -> Optional[IRelationHandler]:
    """Return an instance of the handler for the given relation, or None if not registered."""
    cls = _registry.get(rel)
    return cls() if cls else None


def registered_relations() -> Dict[Relation, Type[IRelationHandler]]:
    """Return a shallow copy of the current relation-to-handler mapping."""
    return dict(_registry)
