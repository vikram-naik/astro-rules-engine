# app/core/rules/interfaces/i_rules_engine.py
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any
from app.core.db.models import Rule


class IRulesEngine(ABC):
    """Abstract interface for rules engine implementations."""

    @abstractmethod
    def evaluate_rule(self, rule: Rule, when: datetime) -> List[Dict[str, Any]]:
        """Evaluate a rule at a given datetime and return resulting events."""
        raise NotImplementedError
