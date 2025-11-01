# app/core/rules/relations/i_relation.py
from abc import ABC, abstractmethod
from datetime import datetime
from app.core.astro.interfaces.i_astro_provider import IAstroProvider
from app.core.db.models import Condition


class IRelationHandler(ABC):
    """
    Base interface for all astrological relation handlers.
    Each handler encapsulates logic for one relation type.
    """

    @abstractmethod
    def check(
        self,
        provider: IAstroProvider,
        cond: Condition,
        when: datetime,
        orb_default: float,
    ) -> bool:
        """
        Evaluate the condition using the given provider and datetime.

        Args:
            provider: IAstroProvider instance to query planetary data.
            cond: Condition ORM instance.
            when: datetime of evaluation.
            orb_default: default orb (deg) if cond.orb is None.

        Returns:
            True if relation satisfied, else False.
        """
        raise NotImplementedError
