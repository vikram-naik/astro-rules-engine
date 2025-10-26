from datetime import datetime
from typing import List, Dict, Any
from app.core.rules.interfaces.i_rules_engine import IRulesEngine
from app.core.astro.interfaces.i_astro_provider import IAstroProvider
from app.core.common.schemas import RuleCreate, ConditionRead
from app.core.db.enums import Relation
from app.core.common.config import settings
import logging

logger = logging.getLogger("astro.rulesengine")


def get_orb(planet_a: str, planet_b: str) -> float:
    """
    Determine orb based on planetary pair.
    Fallback order:
      1. Explicit entry in settings.orb_overrides
      2. Reversed key (planet_b-planet_a)
      3. settings.orb_default
    """
    if not planet_a or not planet_b:
        return settings.orb_default
    key1 = f"{planet_a.lower()}-{planet_b.lower()}"
    key2 = f"{planet_b.lower()}-{planet_a.lower()}"
    return settings.orb_overrides.get(key1) or settings.orb_overrides.get(key2) or settings.orb_default


class RulesEngineImpl(IRulesEngine):
    """Concrete rules engine depending on IAstroProvider abstraction."""

    def __init__(self, provider: IAstroProvider, orb_default: float = None):
        self.provider = provider
        self.orb_default = orb_default if orb_default is not None else settings.orb_default
        logger.debug(
            "RulesEngineImpl initialized with provider=%s orb_default=%s",
            getattr(self.provider, "__class__", type(self.provider)), self.orb_default
        )

    def evaluate_rule(self, rule: RuleCreate, when: datetime) -> List[Dict[str, Any]]:
        logger.debug(
            "evaluate_rule: rule_id=%s when=%s conditions=%d outcomes=%d",
            getattr(rule, "rule_id", None),
            when.isoformat(),
            len(rule.conditions or []),
            len(rule.outcomes or []),
        )

        for cond in rule.conditions:
            if not self._check_condition(cond, when):
                return []

        events = []
        for out in rule.outcomes:
            logger.debug("Outcome: %s", out)
            events.append({
                "rule_id": rule.rule_id,
                "date": (when.date() if hasattr(when, "date") else when).isoformat(),
                "effect": out.effect,
                "weight": out.weight,
                "confidence": rule.confidence,
            })

        logger.debug("evaluate_rule -> events_count=%d events=%s", len(events), events)
        return events

    def _check_condition(self, cond: ConditionRead, when: datetime) -> bool:
        from app.core.rules.relations.registry import get_relation_handler
        planet = (cond.planet or "").lower()
        relation = cond.relation
        if isinstance(relation, Relation):
            relation = relation.name

        target = (cond.target or "").lower()
        orb = cond.orb if cond.orb is not None else get_orb(planet, target)
        logger.debug("Checking condition: planet=%s relation=%s target=%s orb=%s", planet, relation, target, orb)

        try:
            lon = self.provider.longitude(planet, when)
            logger.debug("Provider longitude: planet=%s when=%s lon=%.6f", planet, when.isoformat(), lon)
        except Exception as exc:
            logger.exception("Provider.longitude failed for planet=%s when=%s: %s", planet, when, exc)
            return False

        handler = get_relation_handler(Relation[relation])
        if handler is None:
            logger.warning("No relation handler registered for relation=%s (condition=%s)", relation, cond)
            return False

        try:
            result = handler.check(self.provider, cond, when, orb)
            logger.debug("Relation handler result: relation=%s result=%s", relation, result)
            return result
        except Exception as exc:
            logger.exception("Relation handler raised exception for relation=%s cond=%s: %s", relation, cond, exc)
            return False
