# app/core/rules/relations/registry.py
from typing import Dict, Type, Optional
from app.core.db.enums import Relation
from .i_relation import IRelationHandler

_registry: Dict[Relation, Type[IRelationHandler]] = {}

def register_relation(rel: Relation, handler_cls: Type[IRelationHandler]) -> None:
    """
    Register a handler class for a Relation enum.
    Handler class must implement IRelationHandler and be instantiable with no args.
    """
    _registry[rel] = handler_cls

def get_relation_handler(rel: Relation) -> Optional[IRelationHandler]:
    """
    Return an instance of the handler for the given relation, or None if not registered.
    """
    cls = _registry.get(rel)
    return cls() if cls else None

def registered_relations() -> Dict[Relation, Type[IRelationHandler]]:
    return dict(_registry)
