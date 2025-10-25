# app/core/rules/relations/i_relation.py
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Protocol
from app.core.common.schemas import ConditionRead
from app.core.astro.interfaces.i_astro_provider import IAstroProvider

class IRelationHandler(ABC):
    """
    Relation handler interface.
    Handlers encapsulate logic for a single Relation type and return True/False.
    """

    @abstractmethod
    def check(self, provider: IAstroProvider, cond: ConditionRead, when: datetime, orb_default: float) -> bool:
        """
        Evaluate the condition using the given provider and datetime.

        Args:
            provider: IAstroProvider instance to query positions.
            cond: ConditionRead object (from rules schema).
            when: datetime of evaluation.
            orb_default: default orb degrees if cond.orb is None.
        Returns:
            True if relation satisfied, False otherwise.
        """
        raise NotImplementedError
