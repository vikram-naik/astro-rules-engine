# backend/app/core/interfaces/i_rules_engine.py
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any
from ..schemas import RuleCreate

class IRulesEngine(ABC):
    """Abstract interface for rules engine implementations."""

    @abstractmethod
    def evaluate_rule(self, rule: RuleCreate, when: datetime) -> List[Dict[str, Any]]:
        """Evaluate a rule at a given datetime and return a list of resulting events."""
        raise NotImplementedError
